from __future__ import annotations

import logging
import time
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.state import save_state
from app.zapret_manager.strategies.composer import compose
from app.zapret_manager.strategies.model import Strategy, Command, CommandType
from app.zapret_manager.strategies.overlays import apply_overlays
from app.zapret_manager.utils.platform import is_admin, is_windows
from app.zapret_manager.utils.subprocessx import popen_detached, run

log = logging.getLogger(__name__)

def start_zapret_interactive(*args, **kwargs):
    log.warning("start_zapret_interactive is a placeholder and does nothing.")
    pass

def stop_zapret(*args, **kwargs):
    log.warning("stop_zapret is a placeholder and does nothing.")
    pass



log = logging.getLogger(__name__)


def _mask_cmd_preview(cmd: list[str], *, limit: int = 120) -> str:
    """Return a safe, masked multiline preview of argv.

    IMPORTANT: must not leak secrets from subscription/proxy links.
    """
    try:
        from app.zapret_manager.core.mask import mask_secrets
    except Exception:  # pragma: no cover
        mask_secrets = lambda s: s  # type: ignore

    lines = []
    for i, a in enumerate(cmd[:limit]):
        lines.append(f"[{i}] {a}")
    if len(cmd) > limit:
        lines.append(f"... <truncated: {len(cmd) - limit} args>")
    return str(mask_secrets("\n".join(lines)))


def _parse_missing_from_problem_line(line: str) -> tuple[str, str] | None:
    # line example: "missing file for --hostlist: C:\\... (cwd=...)"
    s = str(line)
    if not s.startswith("missing file for "):
        return None
    try:
        rest = s[len("missing file for ") :]
        opt, tail = rest.split(":", 1)
        path = tail.strip()
        if " (cwd=" in path:
            path = path.split(" (cwd=", 1)[0].strip()
        return opt.strip(), path
    except Exception:
        return None


def format_preflight_diagnostics_ru(
    *,
    strategy_name: str,
    cmd: list[str],
    problems: list[str],
    warnings: list[str],
    ctx: "AppContext",
) -> str:
    """Format a user-facing preflight report in Russian.

    This is used to avoid "silent INVALID": user sees exact missing assets.
    """
    missing_lists: list[str] = []
    missing_fake: list[str] = []
    missing_other: list[str] = []

    for p in problems:
        parsed = _parse_missing_from_problem_line(str(p))
        if not parsed:
            continue
        opt, path = parsed
        opt_l = opt.lower()
        # categorize
        if opt_l in {"--hostlist", "--hostlist-exclude", "--ipset", "--ipset-exclude"}:
            missing_lists.append(path)
        elif opt_l.startswith("--dpi-desync") or opt_l.endswith("-pattern"):
            missing_fake.append(path)
        else:
            missing_other.append(f"{opt}: {path}")

    # runtime core binaries
    # NOTE: we must report missing binary precisely: winws.exe vs winws2.exe.
    missing_bins: list[str] = []
    try:
        exe0 = Path(str(cmd[0] if cmd else "")).name.lower()
        requested_engine = "winws2" if exe0 == "winws2.exe" else "winws"
        rh = runtime_health(ctx, requested_engine=requested_engine)

        # Check selected exe + WinDivert.
        for key in ("selected_binary", "windivert_dll", "windivert_sys"):
            v = str(rh.get(key) or "")
            if not v:
                continue
            if not Path(v).exists():
                missing_bins.append(v)
    except Exception:
        pass

    lines: list[str] = []
    lines.append(f"Стратегия: {strategy_name}")
    lines.append("Статус: INVALID")
    lines.append("")

    if missing_bins:
        lines.append("Не хватает бинарников runtime:")
        for p in missing_bins:
            lines.append(f"- {p}")
        lines.append("")

    if missing_lists:
        lines.append("Не хватает списков (lists):")
        for p in sorted(set(missing_lists)):
            lines.append(f"- {p}")
        lines.append("")

    if missing_fake:
        lines.append("Не хватает fake/pattern файлов:")
        for p in sorted(set(missing_fake)):
            lines.append(f"- {p}")
        lines.append("")

    # other problems
    other = [p for p in problems if not str(p).startswith("missing file for ") and not str(p).startswith("WARN:")]
    if other:
        lines.append("Ошибки preflight:")
        for p in other[:50]:
            lines.append(f"- {p}")
        if len(other) > 50:
            lines.append(f"... <truncated: {len(other) - 50} lines>")
        lines.append("")

    if warnings:
        lines.append("Предупреждения:")
        for w in warnings[:50]:
            lines.append(f"- {w}")
        if len(warnings) > 50:
            lines.append(f"... <truncated: {len(warnings) - 50} lines>")
        lines.append("")

    lines.append("Preview команды (masked):")
    lines.append(_mask_cmd_preview(cmd))
    return "\n".join(lines)


@dataclass(frozen=True)
class WinwsLogs:
    stdout: Path
    stderr: Path


class WinwsStartError(RuntimeError):
    """winws was launched but is not active (died instantly / invalid args / etc)."""

    def __init__(self, message: str, *, exit_code: int | None = None, stderr_tail: str = ""):
        super().__init__(message)
        self.exit_code = exit_code
        self.stderr_tail = stderr_tail


