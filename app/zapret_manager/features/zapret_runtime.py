from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from zapret_manager.core.app_context import AppContext
from zapret_manager.core.state import save_state
from zapret_manager.strategies.composer import compose
from zapret_manager.strategies.model import Strategy
from zapret_manager.strategies.overlays import apply_overlays
from zapret_manager.utils.platform import is_admin, is_windows
from zapret_manager.utils.subprocessx import popen_detached, run


log = logging.getLogger(__name__)


def runtime_health(ctx: AppContext) -> dict[str, object]:
    """Checks that bundled runtime exists and has required files.

    This project is designed to ship runtime *bundled* (portable). If runtime is
    missing, user should re-download/re-extract the release.
    """
    rt = _runtime_root(ctx)
    # common root for zapret-win-bundle layout is runtime/zapret
    # but we search for exe recursively to be robust.
    winws = _find_first(rt, ["winws.exe"])
    winws2 = _find_first(rt, ["winws2.exe"])
    windivert_dll = (rt / "WinDivert.dll")
    windivert_sys = (rt / "WinDivert64.sys")
    blockcheck_cmd = _find_first(rt, ["blockcheck.cmd"])
    fake_dir = Path(ctx.config.paths.fake_files_dir)

    ok = True
    problems: list[str] = []

    if not rt.exists():
        ok = False
        problems.append(f"runtime dir not found: {rt}")
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
        # Not critical for bypass itself, but useful.
        problems.append("blockcheck.cmd not found")
    if not fake_dir.exists():
        problems.append(f"fake files dir not found: {fake_dir}")

    return {
        "ok": ok,
        "runtime_dir": str(rt),
        "winws": str(winws) if winws else "",
        "winws2": str(winws2) if winws2 else "",
        "problems": problems,
    }


def require_runtime_ok(ctx: AppContext) -> None:
    h = runtime_health(ctx)
    if bool(h.get("ok")):
        return
    problems = h.get("problems") or []
    msg = "Bundled runtime is missing or broken. Re-download/re-extract the release."
    if problems:
        msg += "\nProblems:\n- " + "\n- ".join(str(x) for x in problems)
    raise RuntimeError(msg)


def _runtime_root(ctx: AppContext) -> Path:
    # runtime_dir from config is relative to root
    return (ctx.root / ctx.config.zapret.runtime_dir).resolve()


def detect_runtime_files(ctx: AppContext) -> None:
    rt = _runtime_root(ctx)
    winws = _find_first(rt, ["winws.exe"])
    winws2 = _find_first(rt, ["winws2.exe"])
    ctx.state.runtime.installed = bool(winws)
    ctx.state.runtime.runtime_path = str(rt)
    ctx.state.runtime.winws_path = str(winws or "")
    ctx.state.runtime.winws2_path = str(winws2 or "")
    save_state(ctx.paths.state_file, ctx.state)


def uninstall_runtime(ctx: AppContext) -> None:
    """Not used in portable mode.

    Runtime is bundled with release. We deliberately do not provide UI actions
    that delete it.
    """
    raise RuntimeError("Runtime uninstall is disabled (portable bundle ships runtime).")


def build_command(
    ctx: AppContext,
    strategy: Strategy,
    *,
    args_override: list[str] | None = None,
    engine_override: str | None = None,
) -> list[str]:
    rt = _runtime_root(ctx)
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

    resolved: list[str] = []
    for a in args:
        a = a.replace("{BIN}", str(exe.parent) + "\\")
        # {LISTS} -> runtime-provided lists (usually runtime/zapret/lists)
        a = a.replace("{LISTS}", str(Path(ctx.config.paths.lists_dir).resolve()) + "\\")
        # {MGR_LISTS} -> manager-owned lists (data/lists)
        a = a.replace("{MGR_LISTS}", str(ctx.paths.lists_dir.resolve()) + "\\")
        # Support both {FAKE:filename.bin} and legacy {FAKE} prefix.
        a = a.replace("{FAKE}", str(Path(ctx.config.paths.fake_files_dir).resolve()) + "\\")
        a = _resolve_fake(ctx, a)
        resolved.append(a)
    return [str(exe)] + resolved


def start_zapret_interactive(
    ctx: AppContext,
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
    p = popen_detached(cmd, cwd=str(_runtime_root(ctx)))
    ctx.state.zapret.running = True
    ctx.state.zapret.mode = "interactive"
    ctx.state.zapret.pid = int(p.pid)
    ctx.state.zapret.selected_strategy = strategy.name
    save_state(ctx.paths.state_file, ctx.state)
    return warnings


def stop_zapret(ctx: AppContext) -> None:
    if not is_windows():
        raise RuntimeError("This action is Windows-only")
    pid = ctx.state.zapret.pid
    if not pid:
        return
    run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False, capture=True)
    ctx.state.zapret.running = False
    ctx.state.zapret.pid = None
    save_state(ctx.paths.state_file, ctx.state)


def _find_first(root: Path, names: list[str]) -> Path | None:
    for name in names:
        for p in root.rglob(name):
            if p.is_file():
                return p
    return None


def _resolve_fake(ctx: AppContext, token: str) -> str:
    # token may include {FAKE:filename.bin}
    if "{FAKE:" not in token:
        return token
    rt = _runtime_root(ctx)
    import re

    def repl(m: re.Match[str]) -> str:
        fname = m.group(1)
        found = _find_first(rt, [fname])
        return str(found) if found else fname

    return re.sub(r"\{FAKE:([^}]+)\}", repl, token)