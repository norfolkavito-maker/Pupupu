from __future__ import annotations

from pathlib import Path

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.features.zapret_runtime import stop_zapret
from app.zapret_manager.utils.platform import is_windows
from app.zapret_manager.utils.subprocessx import run


def _blockcheck_dir(ctx: AppContext) -> Path:
    return (ctx.paths.runtime_dir / "zapret" / "blockcheck").resolve()


def run_blockcheck(ctx: AppContext, *, variant: str = "1") -> None:
    if not is_windows():
        raise RuntimeError("Windows-only")
    stop_zapret(ctx)
    d = _blockcheck_dir(ctx)
    if not d.exists():
        raise RuntimeError(
            "blockcheck directory not found in runtime. "
            "Bundled runtime is missing. Re-download/re-extract the release."
        )

    script = d / ("blockcheck2.cmd" if variant == "2" else "blockcheck.cmd")
    if not script.exists():
        raise RuntimeError(f"{script.name} not found in runtime.")

    # Open in a new console window and wait.
    run(["cmd", "/c", "start", "\"\"", "/wait", str(script)], check=False, capture=True, cwd=str(d))