def _find_first_dir(root: Path, names: list[str]) -> Path | None:
    for name in names:
        for p in root.rglob(name):
            if p.is_dir():
                return p
    return None


def _runtime_fake_dir(ctx: "AppContext") -> Path:
    zr = zapret_root(ctx)
    preferred = zr / "files" / "fake"
    if preferred.exists():
        return preferred
    found = _find_first_dir(zr, ["fake"]) if zr.exists() else None
    return found or preferred


def _runtime_lists_dir(ctx: "AppContext") -> Path:
    zr = zapret_root(ctx)
    preferred = zr / "lists"
    if preferred.exists():
        return preferred
    found = _find_first_dir(zr, ["lists"]) if zr.exists() else None
    return found or preferred


def _manager_lists_dir(ctx: "AppContext") -> Path:
    return ctx.paths.lists_dir.resolve()


def _rt_lists_dir(ctx: "AppContext") -> Path:
    # Explicit runtime lists dir (legacy / fallback).
    return _runtime_lists_dir(ctx).resolve()


def _resolve_list_path_compat(ctx: "AppContext", path_str: str) -> str:
    """Best-effort mapping for list file names.

    We support common naming differences between bundles/strategies:
    - google.txt <-> list-google.txt
    - exclude.txt <-> list-exclude.txt
    - general.txt <-> list-general.txt
    - general-user.txt <-> list-general-user.txt
    - ipset-exclude.txt <-> list-ipset-exclude.txt
    - ipset-all.txt <-> list-ipset-all.txt

    This function DOES NOT create empty files.
    """
    # Path() on non-Windows treats backslashes as regular characters.
    # Since we frequently build Win-style paths even in unit tests on POSIX,
    # normalize separators when not on Windows.
    norm = path_str
    if os.name != "nt":
        norm = norm.replace("\\", "/")

    try:
        p = Path(norm)
    except Exception:
        return path_str

    name = p.name
    parent = p.parent
    low = name.lower()

    # candidate name swaps
    swaps: dict[str, list[str]] = {
        "google.txt": ["list-google.txt"],
        "list-google.txt": ["google.txt"],
        "exclude.txt": ["list-exclude.txt", "hostlist-exclude.txt"],
        "list-exclude.txt": ["exclude.txt"],
        "general.txt": ["list-general.txt"],
        "list-general.txt": ["general.txt"],
        "general-user.txt": ["list-general-user.txt"],
        "list-general-user.txt": ["general-user.txt"],
        "ipset-exclude.txt": ["list-ipset-exclude.txt"],
        "list-ipset-exclude.txt": ["ipset-exclude.txt"],
        "ipset-all.txt": ["list-ipset-all.txt"],
        "list-ipset-all.txt": ["ipset-all.txt"],
    }

    cand_names = swaps.get(low)
    if not cand_names:
        return path_str

    for cn in cand_names:
        cp = (parent / cn)
        if cp.exists():
            return str(cp)
    return path_str


def _parse_ports_expr(expr: str) -> tuple[list[int], list[tuple[int, int]], list[str]]:
    """Parse port expression like "80,443,1024-65535".

    Returns (ports, ranges, problems).
    - ports: list of individual ports (dedup not guaranteed)
    - ranges: list of (start,end)
    - problems: human-readable errors

    NOTE: This parser is strict and is used for preflight validation.
    """
    problems: list[str] = []
    expr = (expr or "").strip()
    if not expr:
        return ([], [], ["empty port expression"])
    if " " in expr or "\t" in expr:
        problems.append("port expression contains spaces")

    raw_items = expr.split(",")
    if any(i == "" for i in raw_items):
        problems.append("port expression contains empty element (e.g. '443,,80' or trailing comma)")

    ports: list[int] = []
    ranges: list[tuple[int, int]] = []
    for item in raw_items:
        item = item.strip()
        if not item:
            continue
        if "-" in item:
            parts = item.split("-", 1)
            a = parts[0].strip()
            b = parts[1].strip()
            if not a.isdigit() or not b.isdigit():
                problems.append(f"invalid range token: {item}")
                continue
            lo = int(a)
            hi = int(b)
            if not (1 <= lo <= 65535) or not (1 <= hi <= 65535):
                problems.append(f"range out of bounds: {item}")
                continue
            if lo > hi:
                problems.append(f"reversed range: {item}")
                continue
            ranges.append((lo, hi))
        else:
            if not item.isdigit():
                problems.append(f"invalid port token: {item}")
                continue
            n = int(item)
            if not (1 <= n <= 65535):
                problems.append(f"port out of bounds: {n}")
                continue
            ports.append(n)
    return (ports, ranges, problems)


def _normalize_ports_expr(expr: str) -> tuple[str, list[str]]:
    """Normalize a port list expression to stable order + dedup.

    Keeps ranges intact.
    Returns (normalized_expr, problems).
    """
    ports, ranges, problems = _parse_ports_expr(expr)
    if problems:
        return (expr, problems)
    # dedup and sort
    ports_u = sorted(set(ports))
    ranges_u = sorted(set(ranges), key=lambda x: (x[0], x[1]))
    parts: list[str] = [str(p) for p in ports_u] + [f"{a}-{b}" for a, b in ranges_u]
    return (",".join(parts), [])


