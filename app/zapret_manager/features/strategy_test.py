from __future__ import annotations

import logging
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import requests

from zapret_manager.core.app_context import AppContext
from zapret_manager.features.selection import find_strategy
from zapret_manager.features.upstreams import sync_flowseal, sync_stressozz_strategies
from zapret_manager.features.zapret_runtime import start_zapret_interactive, stop_zapret
from zapret_manager.strategies.model import Strategy
from zapret_manager.strategies.store import list_strategies, save_strategy
from zapret_manager.utils.timex import now_utc_iso


log = logging.getLogger(__name__)


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


def _fetch_one_detail(url: str, *, timeout_s: float) -> DomainCheck:
    display = _display_domain(url)
    start = time.perf_counter()
    try:
        # A normal GET is closer to real browser behavior than just opening TCP.
        # We intentionally treat HTTP 4xx as network OK: domain is reachable, even
        # if the server rejects the exact path.
        r = requests.get(url, timeout=timeout_s, allow_redirects=True)
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


def _format_domain_row(index: int, total: int, check: DomainCheck) -> str:
    status = "OK" if check.ok else "FAIL"
    extra = f"{check.elapsed_ms} ms"
    if check.status_code is not None:
        extra += f", HTTP {check.status_code}"
    if check.error:
        extra += f", {check.error}"
    return f"[{index:02d}/{total:02d}] {check.domain:<42} {status:<5} {extra}"


def check_domains_detailed(
    domains: list[str],
    *,
    timeout_s: float = 3.0,
    parallel: int | None = None,
    progress: bool = False,
) -> list[DomainCheck]:
    cleaned = [_normalize_url(d) for d in domains if d.strip()]
    cleaned = [u for u in cleaned if u]
    if not cleaned:
        return []

    # If progress is requested, keep sequential order so the user sees exactly
    # which domain is being tested now. This is slower but much more readable.
    if progress or not parallel or parallel <= 1:
        checks: list[DomainCheck] = []
        total = len(cleaned)
        for i, url in enumerate(cleaned, start=1):
            domain = _display_domain(url)
            if progress:
                print(f"[{i:02d}/{total:02d}] Проверяю {domain:<42} ... ", end="", flush=True)
            check = _fetch_one_detail(url, timeout_s=timeout_s)
            checks.append(check)
            if progress:
                suffix = f"{check.elapsed_ms} ms"
                if check.error:
                    suffix += f", {check.error}"
                print(f"{check.status_text:<5} {suffix}")
        return checks

    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=int(parallel)) as ex:
        return list(ex.map(lambda u: _fetch_one_detail(u, timeout_s=timeout_s), cleaned))


def check_domains(domains: list[str], *, timeout_s: float = 3.0, parallel: int | None = None) -> tuple[int, int]:
    checks = check_domains_detailed(domains, timeout_s=timeout_s, parallel=parallel, progress=False)
    return sum(1 for c in checks if c.ok), len(checks)


def control_test(domains: list[str], *, parallel: int | None = None) -> TestResult:
    """Legacy helper used by UI: baseline check without any strategy running."""
    checks = check_domains_detailed(domains, parallel=parallel, progress=False)
    ok = sum(1 for c in checks if c.ok)
    return TestResult(strategy="control", ok=ok, total=len(checks), checks=checks)


def _runtime_ready(ctx: AppContext) -> bool:
    """Best-effort check that runtime is installed and winws.exe is discoverable."""
    try:
        from zapret_manager.features.zapret_runtime import detect_runtime_files

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
    print(f"Итог {result.strategy}: {result.ok}/{result.total} OK")
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
    settle_s: float = 1.5,
    parallel: int | None = None,
    show_progress: bool = True,
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
        start_zapret_interactive(ctx, strategy)
        time.sleep(settle_s)
        checks = check_domains_detailed(domains, parallel=parallel, progress=show_progress)
        ok = sum(1 for c in checks if c.ok)
        result = TestResult(strategy=strategy.name, ok=ok, total=len(checks), checks=checks)
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


def _select_candidates(ctx: AppContext, group: str) -> list[Strategy]:
    from zapret_manager.features.selection import list_bases, list_layers

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
            results.append(test_strategy(ctx, st, domains, settle_s=settle_s, parallel=parallel, show_progress=True))

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


def write_results(ctx: AppContext, results: list[TestResult], file_name: str) -> Path:
    out = ctx.paths.results_dir / file_name
    lines = [f"# {now_utc_iso()}", ""]
    lines.append("Summary")
    lines.append("-------")
    for r in sorted(results, key=lambda x: (x.ok, x.total, x.strategy), reverse=True):
        lines.append(f"{r.strategy} -> {r.ok}/{r.total}")
    lines.append("")
    lines.append("Details")
    lines.append("-------")
    for r in sorted(results, key=lambda x: (x.ok, x.total, x.strategy), reverse=True):
        lines.append("")
        lines.append(f"[{r.strategy}] {r.ok}/{r.total}")
        for i, c in enumerate(r.checks, start=1):
            lines.append(_format_domain_row(i, r.total, c))
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
