from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.state import save_state
from app.zapret_manager.strategies.composer import compose
from app.zapret_manager.strategies.model import Strategy
from app.zapret_manager.strategies.overlays import apply_overlays
from app.zapret_manager.utils.platform import is_admin, is_windows
from app.zapret_manager.utils.subprocessx import popen_detached, run


log = logging.getLogger(__name__)


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


def runtime_health(ctx: "AppContext") -> dict[str, object]:
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
    lists_dir = _runtime_lists_dir(ctx)

    ok = True
    problems: list[str] = []

    if not rt.exists():
        ok = False
        problems.append(f"runtime dir not found: {rt}")
    if not zr.exists():
        ok = False
        problems.append(f"zapret dir not found: {zr}")
    if not winws:
        ok = False
        problems.append("winws.exe not found")
    if not windivert_dll.exists():
        ok = False
        problems.append("WinDivert.dll not found")
    if not windivert_sys.exists():
        ok = False
        problems.append("WinDivert64.sys not found")
    if not blockcheck_cmd:
        problems.append("blockcheck.cmd not found")
    if not fake_dir.exists():
        problems.append(f"fake files dir not found: {fake_dir}")
    if not lists_dir.exists():
        problems.append(f"lists dir not found: {lists_dir}")

    return {
        "ok": ok,
        "runtime_dir": str(rt),
        "zapret_dir": str(zr),
        "winws": str(winws) if winws else "",
        "winws2": str(winws2) if winws2 else "",
        "windivert_dll": str(windivert_dll),
        "windivert_sys": str(windivert_sys),
        "fake_dir": str(fake_dir),
        "lists_dir": str(lists_dir),
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
    lines.append(f"winws.exe:        {winws} ({okflag(winws)})")
    wdd = Path(str(h.get("windivert_dll") or (zr / 'WinDivert.dll')))
    wds = Path(str(h.get("windivert_sys") or (zr / 'WinDivert64.sys')))
    lines.append(f"WinDivert.dll:    {wdd} ({okflag(wdd)})")
    lines.append(f"WinDivert64.sys:  {wds} ({okflag(wds)})")
    fake_dir = Path(str(h.get("fake_dir") or _runtime_fake_dir(ctx)))
    lists_dir = Path(str(h.get("lists_dir") or _runtime_lists_dir(ctx)))
    lines.append(f"fake dir:         {fake_dir} ({okflag(fake_dir)})")
    lines.append(f"lists dir:        {lists_dir} ({okflag(lists_dir)})")
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

    fake_dir = _runtime_fake_dir(ctx)
    lists_dir = _runtime_lists_dir(ctx)

    resolved = resolve_winws_args(ctx, exe_dir=exe.parent, args=args)
    return [str(exe)] + resolved


def resolve_winws_args(ctx: "AppContext", *, exe_dir: Path, args: list[str]) -> list[str]:
    fake_dir = _runtime_fake_dir(ctx)
    lists_dir = _runtime_lists_dir(ctx)
    resolved: list[str] = []
    for a in args:
        a = a.replace("{BIN}", str(exe_dir) + "\\")
        a = a.replace("{LISTS}", str(lists_dir.resolve()) + "\\")
        a = a.replace("{MGR_LISTS}", str(ctx.paths.lists_dir.resolve()) + "\\")
        a = a.replace("{FAKE}", str(fake_dir.resolve()) + "\\")
        a = _resolve_fake(ctx, a)
        resolved.append(a)
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

    def check_file(opt: str, val: str) -> None:
        v = _strip_quotes(val)
        if not v:
            problems.append(f"{opt} value is empty")
            return
        p = Path(v)
        if not p.is_absolute():
            p = (cwd / p).resolve()
        if not p.exists():
            problems.append(f"missing file for {opt}: {p}")

    def looks_like_path(v: str) -> bool:
        vv = _strip_quotes(v).strip()
        if not vv:
            return False
        # absolute windows path (C:\...) or any path separators
        if ":\\" in vv or "\\" in vv or "/" in vv:
            return True
        # common assets extensions
        lower = vv.lower()
        return lower.endswith(".bin") or lower.endswith(".dat") or lower.endswith(".txt") or lower.endswith(".csv")

    for a in cmd[1:]:
        if a.startswith("--hostlist-domains="):
            continue
        for opt in ("--hostlist=", "--ipset=", "--ipset-exclude="):
            if a.startswith(opt):
                check_file(opt[:-1], a.split("=", 1)[1])
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

    return problems


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
        raise RuntimeError(
            "Runtime not detected. Re-download/re-extract the release (expected runtime/zapret/*)."
        )

    warnings: list[str] = []
    args_override: list[str] | None = None
    engine_override: str | None = None
    if (
        youtube
        or discord
        or ctx.state.zapret.discord_script
        or ctx.state.zapret.games_profile
        or ctx.state.zapret.rkn_enabled
        or ctx.state.zapret.wssize_enabled
    ):
        composed = compose(
            base=strategy,
            youtube=youtube,
            discord=discord,
            discord_script=ctx.state.zapret.discord_script,
            games_profile=ctx.state.zapret.games_profile,
            rkn_enabled=ctx.state.zapret.rkn_enabled,
            wssize_enabled=ctx.state.zapret.wssize_enabled,
        )
        args_override = composed.args
        engine_override = composed.engine
        warnings = list(composed.warnings)

    cmd = build_command(ctx, strategy, args_override=args_override, engine_override=engine_override)

    # Log final argv for diagnostics.
    log.info("winws command (argv):\n%s", dump_winws_command(cmd))

    # Validate BEFORE start.
    cwd = zapret_root(ctx)
    problems = validate_winws_command(ctx, cmd=cmd, cwd=cwd)
    if problems:
        raise WinwsStartError("winws command is invalid:\n- " + "\n- ".join(problems))

    logs = winws_log_paths(ctx)
    p = popen_detached(cmd, cwd=str(cwd), stdout_path=logs.stdout, stderr_path=logs.stderr)

    try:
        verify_winws_started(pid=int(p.pid), stderr_path=logs.stderr, grace_s=0.7)
    except WinwsStartError as e:
        # do not mark zapret running
        tail = e.stderr_tail or tail_text_file(logs.stderr)
        msg = str(e)
        if tail.strip():
            msg += "\n\n--- winws stderr (tail) ---\n" + tail.strip() + "\n--- end ---"
        raise WinwsStartError(msg, exit_code=e.exit_code, stderr_tail=tail)

    ctx.state.zapret.running = True
    ctx.state.zapret.mode = "interactive"
    ctx.state.zapret.pid = int(p.pid)
    ctx.state.zapret.selected_strategy = strategy.name
    save_state(ctx.paths.state_file, ctx.state)
    return warnings


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
    if "{FAKE:" not in token:
        return token
    rt = _runtime_root(ctx)
    import re

    def repl(m: re.Match[str]) -> str:
        fname = m.group(1)
        found = _find_first(rt, [fname])
        return str(found) if found else fname

    return re.sub(r"\{FAKE:([^}]+)\}", repl, token)