def normalize_winws_args(args: list[str]) -> list[str]:
    """Normalize winws argv elements.

    Handles:
    - actual newlines \\n / \\r inside one argv element → split into separate argv;
    - escaped literal \\n / \\r\\n inside one argv element → split too;
    - trim whitespace, remove empty lines;
    - preserve order and --new blocks;
    - do NOT split by normal spaces;
    - do NOT break Windows paths like C:\\...;
    - do NOT aggressively shell-split already prepared argv;
    - --dpi-desync-split-seqovl-pattern=C:\\path with spaces\\file.bin must remain one argv.

    After normalization, if any argv still contains actual newline or escaped newline,
    validation should treat it as an error:
        strategy contains multiline argv element after normalization
    """
    normalized: list[str] = []
    for arg in args:
        if arg is None:
            continue
        a = str(arg)
        # Check for escaped newline literals \\n or \\r\\n
        if "\\n" in a or "\\r\\n" in a:
            # Split by escaped newline
            parts = a.replace("\\r\\n", "\\n").split("\\n")
            for part in parts:
                part = part.strip()
                if part:
                    normalized.append(part)
            continue
        # Check for actual newlines
        if "\n" in a or "\r" in a:
            lines = a.splitlines()
            for line in lines:
                line = line.strip()
                if line:
                    normalized.append(line)
            continue
        # Normal arg - trim and keep
        a = a.strip()
        if a:
            normalized.append(a)
    return normalized


