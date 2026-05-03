from __future__ import annotations

import logging
import shutil
import socket
import tempfile
import time
import json
import threading
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from typing import Any

try:
    import requests
except ImportError:
    requests = None

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.features.selection import find_strategy
from app.zapret_manager.features.upstreams import sync_flowseal, sync_stressozz_strategies
from app.zapret_manager.features.zapret_runtime import start_zapret_interactive, stop_zapret
from app.zapret_manager.features.zapret_runtime import WinwsStartError
from app.zapret_manager.features.zapret_runtime import is_pid_alive
from app.zapret_manager.strategies.model import Strategy
from app.zapret_manager.strategies.store import list_strategies, save_strategy
from app.zapret_manager.utils.timex import now_utc_iso


log = logging.getLogger(__name__)


DEFAULT_SPEED_SETTINGS: dict[str, Any] = {
    "concurrency": 8,
    "connect_timeout_s": 2.0,
    "read_timeout_s": 3.0,
    "total_domain_timeout_s": 4.0,
    "max_strategy_time_s": 90.0,
    "detailed_console_output": False,
    "dns_cache": True,
    "deduplicate_equivalent_strategies": True,
}


def get_speed_settings(ctx: AppContext) -> dict[str, Any]:
    """Return sweep speed settings (stored in state.json).

    We intentionally keep this in state (not config.yaml) so users can tweak it
    interactively without editing files.
    """
    raw = {}
    try:
        raw = dict(getattr(ctx.state, "test", {}) or {})
    except Exception:
        raw = {}
    cur = dict(DEFAULT_SPEED_SETTINGS)
    for k, v in raw.items():
        if k in cur:
            cur[k] = v
    # sanitize
    try:
        cur["concurrency"] = int(cur["concurrency"])
    except Exception:
        cur["concurrency"] = int(DEFAULT_SPEED_SETTINGS["concurrency"])
    cur["concurrency"] = max(1, min(16, int(cur["concurrency"])))

    for k in ["connect_timeout_s", "read_timeout_s", "total_domain_timeout_s", "max_strategy_time_s"]:
        try:
            cur[k] = float(cur[k])
        except Exception:
            cur[k] = float(DEFAULT_SPEED_SETTINGS[k])
        cur[k] = max(0.1, cur[k])
    cur["detailed_console_output"] = bool(cur.get("detailed_console_output", False))
    cur["dns_cache"] = bool(cur.get("dns_cache", True))
    cur["deduplicate_equivalent_strategies"] = bool(cur.get("deduplicate_equivalent_strategies", True))
    return cur


def set_speed_settings(ctx: AppContext, patch: dict[str, Any]) -> dict[str, Any]:
    """Update speed settings in state.json (merge patch), return normalized."""
    cur = dict(getattr(ctx.state, "test", {}) or {})
    cur.update(patch or {})
    ctx.state.test = cur
    from app.zapret_manager.core.state import save_state

    save_state(ctx.paths.state_file, ctx.state)
    return get_speed_settings(ctx)


class _CancelFlag:
    def __init__(self) -> None:
        self._ev = threading.Event()

    def cancel(self) -> None:
        self._ev.set()

    def is_cancelled(self) -> bool:
        return self._ev.is_set()


DEFAULT_TEST_DOMAINS = [
    # Best-effort "youtube/googlevideo" probes (из Zapret-Manager.sh).
    "rr1---sn-gvnuxaxjvh-jx3z.googlevideo.com",
    "rr1---sn-gvnuxaxjvh-jx3l.googlevideo.com",
    "rr1---sn-gvnuxaxjvh-jx3s.googlevideo.com",
]


@dataclass(frozen=True)
class DomainCheck:
    """One user-facing domain probe result.

    This is intentionally small and readable: UI should show these rows, while
    raw subprocess/winws commands stay in logs.
    """

    domain: str
    url: str
    ok: bool
    elapsed_ms: int
    error: str = ""
    status_code: int | None = None

    # Extended probes (best-effort). All of these can be None if probe was not
    # executed or is not applicable.
    resolved_ip: str = ""
    dns_ok: bool | None = None
    dns_ms: int | None = None
    tcp_ok: bool | None = None
    tcp_ms: int | None = None
    ping_ok: bool | None = None
    ping_ms: int | None = None
    udp443: str = ""  # ok/fail/unknown/skip

    @property
    def status_text(self) -> str:
        if self.ok:
            return "OK"
        return "FAIL"


@dataclass(frozen=True)
class TestResult:
    strategy: str
    ok: int
    total: int
    checks: list[DomainCheck] = field(default_factory=list)

    # When winws could not be started/verified, do not pretend it's a domain fail.
    status: str = "ok"  # ok|invalid
    error: str = ""

    # Extended summary fields (best-effort).
    dns_ok: int = 0
    tcp_ok: int = 0
    ping_ok: int = 0
    udp_ok: int = 0

    # Flags to indicate which metrics were actually measured.
    # When False, UI should show N/A instead of 0/N.
    measured_dns: bool = False
    measured_tcp: bool = False
    measured_ping: bool = False
    measured_udp: bool = False

    def summary_text(self) -> str:
        # ok/total is HTTP result to preserve backward compatible display.
        parts = [f"HTTP: {self.ok}/{self.total}"]
        if self.total:
            def _metric(label: str, ok: int, measured: bool) -> str:
                return f"{label}: {ok}/{self.total}" if measured else f"{label}: N/A"

            parts.append(_metric("TCP", self.tcp_ok, self.measured_tcp))
            parts.append(_metric("DNS", self.dns_ok, self.measured_dns))
            parts.append(_metric("PING", self.ping_ok, self.measured_ping))
            parts.append(_metric("UDP443", self.udp_ok, self.measured_udp))
        return " | ".join(parts)


@dataclass(frozen=True)
class ProofRow:
    """One domain probe result for proof-of-effect test."""

    domain: str
    baseline_ok: bool
    strategy_ok: bool
    effect: str
    baseline_error: str | None
    strategy_error: str | None
    baseline_ms: int | None
    strategy_ms: int | None


@dataclass(frozen=True)
class ProofResult:
    """Proof-of-effect test result with winws evidence."""

    strategy_name: str
    rows: list[ProofRow]
    total: int
    improved: int
    already_ok: int
    no_effect: int
    worsened: int
    invalid: int
    strategy_effect_proven: bool
    winws_pid: int | None
    winws_alive_at_start: bool
    winws_alive_at_end: bool
    invalid_reason: str | None
    restore_warning: str | None


@dataclass(frozen=True)
class TestSessionSummary:
    results: list[TestResult]
    pinned: list[Path]
    results_file: Path


