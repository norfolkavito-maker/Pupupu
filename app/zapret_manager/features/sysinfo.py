from __future__ import annotations

import platform

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.features.zapret_runtime import detect_runtime_files
from app.zapret_manager.utils.platform import is_windows
from app.zapret_manager.utils.subprocessx import run


def system_info_text(ctx: AppContext) -> str:
    detect_runtime_files(ctx)
    lines: list[str] = []
    lines.append(f"OS: {platform.platform()}")
    lines.append(f"Python: {platform.python_version()}")
    lines.append(f"Root: {ctx.root}")
    lines.append(f"Runtime installed: {ctx.state.runtime.installed}")
    lines.append(f"winws: {ctx.state.runtime.winws_path}")
    lines.append(f"winws2: {ctx.state.runtime.winws2_path}")
    lines.append("")
    lines.append("Zapret selection:")
    lines.append(f"- base: {ctx.state.zapret.base_strategy or '-'}")
    lines.append(f"- youtube: {ctx.state.zapret.youtube_layer or '-'}")
    lines.append(f"- discord: {ctx.state.zapret.discord_layer or '-'}")
    lines.append(f"- discord script: {ctx.state.zapret.discord_script or '-'}")
    lines.append(f"- games: {ctx.state.zapret.games_profile or '-'}")
    lines.append(f"- rkn: {ctx.state.zapret.rkn_enabled}")
    lines.append(f"- wssize: {ctx.state.zapret.wssize_enabled}")
    lines.append("")

    if is_windows():
        ip = run(["ipconfig"], check=False, capture=True)
        lines.append("ipconfig:")
        lines.append(ip.out.strip())
    return "\n".join(lines).strip() + "\n"

