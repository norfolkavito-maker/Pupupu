from __future__ import annotations

import sys

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.ui.main_menu import run_main_menu


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    ctx = AppContext.bootstrap(argv=argv)
    return run_main_menu(ctx)