def _infer_wf_args_from_filters(args: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Infer global WinDivert capture filters (--wf-tcp/--wf-udp) from per-block filters.

    Returns (wf_args, warnings, errors).
    - wf_args: list like ["--wf-tcp=80,443", "--wf-udp=443"] (order tcp,udp)
    """
    warnings: list[str] = []
    errors: list[str] = []

    has_wf_tcp = any(a.startswith("--wf-tcp=") for a in args)
    has_wf_udp = any(a.startswith("--wf-udp=") for a in args)

    tcp_filters: list[str] = []
    udp_filters: list[str] = []
    for a in args:
        if a.startswith("--filter-tcp="):
            tcp_filters.append(a.split("=", 1)[1])
        if a.startswith("--filter-udp="):
            udp_filters.append(a.split("=", 1)[1])

    wf_args: list[str] = []
    if tcp_filters and not has_wf_tcp:
        union_raw = ",".join([x for x in tcp_filters if x is not None])
        norm, probs = _normalize_ports_expr(union_raw)
        if probs:
            errors.append("cannot infer --wf-tcp: " + "; ".join(probs))
        else:
            wf_args.append(f"--wf-tcp={norm}")

    if udp_filters and not has_wf_udp:
        union_raw = ",".join([x for x in udp_filters if x is not None])
        norm, probs = _normalize_ports_expr(union_raw)
        if probs:
            errors.append("cannot infer --wf-udp: " + "; ".join(probs))
        else:
            wf_args.append(f"--wf-udp={norm}")

    # If strategy uses per-block filters but we could not infer wf, it is a hard error.
    if tcp_filters and not has_wf_tcp and not any(a.startswith("--wf-tcp=") for a in wf_args):
        errors.append("missing WinDivert capture filter for TCP: add --wf-tcp=... (or fix --filter-tcp=... ports)")
    if udp_filters and not has_wf_udp and not any(a.startswith("--wf-udp=") for a in wf_args):
        errors.append("missing WinDivert capture filter for UDP: add --wf-udp=... (or fix --filter-udp=... ports)")

    return (wf_args, warnings, errors)


def runtime_health(ctx: "AppContext", *, requested_engine: str = "auto") -> dict[str, object]:
    """Checks that bundled runtime exists and has required files.

    Core bypass readiness requires winws.exe and WinDivert files. Extra assets
    such as fake/list/blockcheck are reported as problems but do not make the
    whole runtime unusable, because some strategies can still start without
    blockcheck and some bundles have slightly different asset layouts.
    """
    rt = _runtime_root(ctx)
    zr = zapret_root(ctx)

    winws = _find_first(zr, ["winws.exe"]) if zr.exists() else None
    winws2 = _find_first(zr, ["winws2.exe"]) if zr.exists() else None

    windivert_dll = zr / "WinDivert.dll"
    windivert_sys = zr / "WinDivert64.sys"
    blockcheck_cmd = _find_first(zr, ["blockcheck.cmd"]) if zr.exists() else None
    fake_dir = _runtime_fake_dir(ctx)
    # Canonical lists dir (manager): DedZapretData/data/lists
    mgr_lists_dir = _manager_lists_dir(ctx)
    # Legacy runtime lists dir (optional): DedZapretData/runtime/zapret/lists
    rt_lists_dir = _rt_lists_dir(ctx)

    ok = True
    problems: list[str] = []

    # Core runtime: required for ANY start
    core_ok = True

    if not rt.exists():
        ok = False
        core_ok = False
        problems.append(f"runtime dir not found: {rt}")
    if not zr.exists():
        ok = False
        core_ok = False
        problems.append(f"zapret dir not found: {zr}")
    if not winws:
        ok = False
        core_ok = False
        problems.append("winws.exe not found")
    if not windivert_dll.exists():
        ok = False
        core_ok = False
        problems.append("WinDivert.dll not found")
    if not windivert_sys.exists():
        ok = False
        core_ok = False
        problems.append("WinDivert64.sys not found")
    if not blockcheck_cmd:
        problems.append("blockcheck.cmd not found")
    if not fake_dir.exists():
        problems.append(f"fake files dir not found: {fake_dir}")
    if not mgr_lists_dir.exists():
        problems.append(f"manager lists dir not found: {mgr_lists_dir}")
    # runtime lists are optional fallback
    if not rt_lists_dir.exists():
        problems.append(f"runtime lists dir not found (optional): {rt_lists_dir}")

    # Selected binary (for explicit winws2 compatibility diagnostics).
    # Backward compatibility: the "ok" status still reflects winws.exe readiness.
    req = str(requested_engine or "").strip().lower()
    if req not in {"", "auto", "winws", "winws2"}:
        req = "auto"

    if req == "winws2":
        selected_engine = "winws2"
        selected_binary = str(winws2 or (zr / "winws2.exe"))
    else:
        # auto + winws default
        selected_engine = "winws"
        selected_binary = str(winws or (zr / "winws.exe"))

    return {
        # Backward compatible flag (core runtime)
        "ok": core_ok,
        "core_ok": core_ok,
        "runtime_dir": str(rt),
        "zapret_dir": str(zr),
        # canonical binaries
        "winws": str(winws) if winws else "",
        "winws2": str(winws2) if winws2 else "",
        "winws_exists": bool(winws and Path(winws).exists()),
        "winws2_exists": bool(winws2 and Path(winws2).exists()),
        # selection diagnostics
        "requested_engine": ("auto" if req in {"", "auto"} else req),
        "selected_engine": selected_engine,
        "selected_binary": selected_binary,
        "strategy_requested_binary": ("winws2.exe" if req == "winws2" else "winws.exe" if req == "winws" else "auto"),
        "windivert_dll": str(windivert_dll),
        "windivert_sys": str(windivert_sys),
        "windivert_dll_exists": bool(windivert_dll.exists()),
        "windivert_sys_exists": bool(windivert_sys.exists()),
        "fake_dir": str(fake_dir),
        "lists_dir": str(mgr_lists_dir),
        "rt_lists_dir": str(rt_lists_dir),
        "blockcheck": str(blockcheck_cmd) if blockcheck_cmd else "",
        "problems": problems,
    }


def zapret_root(ctx: "AppContext") -> Path:
    """Runtime root for zapret-win-bundle content."""
    return (_runtime_root(ctx) / "zapret").resolve()


def runtime_diagnostics_text(ctx: "AppContext") -> str:
    """Human-friendly runtime diagnostics with actionable instructions."""
    h = runtime_health(ctx)
    rt = Path(str(h.get("runtime_dir", "")))
    zr = Path(str(h.get("zapret_dir", "")))

    def okflag(p: Path) -> str:
        return "OK" if p.exists() else "MISSING"

    lines: list[str] = []
    lines.append("Runtime diagnostics")
    lines.append("-----------------")
    lines.append(f"config path: {ctx.paths.config_file} ({okflag(ctx.paths.config_file)})")
    lines.append(f"sources path: {ctx.paths.sources_file} ({okflag(ctx.paths.sources_file)})")
    lines.append(f"runtime root: {rt} ({okflag(rt)})")
    lines.append(f"zapret root:  {zr} ({okflag(zr)})")
    lines.append("")
    winws = Path(str(h.get("winws") or "")) if h.get("winws") else (zr / "winws.exe")
    winws2 = Path(str(h.get("winws2") or "")) if h.get("winws2") else (zr / "winws2.exe")
    lines.append(f"winws.exe:        {winws} ({okflag(winws)})")
    lines.append(f"winws2.exe:       {winws2} ({okflag(winws2)})")
    lines.append(f"requested_engine: {h.get('requested_engine')}")
    lines.append(f"selected_engine:  {h.get('selected_engine')}")
    lines.append(f"selected_binary:  {h.get('selected_binary')}")
    wdd = Path(str(h.get("windivert_dll") or (zr / 'WinDivert.dll')))
    wds = Path(str(h.get("windivert_sys") or (zr / 'WinDivert64.sys')))
    lines.append(f"WinDivert.dll:    {wdd} ({okflag(wdd)})")
    lines.append(f"WinDivert64.sys:  {wds} ({okflag(wds)})")
    fake_dir = Path(str(h.get("fake_dir") or _runtime_fake_dir(ctx)))
    lists_dir = Path(str(h.get("lists_dir") or _manager_lists_dir(ctx)))
    rt_lists_dir = Path(str(h.get("rt_lists_dir") or _rt_lists_dir(ctx)))
    lines.append(f"fake dir:         {fake_dir} ({okflag(fake_dir)})")
    lines.append(f"lists dir:        {lists_dir} ({okflag(lists_dir)})")
    lines.append(f"rt lists dir:     {rt_lists_dir} ({okflag(rt_lists_dir)})")
    bc = Path(str(h.get("blockcheck") or (zr / 'blockcheck' / 'blockcheck.cmd')))
    lines.append(f"blockcheck.cmd:   {bc} ({okflag(bc)})")

    problems = h.get("problems") or []
    if problems:
        lines.append("\nProblems:")
        for p in problems:
            lines.append(f"- {p}")

        lines.append("\nWhat to do:")
        lines.append("- Core start needs winws.exe + WinDivert.dll + WinDivert64.sys.")
        lines.append("- Some strategies also need files/fake and lists assets.")
        lines.append("- blockcheck is optional for normal start, but needed for blockcheck menu.")
        lines.append("- Re-download/re-extract the release, or copy zapret-win-bundle files into:")
        lines.append(f"  {zr}")

    return "\n".join(lines)


def require_runtime_ok(ctx: "AppContext") -> None:
    h = runtime_health(ctx)
    if bool(h.get("ok")):
        return
    problems = h.get("problems") or []
    msg = "Bundled runtime is missing or broken. Re-download/re-extract the release."
    if problems:
        msg += "\nProblems:\n- " + "\n- ".join(str(x) for x in problems)
    raise RuntimeError(msg)


def validate_strategy_assets(ctx: "AppContext", strategy: Strategy) -> list[str]:
    """Validate that all file-based assets referenced by a strategy exist.

    This does NOT start winws. Used for UI health reporting.
    """
    try:
        cmd = build_command(ctx, strategy)
        cwd = zapret_root(ctx)
        return validate_winws_command(ctx, cmd=cmd, cwd=cwd)
    except Exception as e:
        return [str(e)]


def _runtime_root(ctx: "AppContext") -> Path:
    return ctx.paths.runtime_dir.resolve()


def detect_runtime_files(ctx: "AppContext") -> None:
    rt = _runtime_root(ctx)
    zr = zapret_root(ctx)
    winws = _find_first(zr, ["winws.exe"]) if zr.exists() else None
    winws2 = _find_first(zr, ["winws2.exe"]) if zr.exists() else None
    ctx.state.runtime.installed = bool(winws)
    ctx.state.runtime.runtime_path = str(rt)
    ctx.state.runtime.winws_path = str(winws or "")
    ctx.state.runtime.winws2_path = str(winws2 or "")
    save_state(ctx.paths.state_file, ctx.state)


def uninstall_runtime(ctx: "AppContext") -> None:
    raise RuntimeError("Runtime uninstall is disabled (portable bundle ships runtime).")


def build_command(
    ctx: "AppContext",
    strategy: Strategy,
    *,
    args_override: list[str] | None = None,
    engine_override: str | None = None,
) -> list[str]:
    rt = zapret_root(ctx)
    winws = Path(ctx.state.runtime.winws_path) if ctx.state.runtime.winws_path else None
    winws2 = Path(ctx.state.runtime.winws2_path) if ctx.state.runtime.winws2_path else None

    engine = engine_override or strategy.engine

    if engine == "winws2":
        exe = winws2 or _find_first(rt, ["winws2.exe"])
        if not exe:
            raise RuntimeError("winws2.exe not found in runtime")
    else:
        exe = winws or _find_first(rt, ["winws.exe"])
        if not exe:
            raise RuntimeError("winws.exe not found in runtime")

    args = list(args_override) if args_override is not None else apply_overlays(
        strategy.args,
        discord_profile=ctx.state.zapret.discord_profile,
        games_profile=ctx.state.zapret.games_profile,
    )
    # Normalize: split multiline argv elements (escaped newline / actual newline)
    args = normalize_winws_args(args)

    fake_dir = _runtime_fake_dir(ctx)
    lists_dir = _runtime_lists_dir(ctx)

    resolved = resolve_winws_args(ctx, exe_dir=exe.parent, args=args)

    # Preflight: infer global WinDivert capture filters if missing.
    wf_args, _wf_warn, wf_err = _infer_wf_args_from_filters(resolved)
    if wf_err:
        # Bubble up to caller; start_zapret_interactive will convert to WinwsStartError.
        raise RuntimeError("; ".join(wf_err))

    # Important: --wf-* must be placed at the beginning of argv after exe.
    return [str(exe)] + wf_args + resolved


def resolve_winws_args(ctx: "AppContext", *, exe_dir: Path, args: list[str]) -> list[str]:
    fake_dir = _runtime_fake_dir(ctx)
    mgr_lists_dir = _manager_lists_dir(ctx)
    rt_lists_dir = _rt_lists_dir(ctx)
    resolved: list[str] = []
    sep = "\\" if os.name == "nt" else "/"

    # Upstream roots
    # NOTE: Some unit tests use a minimal ctx.paths SimpleNamespace without upstreams_dir.
    # In that case we still want {LISTS}/{FAKE} resolution to work.
    upstreams_dir = getattr(getattr(ctx, "paths", None), "upstreams_dir", None)
    if upstreams_dir:
        flowseal_root = (Path(str(upstreams_dir)) / "flowseal").resolve()
    else:
        flowseal_root = Path(".").resolve() / "__missing_upstreams__" / "flowseal"
    flowseal_bin = flowseal_root / "bin"
    flowseal_lists = flowseal_root / "lists"

    # Game filter placeholders occasionally appear in upstream scripts (Flowseal/StressOzz)
    # as %GameFilterTCP%/%GameFilterUDP% tokens. We must never pass them to winws.
    GAME_PORTS_UDP = "88,1024-2407,2409-4499,4502-19293,19345-49999,50101-65535"
    GAME_PORTS_TCP = "2802,2302,2502,6112-6119,6695-6710,25565,27015-27030,27036-27037,50001"

    def _clean_ports_expr(expr: str) -> str:
        parts = [p.strip() for p in (expr or "").split(",") if p.strip()]
        return ",".join(parts)

    def _resolve_game_placeholders(arg: str) -> str | None:
        # Only touch port-list options.
        port_opts = ("--wf-tcp=", "--wf-udp=", "--filter-tcp=", "--filter-udp=")
        opt = next((o for o in port_opts if arg.startswith(o)), None)
        if not opt:
            return arg

        expr = arg.split("=", 1)[1]
        # Fast path: nothing to do.
        if "%GameFilter" not in expr:
            return arg

        want_tcp = opt in ("--wf-tcp=", "--filter-tcp=")
        want_udp = opt in ("--wf-udp=", "--filter-udp=")
        game_enabled = bool(getattr(ctx.state, "zapret", None) and ctx.state.zapret.games_profile)

        # Split by commas and resolve placeholders token-by-token.
        out_items: list[str] = []
        for raw in (expr or "").split(","):
            tok = raw.strip()
            if not tok:
                continue
            if tok == "%GameFilterTCP%":
                if game_enabled and want_tcp:
                    out_items.extend(GAME_PORTS_TCP.split(","))
                # else: drop token
                continue
            if tok == "%GameFilterUDP%":
                if game_enabled and want_udp:
                    out_items.extend(GAME_PORTS_UDP.split(","))
                continue
            out_items.append(tok)

        normalized = _clean_ports_expr(",".join(out_items))
        if not normalized:
            # Entire filter becomes empty -> remove the whole option.
            return None
        return f"{opt}{normalized}"

    from app.zapret_manager.core.assets import expand_placeholders

    for a in args:
        a = a.replace("{BIN}", str(exe_dir) + sep)
        # Keep legacy Flowseal placeholders for now (Phase 3 will normalize inputs)
        a = a.replace("{FLOWSEAL_ROOT}", str(flowseal_root) + sep)
        a = a.replace("{FLOWSEAL_BIN}", str(flowseal_bin) + sep)
        a = a.replace("{FLOWSEAL_LISTS}", str(flowseal_lists) + sep)
        # Canonical placeholders via resolver (ensures {FAKE:...} picks runtime fake first)
        a = expand_placeholders(ctx, a)
        # Legacy runtime lists dir placeholder
        a = a.replace("{RT_LISTS}", str(rt_lists_dir) + sep)
        # Apply compat mapping for list file names (google.txt vs list-google.txt, etc.)
        if a.startswith("--hostlist=") or a.startswith("--hostlist-exclude=") or a.startswith("--ipset=") or a.startswith("--ipset-exclude="):
            try:
                key, val = a.split("=", 1)
                a = f"{key}={_resolve_list_path_compat(ctx, val)}"
            except Exception:
                pass
        a2 = _resolve_game_placeholders(a)
        if a2 is None:
            continue
        resolved.append(a2)
    return resolved


def dump_winws_command(cmd: list[str]) -> str:
    return "\n".join(f"[{i}] {a}" for i, a in enumerate(cmd))


def winws_log_paths(ctx: "AppContext", *, ts: str | None = None) -> WinwsLogs:
    ts = (ts or time.strftime("%Y%m%d_%H%M%S", time.localtime())).strip() or "unknown"
    ctx.paths.logs_dir.mkdir(parents=True, exist_ok=True)
    return WinwsLogs(
        stdout=(ctx.paths.logs_dir / f"winws_stdout_{ts}.log").resolve(),
        stderr=(ctx.paths.logs_dir / f"winws_stderr_{ts}.log").resolve(),
    )


def tail_text_file(path: Path, *, max_bytes: int = 8192) -> str:
    try:
        if not path.exists():
            return ""
        data = path.read_bytes()
        if len(data) > max_bytes:
            data = data[-max_bytes:]
        return data.decode("utf-8", errors="replace")
    except Exception:
        return ""


def is_pid_alive(pid: int) -> bool:
    """Windows-only: check process by PID.

    Primary: OpenProcess + GetExitCodeProcess (STILL_ACTIVE).
    Fallback: tasklist /NH /FO CSV /FI "PID eq <pid>" and check PID appears.
    """
    if pid <= 0:
        return False
    try:
        import ctypes
        from ctypes import wintypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        OpenProcess = kernel32.OpenProcess
        OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        OpenProcess.restype = wintypes.HANDLE

        GetExitCodeProcess = kernel32.GetExitCodeProcess
        GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        GetExitCodeProcess.restype = wintypes.BOOL

        CloseHandle = kernel32.CloseHandle
        CloseHandle.argtypes = [wintypes.HANDLE]
        CloseHandle.restype = wintypes.BOOL

        h = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
        if not h:
            return False
        try:
            code = wintypes.DWORD(0)
            ok = bool(GetExitCodeProcess(h, ctypes.byref(code)))
            if not ok:
                return False
            return int(code.value) == STILL_ACTIVE
        finally:
            CloseHandle(h)
    except Exception:
        pass

    try:
        r = run(["tasklist", "/NH", "/FO", "CSV", "/FI", f"PID eq {pid}"], check=False, capture=True)
        # Do not rely on localized output. CSV will include the PID as a field.
        return f",\"{pid}\"" in (r.out or "") or f"\"{pid}\"" in (r.out or "")
    except Exception:
        return False


def verify_winws_started(*, pid: int, stderr_path: Path, grace_s: float = 0.7) -> None:
    time.sleep(max(0.0, grace_s))
    if is_pid_alive(pid):
        return
    tail = tail_text_file(stderr_path)
    raise WinwsStartError(
        "winws запустился, но завершился сразу — стратегия не активна",
        exit_code=None,
        stderr_tail=tail,
    )


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1].strip()
    return s


def validate_winws_command(ctx: "AppContext", *, cmd: list[str], cwd: Path) -> list[str]:
    import re

    problems: list[str] = []
    if not cmd:
        return ["empty command"]
    for i, a in enumerate(cmd):
        if a is None or not str(a).strip():
            problems.append(f"argv[{i}] is empty")
            continue
        if "\n" in a or "\r" in a:
            problems.append(f"argv[{i}] contains newline")

    joined = "\n".join(cmd)
    # Reject any unresolved %VAR% placeholders in the final argv.
    # This catches %GameFilterTCP%/%GameFilterUDP% and any other %...% patterns.
    # Use a strict batch-variable-like matcher: %NAME%.
    if re.search(r"%[A-Za-z0-9_]+%", joined):
        problems.append("command contains unresolved %VAR% placeholder(s)")

    # --new sanity
    if cmd and cmd[-1] == "--new":
        problems.append("command ends with --new (empty block)")
    for i in range(1, len(cmd)):
        if cmd[i] == "--new" and cmd[i - 1] == "--new":
            problems.append("command contains duplicate --new --new (empty block)")

    def check_file(opt: str, val: str) -> None:
        v = _strip_quotes(val)
        if not v:
            problems.append(f"{opt} value is empty")
            return
        p = Path(v)
        if not p.is_absolute():
            p = (cwd / p).resolve()
        if not p.exists():
            problems.append(f"missing file for {opt}: {p} (cwd={cwd})")

    def check_file_warn_empty(opt: str, val: str) -> None:
        """Check that file exists; if exists but empty -> warn (non-fatal).

        Used for hostlist-exclude where empty file is allowed.
        """
        v = _strip_quotes(val)
        if not v:
            problems.append(f"{opt} value is empty")
            return
        p = Path(v)
        if not p.is_absolute():
            p = (cwd / p).resolve()
        if not p.exists():
            problems.append(f"missing file for {opt}: {p} (cwd={cwd})")
            return
        try:
            if p.is_file() and p.stat().st_size == 0:
                # WARNING encoded inside problems list (caller can render separately).
                # start_zapret_interactive() treats "WARN:" entries as non-fatal.
                problems.append(f"WARN: file for {opt} is empty: {p}")
        except Exception:
            pass

    def check_ports_opt(opt: str, val: str) -> None:
        v = _strip_quotes(val)
        if not v:
            problems.append(f"{opt} port expression is empty")
            return
        _ports, _ranges, probs = _parse_ports_expr(v)
        if probs:
            problems.append(f"invalid {opt} ports: {v} ({'; '.join(probs)})")

    def looks_like_path(v: str) -> bool:
        vv = _strip_quotes(v).strip()
        if not vv:
            return False
        # Common non-path tokens we must NOT treat as files.
        # Examples from real strategies:
        # - 0x0F0F0F0F (hex masks)
        # - none
        # - rnd,dupsid,sni=... (modifier lists)
        lower_vv = vv.lower()
        if lower_vv == "none":
            return False
        if lower_vv.startswith("0x") and len(lower_vv) > 2 and all(c in "0123456789abcdef" for c in lower_vv[2:]):
            return False
        # absolute windows path (C:\...) or any path separators
        if ":\\" in vv or "\\" in vv or "/" in vv:
            return True
        # common assets extensions
        lower = vv.lower()
        return (
            lower.endswith(".bin")
            or lower.endswith(".dat")
            or lower.endswith(".txt")
            or lower.endswith(".csv")
            or lower.endswith(".pem")
            or lower.endswith(".crt")
            or lower.endswith(".cer")
            or lower.endswith(".key")
        )

    for a in cmd[1:]:
        if a.startswith("--hostlist-domains="):
            continue
        if a.startswith("--wf-tcp="):
            check_ports_opt("--wf-tcp", a.split("=", 1)[1])
        if a.startswith("--wf-udp="):
            check_ports_opt("--wf-udp", a.split("=", 1)[1])
        if a.startswith("--filter-tcp="):
            check_ports_opt("--filter-tcp", a.split("=", 1)[1])
        if a.startswith("--filter-udp="):
            check_ports_opt("--filter-udp", a.split("=", 1)[1])
        for opt in ("--hostlist=", "--ipset=", "--ipset-exclude="):
            if a.startswith(opt):
                check_file(opt[:-1], a.split("=", 1)[1])
        if a.startswith("--hostlist-exclude="):
            # Missing exclude list is error, but empty file should not block start.
            check_file_warn_empty("--hostlist-exclude", a.split("=", 1)[1])
        # Fake/pattern arguments that point to a file.
        if "=" in a and a.startswith("--"):
            key, val = a.split("=", 1)
            key_l = key.lower()
            if val.strip().startswith("http"):
                continue
            # Avoid false positives like --dpi-desync=fake
            if key_l.startswith("--dpi-desync-fake") and looks_like_path(val):
                check_file(key, val)
            if key_l.endswith("-pattern") and looks_like_path(val):
                check_file(key, val)

    # Capture filter sanity: if per-block filters exist, global wf must exist.
    has_filter_tcp = any(a.startswith("--filter-tcp=") for a in cmd)
    has_filter_udp = any(a.startswith("--filter-udp=") for a in cmd)
    has_wf_tcp = any(a.startswith("--wf-tcp=") for a in cmd)
    has_wf_udp = any(a.startswith("--wf-udp=") for a in cmd)
    if has_filter_tcp and not has_wf_tcp:
        problems.append("missing WinDivert capture filter: add --wf-tcp=... (inferred normally)")
    if has_filter_udp and not has_wf_udp:
        problems.append("missing WinDivert capture filter: add --wf-udp=... (inferred normally)")

    return problems


def preflight_summary(ctx: "AppContext", *, cmd: list[str], cwd: Path) -> dict[str, object]:
    """Build a machine-readable preflight summary for diagnostics logs."""
    # collect wf values
    wf_tcp = next((a.split("=", 1)[1] for a in cmd if a.startswith("--wf-tcp=")), "")
    wf_udp = next((a.split("=", 1)[1] for a in cmd if a.startswith("--wf-udp=")), "")
    blocks = sum(1 for a in cmd if a == "--new")

    def _collect_files() -> list[dict[str, object]]:
        items: list[dict[str, object]] = []

        def add(kind: str, opt: str, raw: str) -> None:
            v = _strip_quotes(raw)
            p = Path(v)
            if not p.is_absolute():
                p = (cwd / p).resolve()
            exists = p.exists()
            size = None
            try:
                if exists and p.is_file():
                    size = int(p.stat().st_size)
            except Exception:
                size = None
            items.append({"kind": kind, "opt": opt, "path": str(p), "exists": exists, "size": size})

        for a in cmd[1:]:
            if a.startswith("--hostlist-domains="):
                continue
            if a.startswith("--hostlist="):
                add("list", "--hostlist", a.split("=", 1)[1])
            if a.startswith("--hostlist-exclude="):
                add("list", "--hostlist-exclude", a.split("=", 1)[1])
            if a.startswith("--ipset="):
                add("list", "--ipset", a.split("=", 1)[1])
            if a.startswith("--ipset-exclude="):
                add("list", "--ipset-exclude", a.split("=", 1)[1])
            if "=" in a and a.startswith("--"):
                k, v = a.split("=", 1)
                kl = k.lower()
                if kl.startswith("--dpi-desync-fake"):
                    add("fake", k, v)
                if kl.endswith("-pattern"):
                    add("pattern", k, v)
        return items

    return {
        "strategy": getattr(getattr(ctx, "state", None), "zapret", None).selected_strategy
        if getattr(ctx, "state", None)
        else "",
        "cwd": str(cwd),
        "wf_tcp": wf_tcp,
        "wf_udp": wf_udp,
        "new_blocks": blocks,
        "files": _collect_files(),
    }


    def start_zapret_interactive(
        ctx: "AppContext",
        strategy: Strategy,
        youtube: Strategy | None = None,
        discord: Strategy | None = None,
    ) -> list[str]:
        if not is_windows():
            raise RuntimeError("This action is Windows-only")
        if not is_admin():
            raise RuntimeError("Нужны права администратора (запусти от имени администратора).")

        require_runtime_ok(ctx)
        detect_runtime_files(ctx)
        if not ctx.state.runtime.installed:
            raise WinwsStartError(
                "Runtime not detected. Re-download/re-extract the release (expected runtime/zapret/*)."
            )

        warnings: list[str] = []

        # --- First-pass validation from strategy object itself ---
        if not strategy.is_valid:
            # Strategy is already marked invalid during load time.
            report_lines = []
            if strategy.validation_errors:
                report_lines.append("Validation errors:")
                report_lines.extend([f"- {e}" for e in strategy.validation_errors])
            if strategy.missing_assets:
                report_lines.append("Missing assets:")
                report_lines.extend([f"- {a}" for a in strategy.missing_assets])
            if strategy.unresolved_placeholders:
                report_lines.append("Unresolved placeholders:")
                report_lines.extend([f"- {p}" for p in strategy.unresolved_placeholders])
            
            report_text = "\n".join(report_lines) if report_lines else "No specific details (check logs)."
            raise WinwsStartError(f"Стратегия невалидна:\n{report_text}")


def stop_zapret(ctx: "AppContext") -> None:
    if not is_windows():
        raise RuntimeError("This action is Windows-only")
    pid = ctx.state.zapret.pid
    if not pid:
        return
    r = run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False, capture=True)
    if r.code != 0:
        # PID not found / already exited is not fatal.
        log.warning("taskkill returned code=%s err=%s", r.code, (r.err or "").strip())
        # Always clean state on taskkill error (process likely already gone)
    ctx.state.zapret.running = False
    ctx.state.zapret.pid = None
    save_state(ctx.paths.state_file, ctx.state)


def _find_first(root: Path, names: list[str]) -> Path | None:
    for name in names:
        for p in root.rglob(name):
            if p.is_file():
                return p
    return None


def _resolve_fake(ctx: "AppContext", token: str) -> str:
    """Legacy helper (deprecated).

    Placeholder expansion is now centralized in app.zapret_manager.core.assets.
    """
    return token