def _normalize_url(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    return raw if raw.startswith("http://") or raw.startswith("https://") else f"https://{raw}"


def _display_domain(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc:
        return parsed.netloc
    return url.replace("https://", "").replace("http://", "").strip("/")


def _host_for_probes(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc:
        return parsed.netloc
    # handle raw host without scheme
    return url.replace("https://", "").replace("http://", "").strip("/")


def _dns_resolve(host: str) -> tuple[bool, str, int, str]:
    start = time.perf_counter()
    try:
        infos = socket.getaddrinfo(host, None)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        ip = ""
        for fam, _socktype, _proto, _canon, sockaddr in infos:
            if fam in (socket.AF_INET, socket.AF_INET6):
                ip = sockaddr[0]
                break
        return (bool(ip), ip, elapsed_ms, "" if ip else "no ip")
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return (False, "", elapsed_ms, type(e).__name__)


def _tcp_connect(host: str, port: int, *, timeout_s: float) -> tuple[bool, int, str]:
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            pass
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return True, elapsed_ms, ""
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return False, elapsed_ms, type(e).__name__


def _ping_host(host: str, *, timeout_ms: int = 1200) -> tuple[bool, int, str]:
    # Best-effort and cross-platform.
    from app.zapret_manager.utils.platform import is_windows
    from app.zapret_manager.utils.subprocessx import run

    start = time.perf_counter()
    try:
        if is_windows():
            # -n 1 : single echo
            # -w timeout in ms
            r = run(["ping", "-n", "1", "-w", str(timeout_ms), host], check=False, capture=True)
        else:
            # macOS: -W is timeout in ms
            r = run(["ping", "-c", "1", "-W", str(max(1, int(timeout_ms / 1000))), host], check=False, capture=True)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        ok = r.code == 0
        return ok, elapsed_ms, "" if ok else (r.err.strip() or "ping failed")
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return False, elapsed_ms, type(e).__name__


def _udp443_probe(ip: str, *, timeout_s: float = 1.0) -> tuple[str, str]:
    """Best-effort QUIC/UDP indicator.

    UDP reachability can't be reliably tested without protocol/response.
    We return:
      - ok: send did not error (still not a guarantee)
      - fail: immediate socket error
      - skip: no ip
    """
    if not ip:
        return "skip", ""
    try:
        s = socket.socket(socket.AF_INET6 if ":" in ip else socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout_s)
        try:
            s.connect((ip, 443))
            s.send(b"\x00")
        finally:
            s.close()
        return "ok", ""
    except Exception as e:
        return "fail", type(e).__name__


def _fetch_one_quick(url: str, *, timeout_s: float) -> DomainCheck:
    """Quick probe: HTTP(S) GET with Range, no DNS/TCP/PING/UDP helpers.

    Requirements (per UX spec):
    - GET (not HEAD)
    - Range bytes=0-65535
    - short timeout
    - 2xx-4xx = OK
    - 5xx/timeout/exception = FAIL
    """
    display = _display_domain(url)
    start = time.perf_counter()

    if requests is None:
        return DomainCheck(
            domain=display,
            url=url,
            ok=False,
            elapsed_ms=int((time.perf_counter() - start) * 1000),
            error="requests module not available",
        )

    try:
        r = requests.get(
            url,
            timeout=timeout_s,
            allow_redirects=True,
            headers={"Range": "bytes=0-65535"},
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        ok = 200 <= r.status_code < 500
        return DomainCheck(
            domain=display,
            url=url,
            ok=ok,
            elapsed_ms=elapsed_ms,
            status_code=r.status_code,
            error="" if ok else f"http {r.status_code}",
        )
    except requests.exceptions.Timeout:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return DomainCheck(display, url, False, elapsed_ms, error="timeout")
    except requests.exceptions.SSLError:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return DomainCheck(display, url, False, elapsed_ms, error="tls error")
    except requests.exceptions.ConnectionError:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return DomainCheck(display, url, False, elapsed_ms, error="connection error")
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return DomainCheck(display, url, False, elapsed_ms, error=type(e).__name__)


def _fetch_one_detail(
    url: str,
    *,
    timeout_s: float,
    connect_timeout_s: float | None = None,
    read_timeout_s: float | None = None,
    dns_cache: "DNSCache | None" = None,
) -> DomainCheck:
    display = _display_domain(url)
    host = _host_for_probes(url)

    if dns_cache is not None:
        dns_ok, ip, dns_ms, dns_err = dns_cache.resolve(host)
    else:
        dns_ok, ip, dns_ms, dns_err = _dns_resolve(host)

    tcp_timeout = float(connect_timeout_s if connect_timeout_s is not None else timeout_s)
    tcp_ok, tcp_ms, tcp_err = _tcp_connect(host, 443, timeout_s=tcp_timeout)
    ping_ok, ping_ms, ping_err = _ping_host(host)
    udp_status, udp_err = _udp443_probe(ip)

    start = time.perf_counter()
    
    if requests is None:
        return DomainCheck(
            domain=display,
            url=url,
            ok=False,
            elapsed_ms=int((time.perf_counter() - start) * 1000),
            error="requests module not available",
            resolved_ip=ip,
            dns_ok=dns_ok,
            dns_ms=dns_ms,
            tcp_ok=tcp_ok,
            tcp_ms=tcp_ms,
            ping_ok=ping_ok,
            ping_ms=ping_ms,
            udp443=udp_status,
        )

    try:
        # A normal GET is closer to real browser behavior than just opening TCP.
        # We intentionally treat HTTP 4xx as network OK: domain is reachable, even
        # if the server rejects the exact path.
        ct = float(connect_timeout_s if connect_timeout_s is not None else timeout_s)
        rt = float(read_timeout_s if read_timeout_s is not None else timeout_s)
        r = requests.get(url, timeout=(ct, rt), allow_redirects=True, stream=True)
        # Don't download full page.
        try:
            _ = r.raw.read(256)  # type: ignore[attr-defined]
        except Exception:
            pass
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        ok = 200 <= r.status_code < 500
        return DomainCheck(
            domain=display,
            url=url,
            ok=ok,
            elapsed_ms=elapsed_ms,
            status_code=r.status_code,
            error="" if ok else f"http {r.status_code}",
            resolved_ip=ip,
            dns_ok=dns_ok,
            dns_ms=dns_ms,
            tcp_ok=tcp_ok,
            tcp_ms=tcp_ms,
            ping_ok=ping_ok,
            ping_ms=ping_ms,
            udp443=udp_status,
        )
    except requests.exceptions.Timeout:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return DomainCheck(
            display,
            url,
            False,
            elapsed_ms,
            error="timeout",
            resolved_ip=ip,
            dns_ok=dns_ok,
            dns_ms=dns_ms,
            tcp_ok=tcp_ok,
            tcp_ms=tcp_ms,
            ping_ok=ping_ok,
            ping_ms=ping_ms,
            udp443=udp_status,
        )
    except requests.exceptions.SSLError:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return DomainCheck(
            display,
            url,
            False,
            elapsed_ms,
            error="tls error",
            resolved_ip=ip,
            dns_ok=dns_ok,
            dns_ms=dns_ms,
            tcp_ok=tcp_ok,
            tcp_ms=tcp_ms,
            ping_ok=ping_ok,
            ping_ms=ping_ms,
            udp443=udp_status,
        )
    except requests.exceptions.ConnectionError:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return DomainCheck(
            display,
            url,
            False,
            elapsed_ms,
            error="connection error",
            resolved_ip=ip,
            dns_ok=dns_ok,
            dns_ms=dns_ms,
            tcp_ok=tcp_ok,
            tcp_ms=tcp_ms,
            ping_ok=ping_ok,
            ping_ms=ping_ms,
            udp443=udp_status,
        )
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return DomainCheck(
            display,
            url,
            False,
            elapsed_ms,
            error=type(e).__name__,
            resolved_ip=ip,
            dns_ok=dns_ok,
            dns_ms=dns_ms,
            tcp_ok=tcp_ok,
            tcp_ms=tcp_ms,
            ping_ok=ping_ok,
            ping_ms=ping_ms,
            udp443=udp_status,
        )


def _format_domain_row(index: int, total: int, check: DomainCheck) -> str:
    status = "OK" if check.ok else "FAIL"
    extra = f"{check.elapsed_ms} ms"
    if check.status_code is not None:
        extra += f", HTTP {check.status_code}"
    if check.error:
        extra += f", {check.error}"
    # Extended probes
    if check.dns_ok is not None:
        extra += f", DNS {'OK' if check.dns_ok else 'FAIL'}"
    if check.tcp_ok is not None:
        extra += f", TCP443 {'OK' if check.tcp_ok else 'FAIL'}"
    if check.ping_ok is not None:
        extra += f", PING {'OK' if check.ping_ok else 'FAIL'}"
    if check.udp443:
        extra += f", UDP443 {check.udp443}"
    return f"[{index:02d}/{total:02d}] {check.domain:<42} {status:<5} {extra}"


def check_domains_detailed(
    domains: list[str],
    *,
    timeout_s: float = 3.0,
    parallel: int | None = None,
    progress: bool = False,
    mode: str = "full",  # full|quick
    connect_timeout_s: float | None = None,
    read_timeout_s: float | None = None,
    total_domain_timeout_s: float | None = None,
    dns_cache: "DNSCache | None" = None,
    cancel: "_CancelFlag | None" = None,
) -> list[DomainCheck]:
    cleaned = [_normalize_url(d) for d in domains if d.strip()]
    cleaned = [u for u in cleaned if u]
    if not cleaned:
        return []

    def _fetch(url: str, *, timeout_s: float) -> DomainCheck:
        if cancel is not None and cancel.is_cancelled():
            return DomainCheck(domain=_display_domain(url), url=url, ok=False, elapsed_ms=0, error="cancelled")
        if mode == "quick":
            # quick path keeps backward compatible single timeout
            return _fetch_one_quick(url, timeout_s=timeout_s)
        return _fetch_one_detail(
            url,
            timeout_s=timeout_s,
            connect_timeout_s=connect_timeout_s,
            read_timeout_s=read_timeout_s,
            dns_cache=dns_cache,
        )

    # If progress is requested, keep sequential order so the user sees exactly
    # which domain is being tested now. This is slower but much more readable.
    if progress or not parallel or parallel <= 1:
        checks: list[DomainCheck] = []
        total = len(cleaned)
        for i, url in enumerate(cleaned, start=1):
            domain = _display_domain(url)
            if progress:
                try:
                    from app.zapret_manager.ui.colors import C
                except Exception:  # pragma: no cover
                    class _C:
                        GREEN = RED = YELLOW = DIM = RESET = ""

                    C = _C()  # type: ignore
                # UX: keep format stable for parsing and readability.
                # Caller is responsible for higher-level progress (strategy index/name).
                print(f"  [Domain {i:02d}/{total:02d}] {domain:<42} ... ", end="", flush=True)
            if cancel is not None and cancel.is_cancelled():
                break
            check = _fetch(url, timeout_s=timeout_s)
            checks.append(check)
            if progress:
                suffix = f"{check.elapsed_ms} ms"
                if check.error:
                    suffix += f", {check.error}"
                color = C.GREEN if check.ok else C.RED
                print(f"{color}{check.status_text:<5}{C.RESET} {suffix}")
        return checks

    # Parallel mode (no per-domain prints). Keep results order stable.
    from concurrent.futures import ThreadPoolExecutor, as_completed

    import concurrent.futures

    checks: list[DomainCheck] = [DomainCheck("", "", False, 0, error="internal") for _ in cleaned]
    with ThreadPoolExecutor(max_workers=int(parallel)) as ex:
        futs: dict[concurrent.futures.Future[DomainCheck], int] = {}
        for idx, u in enumerate(cleaned):
            if cancel is not None and cancel.is_cancelled():
                break
            futs[ex.submit(_fetch, u, timeout_s=timeout_s)] = idx
        for f in as_completed(futs):
            idx = futs[f]
            try:
                if total_domain_timeout_s is not None:
                    checks[idx] = f.result(timeout=float(total_domain_timeout_s))
                else:
                    checks[idx] = f.result()
            except Exception as e:
                url = cleaned[idx]
                checks[idx] = DomainCheck(
                    domain=_display_domain(url),
                    url=url,
                    ok=False,
                    elapsed_ms=0,
                    error=type(e).__name__,
                )
    return checks


class DNSCache:
    """In-memory DNS cache for one sweep (best-effort)."""

    def __init__(self, *, ttl_s: float = 600.0) -> None:
        self.ttl_s = float(ttl_s)
        self._items: dict[str, tuple[float, tuple[bool, str, int, str]]] = {}

    def resolve(self, host: str) -> tuple[bool, str, int, str]:
        now = time.time()
        item = self._items.get(host)
        if item:
            ts, val = item
            if now - ts <= self.ttl_s:
                return val
        val = _dns_resolve(host)
        self._items[host] = (now, val)
        return val


def _compact_progress_line(
    *,
    strategy_name: str,
    strategy_idx: int,
    strategies_total: int,
    done: int,
    total: int,
    ok: int,
    fail: int,
    elapsed_s: float,
) -> str:
    return (
        f"[Strategy {strategy_idx:02d}/{strategies_total:02d}] {strategy_name}"
        f" | domains {done}/{total} | OK {ok} | FAIL {fail} | elapsed {int(elapsed_s)}s"
    )


def check_domains_compact(
    domains: list[str],
    *,
    timeout_s: float,
    parallel: int,
    mode: str,
    connect_timeout_s: float,
    read_timeout_s: float,
    total_domain_timeout_s: float,
    dns_cache: "DNSCache | None",
    cancel: "_CancelFlag",
    max_strategy_time_s: float,
    progress_cb: callable,
) -> tuple[list[DomainCheck], bool]:
    """Parallel checks with compact progress callback.

    Returns (checks, partial_timeout).
    """
    cleaned = [_normalize_url(d) for d in domains if d.strip()]
    cleaned = [u for u in cleaned if u]
    if not cleaned:
        return ([], False)

    start = time.perf_counter()
    partial_timeout = False

    from concurrent.futures import ThreadPoolExecutor, as_completed

    checks: list[DomainCheck] = [DomainCheck("", "", False, 0, error="internal") for _ in cleaned]
    ok = 0
    fail = 0
    done = 0

    def _fetch_one(url: str) -> DomainCheck:
        if cancel.is_cancelled():
            return DomainCheck(domain=_display_domain(url), url=url, ok=False, elapsed_ms=0, error="cancelled")
        # Reuse rich fetch path.
        return check_domains_detailed(
            [url],
            timeout_s=timeout_s,
            parallel=None,
            progress=False,
            mode=mode,
            connect_timeout_s=connect_timeout_s,
            read_timeout_s=read_timeout_s,
            total_domain_timeout_s=total_domain_timeout_s,
            dns_cache=dns_cache,
            cancel=cancel,
        )[0]

    with ThreadPoolExecutor(max_workers=int(parallel)) as ex:
        futs = {ex.submit(_fetch_one, u): idx for idx, u in enumerate(cleaned)}
        for f in as_completed(futs):
            idx = futs[f]
            # strategy hard deadline
            if max_strategy_time_s is not None and (time.perf_counter() - start) > float(max_strategy_time_s):
                partial_timeout = True
                cancel.cancel()
            try:
                checks[idx] = f.result(timeout=float(total_domain_timeout_s))
            except Exception as e:
                url = cleaned[idx]
                checks[idx] = DomainCheck(domain=_display_domain(url), url=url, ok=False, elapsed_ms=0, error=type(e).__name__)
            done += 1
            if checks[idx].ok:
                ok += 1
            else:
                fail += 1
            progress_cb(done=done, total=len(cleaned), ok=ok, fail=fail, elapsed_s=time.perf_counter() - start)
            if cancel.is_cancelled():
                break

    # Only keep checks for completed futures if cancelled.
    if cancel.is_cancelled():
        checks = [c for c in checks if c.domain]
    return (checks, partial_timeout)


def check_domains(domains: list[str], *, timeout_s: float = 3.0, parallel: int | None = None) -> tuple[int, int]:
    checks = check_domains_detailed(domains, timeout_s=timeout_s, parallel=parallel, progress=False, mode="full")
    return sum(1 for c in checks if c.ok), len(checks)


def control_test(ctx: "AppContext", domains: list[str], *, parallel: int | None = None) -> TestResult:
    """Legacy helper used by UI: baseline check without any strategy running."""
    checks = check_domains_detailed(domains, parallel=parallel, progress=False, mode="full")
    ok = sum(1 for c in checks if c.ok)
    dns_ok = sum(1 for c in checks if c.dns_ok)
    tcp_ok = sum(1 for c in checks if c.tcp_ok)
    ping_ok = sum(1 for c in checks if c.ping_ok)
    udp_ok = sum(1 for c in checks if c.udp443 == "ok")
    measured_dns = any(c.dns_ok is not None for c in checks)
    measured_tcp = any(c.tcp_ok is not None for c in checks)
    measured_ping = any(c.ping_ok is not None for c in checks)
    measured_udp = any(bool(c.udp443) for c in checks)

    result = TestResult(
        strategy="control",
        ok=ok,
        total=len(checks),
        checks=checks,
        dns_ok=dns_ok,
        tcp_ok=tcp_ok,
        ping_ok=ping_ok,
        udp_ok=udp_ok,
        measured_dns=measured_dns,
        measured_tcp=measured_tcp,
        measured_ping=measured_ping,
        measured_udp=measured_udp,
    )
    # Record failed domains as problem domains
    try:
        from app.zapret_manager.features.problem_domains import add_from_domain_checks
        add_from_domain_checks(ctx, checks, source="control")
    except Exception as e:
        log.warning("Failed to record problem domains from control test: %s", e)
    return result


def control_test_mode(
    ctx: "AppContext",
    domains: list[str],
    *,
    mode: str = "full",
    parallel: int | None = None,
    progress: bool = True,
    timeout_s: float | None = None,
) -> TestResult:
    """Baseline test without zapret in either quick or full mode.

    - quick: GET+Range only, short timeout
    - full: existing detailed probes
    """
    t = timeout_s
    if t is None:
        t = 2.5 if mode == "quick" else 3.0
    checks = check_domains_detailed(domains, parallel=parallel, progress=progress, mode=mode, timeout_s=t)
    ok = sum(1 for c in checks if c.ok)
    dns_ok = sum(1 for c in checks if c.dns_ok)
    tcp_ok = sum(1 for c in checks if c.tcp_ok)
    ping_ok = sum(1 for c in checks if c.ping_ok)
    udp_ok = sum(1 for c in checks if c.udp443 == "ok")
    measured_dns = any(c.dns_ok is not None for c in checks)
    measured_tcp = any(c.tcp_ok is not None for c in checks)
    measured_ping = any(c.ping_ok is not None for c in checks)
    measured_udp = any(bool(c.udp443) for c in checks)

    result = TestResult(
        strategy="control",
        ok=ok,
        total=len(checks),
        checks=checks,
        dns_ok=dns_ok,
        tcp_ok=tcp_ok,
        ping_ok=ping_ok,
        udp_ok=udp_ok,
        measured_dns=measured_dns,
        measured_tcp=measured_tcp,
        measured_ping=measured_ping,
        measured_udp=measured_udp,
    )
    try:
        from app.zapret_manager.features.problem_domains import add_from_domain_checks

        add_from_domain_checks(ctx, checks, source="control")
    except Exception as e:
        log.warning("Failed to record problem domains from control test: %s", e)
    return result


def _runtime_ready(ctx: AppContext) -> bool:
    """Best-effort check that runtime is installed and winws.exe is discoverable."""
    try:
        from app.zapret_manager.features.zapret_runtime import detect_runtime_files

        detect_runtime_files(ctx)
        return bool(ctx.state.runtime.installed and ctx.state.runtime.winws_path)
    except Exception:
        return False


def _ensure_runtime(ctx: AppContext) -> None:
    # v0.3: runtime is bundled. We do not download it for the user.
    if _runtime_ready(ctx):
        return
    raise RuntimeError(
        "Bundled runtime not found. Re-download/re-extract the release (expected runtime/zapret/*)."
    )


def _ensure_pack_strategies(ctx: AppContext, *, need_flowseal: bool, need_stressozz: bool) -> None:
    """Sync optional packs if strategies are missing."""
    if need_flowseal:
        log.info("flowseal strategies missing -> syncing Flowseal")
        sync_flowseal(ctx, generated_dir=_tmp_pack_dir(ctx, "flowseal"))
    if need_stressozz:
        log.info("stressozz strategies missing -> syncing StressOzz")
        sync_stressozz_strategies(ctx, generated_dir=_tmp_pack_dir(ctx, "stressozz"))


def _tmp_pack_dir(ctx: AppContext, pack: str) -> Path:
    d = ctx.paths.strategies_generated_dir / "_tmp" / "packs" / pack
    d.mkdir(parents=True, exist_ok=True)
    return d


def _tmp_dir(ctx: AppContext, name: str) -> Path:
    d = ctx.paths.strategies_generated_dir / "_tmp" / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def _list_tmp_strategies(ctx: AppContext, tmp_dir: Path, *, kind: str | None = None) -> list[Strategy]:
    return list_strategies(tmp_dir, kind=kind)


def _pin_top_results(ctx: AppContext, results: list[TestResult], tmp_dir: Path, *, top_n: int = 5) -> list[Path]:
    """Pin top strategies into custom dir (user won't lose them on updates)."""
    if top_n == 5:
        best = _select_top5_wide(results)
    else:
        ranked = sorted(results, key=lambda r: (r.ok, r.total, r.strategy), reverse=True)
        best = [r for r in ranked if r.total > 0][:top_n]

    pinned: list[Path] = []
    for r in best:
        st = find_strategy(ctx, r.strategy) or next(
            (s for s in _list_tmp_strategies(ctx, tmp_dir) if s.name == r.strategy), None
        )
        if not st:
            continue
        p = save_strategy(ctx.paths.strategies_custom_dir, st)
        pinned.append(p)
    return pinned


def _cleanup_tmp(tmp_dir: Path) -> None:
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _print_strategy_header(strategy: Strategy, domains: list[str]) -> None:
    print()
    print(f"Тест стратегии: {strategy.name}")
    print(f"Проверок: {len([d for d in domains if d.strip()])}")
    print("Формат: HTTP(S) GET; HTTP 2xx-4xx = доступен, timeout/connection/tls = FAIL")
    print("-" * 78)


def _print_strategy_footer(result: TestResult) -> None:
    print("-" * 78)
    if result.status != "ok":
        print(f"Итог {result.strategy}: INVALID ({result.error})")
        print()
        return
    print(f"Итог {result.strategy}: {result.summary_text()}")
    failed = [c for c in result.checks if not c.ok]
    if failed:
        print("Провалились:")
        for c in failed:
            print(f"- {c.domain}: {c.error or 'unknown'}")
    print()


def test_strategy(
    ctx: AppContext,
    strategy: Strategy,
    domains: list[str],
    *,
    youtube: Strategy | None = None,
    discord: Strategy | None = None,
    settle_s: float = 1.5,
    parallel: int | None = None,
    show_progress: bool = True,
    mode: str = "full",
) -> TestResult:
    was_running = ctx.state.zapret.running
    prev_base = ctx.state.zapret.base_strategy
    prev_selected = ctx.state.zapret.selected_strategy
    prev_youtube = ctx.state.zapret.youtube_layer
    prev_discord = ctx.state.zapret.discord_layer
    try:
        stop_zapret(ctx)
        if show_progress:
            _print_strategy_header(strategy, domains)
        try:
            start_zapret_interactive(ctx, strategy, youtube=youtube, discord=discord)
        except WinwsStartError as e:
            # Strategy is not active. Do not run domain checks.
            return TestResult(strategy=strategy.name, ok=0, total=0, checks=[], status="invalid", error=str(e))
        time.sleep(settle_s)
        checks = check_domains_detailed(domains, parallel=parallel, progress=show_progress, mode=mode)
        ok = sum(1 for c in checks if c.ok)
        dns_ok = sum(1 for c in checks if c.dns_ok)
        tcp_ok = sum(1 for c in checks if c.tcp_ok)
        ping_ok = sum(1 for c in checks if c.ping_ok)
        udp_ok = sum(1 for c in checks if c.udp443 == "ok")
        measured_dns = any(c.dns_ok is not None for c in checks)
        measured_tcp = any(c.tcp_ok is not None for c in checks)
        measured_ping = any(c.ping_ok is not None for c in checks)
        measured_udp = any(bool(c.udp443) for c in checks)

        result = TestResult(
            strategy=strategy.name,
            ok=ok,
            total=len(checks),
            checks=checks,
            dns_ok=dns_ok,
            tcp_ok=tcp_ok,
            ping_ok=ping_ok,
            udp_ok=udp_ok,
            measured_dns=measured_dns,
            measured_tcp=measured_tcp,
            measured_ping=measured_ping,
            measured_udp=measured_udp,
        )
        if show_progress:
            _print_strategy_footer(result)
        return result
    finally:
        stop_zapret(ctx)
        ctx.state.zapret.base_strategy = prev_base
        ctx.state.zapret.selected_strategy = prev_selected
        ctx.state.zapret.youtube_layer = prev_youtube
        ctx.state.zapret.discord_layer = prev_discord
        if was_running and prev_selected:
            prev_strategy = find_strategy(ctx, prev_selected, kind="base") or find_strategy(ctx, prev_selected)
            if prev_strategy:
                youtube = find_strategy(ctx, prev_youtube, kind="youtube") if prev_youtube else None
                discord = find_strategy(ctx, prev_discord, kind="discord") if prev_discord else None
                try:
                    start_zapret_interactive(ctx, prev_strategy, youtube=youtube, discord=discord)
                except Exception:
                    log.exception("failed to restore previous zapret state after strategy test")


def _telemetry_jsonl_path(ctx: AppContext) -> Path:
    p = (ctx.paths.data_dir / "telemetry" / "strategy_runs.jsonl").resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _safe_domain_set_key(key: str) -> str:
    return (key or "unknown").strip().lower().replace(" ", "_")


@dataclass(frozen=True)
class StrategyRunRecord:
    ts: str
    mode: str
    domain_set: str
    strategy_id: str
    ok: int
    fail: int
    avg_ms: int
    score: int
    missing_assets: list[str]
    error: str

    def to_json(self) -> dict[str, Any]:
        return {
            "ts": self.ts,
            "mode": self.mode,
            "domain_set": self.domain_set,
            "strategy_id": self.strategy_id,
            "ok": self.ok,
            "fail": self.fail,
            "avg_ms": self.avg_ms,
            "score": self.score,
            "missing_assets": self.missing_assets,
            "error": self.error,
        }


@dataclass(frozen=True)
class StrategyRankingRow:
    rank: int
    strategy: str
    ok: int
    fail: int
    avg_ms: int
    missing_assets: list[str]
    score: int
    status: str
    error: str


def _avg_ms_from_checks(checks: list[DomainCheck]) -> int:
    if not checks:
        return 0
    return int(sum(c.elapsed_ms for c in checks) / max(1, len(checks)))


def _score_run(
    *,
    ok: int,
    total: int,
    missing_assets: int,
    crashed: bool,
    avg_ms: int,
) -> int:
    """Simple, explainable scoring.

    score = success_rate*100 - penalties
    - missing_assets penalty: 3 pts each
    - crash/start error penalty: 30 pts
    - latency penalty: 0..10 pts (avg_ms / 200)
    """

    if total <= 0:
        base = 0
    else:
        base = int((ok / total) * 100)
    penalty = 0
    penalty += int(missing_assets) * 3
    if crashed:
        penalty += 30
    penalty += min(10, int(max(0, avg_ms) / 200))
    return max(0, min(100, base - penalty))


def _detect_missing_assets_from_error(err: str) -> list[str]:
    # Best-effort heuristic; keep stable and simple.
    e = (err or "")
    out: list[str] = []
    for key in ["hostlist", "ipset", "bin", "quic", "stun", "fake", "exclude", "rkn"]:
        if key in e.lower():
            out.append(key)
    # de-dup
    seen: set[str] = set()
    uniq: list[str] = []
    for x in out:
        if x in seen:
            continue
        seen.add(x)
        uniq.append(x)
    return uniq


def _append_strategy_run_jsonl(ctx: AppContext, rec: StrategyRunRecord) -> None:
    p = _telemetry_jsonl_path(ctx)
    p.write_text("", encoding="utf-8") if not p.exists() else None
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec.to_json(), ensure_ascii=False) + "\n")


def _save_latest_ranking_json(ctx: AppContext, rows: list[StrategyRankingRow], *, domain_set: str, mode: str) -> Path:
    out_dir = (ctx.paths.data_dir / "telemetry").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    p = (out_dir / "latest_strategy_ranking.json").resolve()
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "domain_set": domain_set,
        "rows": [
            {
                "rank": r.rank,
                "strategy": r.strategy,
                "ok": r.ok,
                "fail": r.fail,
                "avg_ms": r.avg_ms,
                "missing_assets": r.missing_assets,
                "score": r.score,
                "status": r.status,
                "error": r.error,
            }
            for r in rows
        ],
    }
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def _print_ranking_table(rows: list[StrategyRankingRow]) -> None:
    print()
    print("Rank | Strategy | OK | FAIL | Avg ms | Missing assets | Score")
    print("-" * 78)
    for r in rows:
        miss = ",".join(r.missing_assets) if r.missing_assets else "-"
        print(f"{r.rank:>4} | {r.strategy:<16} | {r.ok:>3} | {r.fail:>4} | {r.avg_ms:>6} | {miss:<14} | {r.score:>3}")
    print("-" * 78)


def _strategies_for_mode(ctx: AppContext, *, mode: str) -> tuple[list[Strategy], bool, bool]:
    """Return (candidates, ensure_flowseal, ensure_stressozz)."""
    m = (mode or "").strip().lower()
    if m == "quick":
        # builtin/base only
        return (list_strategies(ctx.paths.strategies_builtin_dir, kind="base"), False, False)
    if m == "full":
        # builtin + generated + packs (if available / can be synced)
        return (
            list_strategies(ctx.paths.strategies_builtin_dir, kind="base")
            + list_strategies(ctx.paths.strategies_generated_dir, kind="base")
            + list_strategies(ctx.paths.strategies_custom_dir, kind="base"),
            True,
            True,
        )
    if m == "exhaustive":
        # same as full, but we also force include tmp pack candidates group(all)
        # NOTE: this may be slow.
        return (_select_candidates(ctx, "all"), True, True)
    raise ValueError(f"Unknown test mode: {mode}")


def _strategy_equivalence_key(st: Strategy) -> str:
    """Key for deduplicating equivalent strategies.

    We cannot use just name, because upstream packs may provide same params under
    different names. We normalize by engine and args.
    """
    try:
        args = st.get_full_args()
    except Exception:
        args = list(st.args)
    return "|".join([str(st.engine).lower()] + [str(a) for a in args])


def test_all_strategies_with_progress(
    ctx: AppContext,
    *,
    domains: list[str],
    domain_set: str,
    mode: str,
    parallel: int | None = None,
    settle_s: float = 1.5,
    top_n_pin: int = 5,
) -> tuple[TestSessionSummary, list[StrategyRankingRow], Path]:
    """Run strategies sweep with progress, scoring, ranking, and JSONL telemetry.

    Reuses:
      - test_session(...) to execute strategies sequentially
      - check_domains_detailed(..., progress=True) inside test_strategy()
    """

    settings = get_speed_settings(ctx)
    # Backward compatible override: old menu passes parallel. New default is from settings.
    concurrency = int(parallel if parallel is not None else settings["concurrency"])
    concurrency = max(1, min(16, concurrency))
    detailed_console_output = bool(settings["detailed_console_output"])

    candidates, ensure_flowseal, ensure_stressozz = _strategies_for_mode(ctx, mode=mode)
    # Best-effort pack sync if requested.
    if ensure_flowseal or ensure_stressozz:
        _ensure_pack_strategies(ctx, need_flowseal=ensure_flowseal, need_stressozz=ensure_stressozz)

    # De-dup candidates by name, preserve order.
    seen_names: set[str] = set()
    uniq: list[Strategy] = []
    for st in candidates:
        if st.name in seen_names:
            continue
        seen_names.add(st.name)
        uniq.append(st)
    candidates = uniq

    # Optionally de-dup by equivalent args (same engine+args): this can reduce
    # sweep time significantly when upstream packs contain aliases.
    if bool(settings.get("deduplicate_equivalent_strategies", True)):
        seen_keys: set[str] = set()
        uniq2: list[Strategy] = []
        for st in candidates:
            k = _strategy_equivalence_key(st)
            if k in seen_keys:
                continue
            seen_keys.add(k)
            uniq2.append(st)
        candidates = uniq2

    if not candidates:
        raise RuntimeError("No strategies for this mode.")

    cancel = _CancelFlag()
    dns_cache = DNSCache(ttl_s=900.0) if bool(settings.get("dns_cache", True)) else None

    # Patch in strategy-level progress header by wrapping test_strategy.
    results: list[TestResult] = []

    total_strategies = len(candidates)
    try:
        for idx, st in enumerate(candidates, start=1):
            # NOTE: must not run multiple strategies simultaneously.
            # Strategy starts once here, domain checks happen inside.
            if cancel.is_cancelled():
                break

            # Strategy-level header
            print(f"[Strategy {idx:02d}/{total_strategies:02d}] {st.name}")

            r: TestResult | None = None
            if not detailed_console_output:
                # Compact mode: run parallel checks without per-domain prints.
                was_running = ctx.state.zapret.running
                prev_selected = ctx.state.zapret.selected_strategy
                prev_base = ctx.state.zapret.base_strategy
                prev_youtube = ctx.state.zapret.youtube_layer
                prev_discord = ctx.state.zapret.discord_layer
                try:
                    stop_zapret(ctx)
                    try:
                        start_zapret_interactive(ctx, st)
                    except WinwsStartError as e:
                        r = TestResult(strategy=st.name, ok=0, total=0, checks=[], status="invalid", error=str(e))
                        results.append(r)
                        # telemetry
                        missing_assets = _detect_missing_assets_from_error(r.error) if r.status != "ok" else []
                        avg_ms = _avg_ms_from_checks(r.checks)
                        fail = max(0, r.total - r.ok)
                        crashed = r.status != "ok"
                        score = _score_run(
                            ok=r.ok,
                            total=r.total,
                            missing_assets=len(missing_assets),
                            crashed=crashed,
                            avg_ms=avg_ms,
                        )
                        _append_strategy_run_jsonl(
                            ctx,
                            StrategyRunRecord(
                                ts=datetime.now(timezone.utc).isoformat(),
                                mode=mode,
                                domain_set=_safe_domain_set_key(domain_set),
                                strategy_id=st.name,
                                ok=r.ok,
                                fail=fail,
                                avg_ms=avg_ms,
                                score=score,
                                missing_assets=missing_assets,
                                error=r.error if r.status != "ok" else "",
                            ),
                        )
                        continue

                    time.sleep(settle_s)

                    last_print = 0.0

                    def _cb(*, done: int, total: int, ok: int, fail: int, elapsed_s: float) -> None:
                        nonlocal last_print
                        now = time.perf_counter()
                        if now - last_print < 0.4 and done < total:
                            return
                        last_print = now
                        print(_compact_progress_line(
                            strategy_name=st.name,
                            strategy_idx=idx,
                            strategies_total=total_strategies,
                            done=done,
                            total=total,
                            ok=ok,
                            fail=fail,
                            elapsed_s=elapsed_s,
                        ))

                    checks, partial_timeout = check_domains_compact(
                        domains,
                        timeout_s=float(settings["read_timeout_s"]),
                        parallel=concurrency,
                        mode=("quick" if mode == "quick" else "full"),
                        connect_timeout_s=float(settings["connect_timeout_s"]),
                        read_timeout_s=float(settings["read_timeout_s"]),
                        total_domain_timeout_s=float(settings["total_domain_timeout_s"]),
                        dns_cache=dns_cache,
                        cancel=cancel,
                        max_strategy_time_s=float(settings["max_strategy_time_s"]),
                        progress_cb=_cb,
                    )
                    okc = sum(1 for c in checks if c.ok)
                    dnsc = sum(1 for c in checks if c.dns_ok)
                    tcpc = sum(1 for c in checks if c.tcp_ok)
                    pingc = sum(1 for c in checks if c.ping_ok)
                    udpc = sum(1 for c in checks if c.udp443 == "ok")
                    measured_dns = any(c.dns_ok is not None for c in checks)
                    measured_tcp = any(c.tcp_ok is not None for c in checks)
                    measured_ping = any(c.ping_ok is not None for c in checks)
                    measured_udp = any(bool(c.udp443) for c in checks)
                    status = "ok"
                    err = ""
                    if partial_timeout:
                        status = "invalid"
                        err = "partial_timeout"
                    r = TestResult(
                        strategy=st.name,
                        ok=okc,
                        total=len(checks),
                        checks=checks,
                        dns_ok=dnsc,
                        tcp_ok=tcpc,
                        ping_ok=pingc,
                        udp_ok=udpc,
                        measured_dns=measured_dns,
                        measured_tcp=measured_tcp,
                        measured_ping=measured_ping,
                        measured_udp=measured_udp,
                        status=status,
                        error=err,
                    )
                    results.append(r)
                finally:
                    stop_zapret(ctx)
                    ctx.state.zapret.base_strategy = prev_base
                    ctx.state.zapret.selected_strategy = prev_selected
                    ctx.state.zapret.youtube_layer = prev_youtube
                    ctx.state.zapret.discord_layer = prev_discord
                    if was_running and prev_selected:
                        prev_strategy = find_strategy(ctx, prev_selected, kind="base") or find_strategy(ctx, prev_selected)
                        if prev_strategy:
                            try:
                                start_zapret_interactive(ctx, prev_strategy)
                            except Exception:
                                pass
            else:
                # Detailed mode: keep existing verbose printing, but allow bounded parallel
                # ONLY when progress=False (so here parallel must be None -> sequential).
                r = test_strategy(
                    ctx,
                    st,
                    domains,
                    settle_s=settle_s,
                    parallel=None,
                    show_progress=True,
                    mode="quick" if mode == "quick" else "full",
                )
                results.append(r)

            # telemetry (per strategy)
            if r is not None:
                missing_assets = _detect_missing_assets_from_error(r.error) if r.status != "ok" else []
                avg_ms = _avg_ms_from_checks(r.checks)
                fail = max(0, r.total - r.ok)
                crashed = r.status != "ok"
                score = _score_run(
                    ok=r.ok,
                    total=r.total,
                    missing_assets=len(missing_assets),
                    crashed=crashed,
                    avg_ms=avg_ms,
                )
                _append_strategy_run_jsonl(
                    ctx,
                    StrategyRunRecord(
                        ts=datetime.now(timezone.utc).isoformat(),
                        mode=mode,
                        domain_set=_safe_domain_set_key(domain_set),
                        strategy_id=st.name,
                        ok=r.ok,
                        fail=fail,
                        avg_ms=avg_ms,
                        score=score,
                        missing_assets=missing_assets,
                        error=r.error if r.status != "ok" else "",
                    ),
                )

    except KeyboardInterrupt:
        cancel.cancel()
        print("\nТест остановлен пользователем")
    finally:
        stop_zapret(ctx)

    # Persist classic results (txt + pin) by reusing existing helper.
    # We keep this behavior by building a minimal TestSessionSummary.
    out_name = f"results_all_strategies_{_safe_domain_set_key(domain_set)}_{mode}.txt"
    results_file = write_results(ctx, results, out_name)
    tmp_dir = _tmp_dir(ctx, f"all_strategies_{now_utc_iso().replace(':','-').replace('T','_')}")
    try:
        for st in candidates:
            save_strategy(tmp_dir, st)
        pinned = _pin_top_results(ctx, results, tmp_dir, top_n=top_n_pin)
    finally:
        _cleanup_tmp(tmp_dir)

    # Ranking
    ranking_src: list[tuple[str, TestResult, int, int, list[str]]] = []
    for r in results:
        missing_assets = _detect_missing_assets_from_error(r.error) if r.status != "ok" else []
        avg_ms = _avg_ms_from_checks(r.checks)
        fail = max(0, r.total - r.ok)
        crashed = r.status != "ok"
        score = _score_run(ok=r.ok, total=r.total, missing_assets=len(missing_assets), crashed=crashed, avg_ms=avg_ms)
        ranking_src.append((r.strategy, r, score, avg_ms, missing_assets))

    ranking_src.sort(key=lambda x: (x[2], x[1].ok, -x[3], x[0]), reverse=True)
    rows: list[StrategyRankingRow] = []
    for i, (name, r, score, avg_ms, missing_assets) in enumerate(ranking_src, start=1):
        rows.append(
            StrategyRankingRow(
                rank=i,
                strategy=name,
                ok=r.ok,
                fail=max(0, r.total - r.ok),
                avg_ms=avg_ms,
                missing_assets=missing_assets,
                score=score,
                status=r.status,
                error=r.error,
            )
        )

    _print_ranking_table(rows)
    ranking_json = _save_latest_ranking_json(ctx, rows, domain_set=domain_set, mode=mode)

    # Recommended strategy = best row with status ok and total>0, else best by score.
    recommended = next((r for r in rows if r.status == "ok" and (r.ok + r.fail) > 0), rows[0] if rows else None)
    if recommended:
        print(f"Recommended strategy: {recommended.strategy} (score={recommended.score}, ok={recommended.ok}, fail={recommended.fail})")

    summary = TestSessionSummary(results=results, pinned=pinned, results_file=results_file)
    return summary, rows, ranking_json


# Prevent pytest from collecting this helper as a test function.
test_strategy.__test__ = False  # type: ignore[attr-defined]


def _select_candidates(ctx: AppContext, group: str) -> list[Strategy]:
    from app.zapret_manager.features.selection import list_bases, list_layers

    tmp_flowseal = ctx.paths.strategies_generated_dir / "_tmp" / "packs" / "flowseal"
    tmp_stressozz = ctx.paths.strategies_generated_dir / "_tmp" / "packs" / "stressozz"
    tmp_bases = list_strategies(tmp_flowseal, kind="base") + list_strategies(tmp_stressozz, kind="base")
    tmp_yv = list_strategies(tmp_flowseal, kind="youtube") + list_strategies(tmp_stressozz, kind="youtube")
    tmp_dv = list_strategies(tmp_flowseal, kind="discord") + list_strategies(tmp_stressozz, kind="discord")

    if group == "v":
        bases = list_bases(ctx)
        out = [b for b in bases if b.name.lower().startswith("v") and b.name[1:].isdigit()]
        for st in tmp_bases:
            if st.name.lower().startswith("v") and st.name[1:].isdigit():
                out.append(st)
        seen: set[str] = set()
        uniq: list[Strategy] = []
        for st in out:
            if st.name in seen:
                continue
            seen.add(st.name)
            uniq.append(st)
        return uniq
    if group == "flowseal":
        out = [b for b in list_bases(ctx) if (b.upstream or "").lower() == "flowseal"]
        out.extend([b for b in tmp_bases if (b.upstream or "").lower() == "flowseal"])
        return out
    if group == "all":
        out: list[Strategy] = []
        seen: set[str] = set()
        for st in _select_candidates(ctx, "v") + _select_candidates(ctx, "flowseal"):
            if st.name in seen:
                continue
            seen.add(st.name)
            out.append(st)
        return out
    if group == "youtube":
        out = [s for s in list_layers(ctx, "youtube") if s.name.lower().startswith("yv")]
        out.extend([s for s in tmp_yv if s.name.lower().startswith("yv")])
        seen: set[str] = set()
        uniq: list[Strategy] = []
        for st in out:
            if st.name in seen:
                continue
            seen.add(st.name)
            uniq.append(st)
        return uniq
    if group == "discord":
        out = [s for s in list_layers(ctx, "discord") if s.name.lower().startswith("dv")]
        out.extend([s for s in tmp_dv if s.name.lower().startswith("dv")])
        seen: set[str] = set()
        uniq: list[Strategy] = []
        for st in out:
            if st.name in seen:
                continue
            seen.add(st.name)
            uniq.append(st)
        return uniq
    raise ValueError(f"Unknown candidates group: {group}")


def _select_top5_wide(results: list[TestResult]) -> list[TestResult]:
    ranked = sorted(results, key=lambda r: (r.ok, r.total, r.strategy), reverse=True)
    return [r for r in ranked if r.total > 0][:5]


def _print_session_table(results: list[TestResult]) -> None:
    print()
    print("Сводка тестирования")
    print("-" * 78)
    print(f"{'Стратегия':<18} {'OK/ALL':<10} {'FAIL':<6} Провалившиеся домены")
    print("-" * 78)
    for r in sorted(results, key=lambda x: (x.ok, x.total, x.strategy), reverse=True):
        failed = [c.domain for c in r.checks if not c.ok]
        failed_text = ", ".join(failed[:3])
        if len(failed) > 3:
            failed_text += f" +{len(failed) - 3}"
        print(f"{r.strategy:<18} {f'{r.ok}/{r.total}':<10} {len(failed):<6} {failed_text or '-'}")
    print("-" * 78)
    best_ok = max((r.ok for r in results), default=0)
    best = [r.strategy for r in results if r.ok == best_ok and r.total > 0]
    if best:
        print("Лучшие стратегии: " + ", ".join(best[:10]))
    print()


def test_session(
    ctx: AppContext,
    *,
    group: str | None = None,
    candidates: list[Strategy] | None = None,
    domains: list[str],
    out_name: str,
    settle_s: float = 1.5,
    top_n: int = 5,
    parallel: int | None = None,
    ensure_runtime: bool = True,
    ensure_flowseal: bool = False,
    ensure_stressozz: bool = False,
    mode: str = "full",
) -> TestSessionSummary:
    """Runs a human-readable strategy test session."""
    if ensure_runtime:
        _ensure_runtime(ctx)
    _ensure_pack_strategies(ctx, need_flowseal=ensure_flowseal, need_stressozz=ensure_stressozz)

    if candidates is None:
        if not group:
            raise ValueError("either candidates or group must be provided")
        candidates = _select_candidates(ctx, group)

    if not candidates:
        raise RuntimeError("No strategies found for test session (after ensure).")

    tmp_name = f"session_{now_utc_iso().replace(':','-').replace('T','_')}_{next(tempfile._get_candidate_names())}"
    tmp_dir = _tmp_dir(ctx, tmp_name)
    try:
        for st in candidates:
            save_strategy(tmp_dir, st)

        session_strategies = _list_tmp_strategies(ctx, tmp_dir)
        if not session_strategies:
            raise RuntimeError("No strategies to test.")

        print()
        print(f"Стратегий в тесте: {len(session_strategies)}")
        print(f"Доменов в тесте: {len([d for d in domains if d.strip()])}")
        print("Формат: HTTP(S) GET; HTTP 2xx-4xx = OK, timeout/connection/tls = FAIL")
        print()

        results: list[TestResult] = []
        for st in session_strategies:
            log.info("testing strategy %s", st.name)
            results.append(
                test_strategy(
                    ctx,
                    st,
                    domains,
                    settle_s=settle_s,
                    parallel=parallel,
                    show_progress=True,
                    mode=mode,
                )
            )

        _print_session_table(results)
        results_file = write_results(ctx, results, out_name)
        pinned = _pin_top_results(ctx, results, tmp_dir, top_n=top_n)
        return TestSessionSummary(results=results, pinned=pinned, results_file=results_file)
    finally:
        _cleanup_tmp(tmp_dir)
        if ensure_flowseal:
            _cleanup_tmp(_tmp_pack_dir(ctx, "flowseal"))
        if ensure_stressozz:
            _cleanup_tmp(_tmp_pack_dir(ctx, "stressozz"))


# Prevent pytest from collecting this helper as a test function.
test_session.__test__ = False  # type: ignore[attr-defined]


def classify_effect(baseline_ok: bool, strategy_ok: bool) -> str:
    """Classify the effect of strategy compared to baseline."""
    if not baseline_ok and strategy_ok:
        return "improved"
    if baseline_ok and strategy_ok:
        return "already_ok"
    if not baseline_ok and not strategy_ok:
        return "no_effect"
    if baseline_ok and not strategy_ok:
        return "worsened"
    return "invalid"


def classify_effect_from_checks(baseline_check: DomainCheck, strategy_check: DomainCheck) -> str:
    """Classify effect from DomainCheck objects."""
    return classify_effect(baseline_check.ok, strategy_check.ok)


def _ensure_winws_stopped(ctx: AppContext) -> None:
    """Ensure winws is stopped and verify it's really dead."""
    stop_zapret(ctx)
    # Small delay to allow winws to shut down
    time.sleep(0.5)
    
    # Check if winws process is still alive
    if ctx.state.zapret.running and ctx.state.zapret.pid:
        # Try to kill the process forcefully
        try:
            import os
            os.kill(ctx.state.zapret.pid, 9)
            ctx.state.zapret.running = False
            ctx.state.zapret.pid = None
            log.info("Force-killed remaining winws process")
        except Exception:
            pass
    
    # Final verification
    if ctx.state.zapret.running:
        raise RuntimeError("WinWS failed to stop after zapret stop command")


def proof_of_effect(
    ctx: AppContext, 
    strategy: Strategy, 
    domains: list[str], 
    *, 
    settle_s: float = 1.5, 
    parallel: int = 6,
    mode: str = "full",
) -> ProofResult:
    """Proof-of-effect test: baseline vs strategy with winws evidence."""
    
    # Save previous state
    was_running = ctx.state.zapret.running
    prev_base = ctx.state.zapret.base_strategy
    prev_selected = ctx.state.zapret.selected_strategy
    prev_youtube = ctx.state.zapret.youtube_layer
    prev_discord = ctx.state.zapret.discord_layer
    
    restore_warning: str | None = None
    result: ProofResult | None = None

    try:
        # Phase 1: Stop winws and verify baseline is without winws
        _ensure_winws_stopped(ctx)
        winws_alive_at_start = False

        # Phase 2: Run baseline check (without winws)
        baseline_checks = check_domains_detailed(domains, parallel=parallel, progress=False, mode=mode)

        # Phase 3: Start strategy and verify winws is alive
        start_zapret_interactive(ctx, strategy)
        time.sleep(settle_s)

        # Strict proof requirement:
        # - running must be True
        # - pid must be known
        # - pid must be alive (PR-1 health-check logic)
        if not ctx.state.zapret.running:
            raise WinwsStartError("WinWS process failed to start or died immediately")

        if ctx.state.zapret.pid is None:
            raise WinwsStartError("WinWS started but PID is unknown")

        winws_pid = int(ctx.state.zapret.pid)
        winws_alive_at_end = is_pid_alive(winws_pid)
        if not winws_alive_at_end:
            raise WinwsStartError("WinWS process is not alive after start")

        # Phase 4: Run strategy check (with winws)
        strategy_checks = check_domains_detailed(domains, parallel=parallel, progress=False, mode=mode)

        # Phase 5: Compare baseline vs strategy
        rows: list[ProofRow] = []
        improved = 0
        already_ok = 0
        no_effect = 0
        worsened = 0

        for baseline_check, strategy_check in zip(baseline_checks, strategy_checks):
            effect = classify_effect_from_checks(baseline_check, strategy_check)

            row = ProofRow(
                domain=baseline_check.domain,
                baseline_ok=baseline_check.ok,
                strategy_ok=strategy_check.ok,
                effect=effect,
                baseline_error=baseline_check.error if not baseline_check.ok else None,
                strategy_error=strategy_check.error if not strategy_check.ok else None,
                baseline_ms=baseline_check.elapsed_ms,
                strategy_ms=strategy_check.elapsed_ms,
            )
            rows.append(row)

            if effect == "improved":
                improved += 1
            elif effect == "already_ok":
                already_ok += 1
            elif effect == "no_effect":
                no_effect += 1
            elif effect == "worsened":
                worsened += 1

        total = len(rows)
        strategy_effect_proven = improved > 0

        result = ProofResult(
            strategy_name=strategy.name,
            rows=rows,
            total=total,
            improved=improved,
            already_ok=already_ok,
            no_effect=no_effect,
            worsened=worsened,
            invalid=0,
            strategy_effect_proven=strategy_effect_proven,
            winws_pid=winws_pid,
            winws_alive_at_start=winws_alive_at_start,
            winws_alive_at_end=winws_alive_at_end,
            invalid_reason=None,
            restore_warning=None,
        )

    except WinwsStartError as e:
        # Strategy failed to start, don't run domain checks.
        result = ProofResult(
            strategy_name=strategy.name,
            rows=[],
            total=0,
            improved=0,
            already_ok=0,
            no_effect=0,
            worsened=0,
            invalid=1,
            strategy_effect_proven=False,
            winws_pid=None,
            winws_alive_at_start=False,
            winws_alive_at_end=False,
            invalid_reason=str(e),
            restore_warning=None,
        )

    except Exception as e:
        # If anything failed during the test (baseline probe, compare, etc.)
        result = ProofResult(
            strategy_name=strategy.name,
            rows=[],
            total=0,
            improved=0,
            already_ok=0,
            no_effect=0,
            worsened=0,
            invalid=1,
            strategy_effect_proven=False,
            winws_pid=None,
            winws_alive_at_start=False,
            winws_alive_at_end=False,
            invalid_reason=str(e),
            restore_warning=None,
        )

    finally:
        # Phase 6: Stop test winws and restore previous state
        stop_zapret(ctx)

        if was_running and prev_selected:
            try:
                prev_strategy = find_strategy(ctx, prev_selected, kind="base") or find_strategy(ctx, prev_selected)
                if prev_strategy:
                    youtube = find_strategy(ctx, prev_youtube, kind="youtube") if prev_youtube else None
                    discord = find_strategy(ctx, prev_discord, kind="discord") if prev_discord else None
                    start_zapret_interactive(ctx, prev_strategy, youtube=youtube, discord=discord)
                else:
                    restore_warning = f"Previous strategy '{prev_selected}' not found for restoration"
            except Exception as e:
                # IMPORTANT: do not turn proof into invalid if restore failed.
                restore_warning = f"Failed to restore previous state: {e}"

    # Record failed domains from strategy checks
    if result and result.rows:
        try:
            from app.zapret_manager.features.problem_domains import add_from_domain_checks
            # We need to record domains that failed during strategy test
            for row in result.rows:
                if not row.strategy_ok:
                    try:
                        from app.zapret_manager.features.problem_domains import add_problem_domain
                        add_problem_domain(
                            ctx,
                            domain=row.domain,
                            source="strategy",
                            fail_reason="strategy_fail",
                            error=row.strategy_error or "",
                        )
                    except Exception:
                        pass
        except Exception as e:
            log.warning("Failed to record problem domains from proof-of-effect: %s", e)

    if result is None:
        # Defensive fallback, should not happen.
        result = ProofResult(
            strategy_name=strategy.name,
            rows=[],
            total=0,
            improved=0,
            already_ok=0,
            no_effect=0,
            worsened=0,
            invalid=1,
            strategy_effect_proven=False,
            winws_pid=None,
            winws_alive_at_start=False,
            winws_alive_at_end=False,
            invalid_reason="proof_of_effect: internal error (no result)",
            restore_warning=None,
        )

    if restore_warning:
        result = replace(result, restore_warning=restore_warning)

    return result


def write_results(ctx: AppContext, results: list[TestResult], file_name: str) -> Path:
    out = ctx.paths.results_dir / file_name
    lines = [f"# {now_utc_iso()}", ""]
    lines.append("Summary")
    lines.append("-------")
    for r in sorted(results, key=lambda x: (x.ok, x.total, x.strategy), reverse=True):
        if r.status != "ok":
            lines.append(f"{r.strategy} -> INVALID ({r.error})")
        else:
            lines.append(f"{r.strategy} -> {r.summary_text()}")
    lines.append("")
    lines.append("Details")
    lines.append("-------")
    for r in sorted(results, key=lambda x: (x.ok, x.total, x.strategy), reverse=True):
        lines.append("")
        if r.status != "ok":
            lines.append(f"[{r.strategy}] INVALID ({r.error})")
            continue
        lines.append(f"[{r.strategy}] {r.summary_text()}")
        for i, c in enumerate(r.checks, start=1):
            lines.append(_format_domain_row(i, r.total, c))
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
