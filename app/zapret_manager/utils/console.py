from __future__ import annotations

import os
import sys

from app.zapret_manager.core.diagnostics import diag_log
from app.zapret_manager.ui.colors import C

# Backward-compatible alias for older UI code / bundled builds.
# Some modules historically imported `c` (lowercase) as a color holder.
c = C



def clear() -> None:
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def pause(prompt: str = "Нажмите Enter...") -> None:
    try:
        diag_log("ui.pause", "console", {"prompt": prompt})
        input(prompt)
    except EOFError:
        return


def ask(prompt: str) -> str:
    try:
        diag_log("ui.prompt", "console", {"prompt": prompt})
        ans = input(prompt)
        diag_log("ui.input", "console", {"prompt": prompt, "answer": ans})
        return ans
    except EOFError:
        return ""


def print_err(msg: str) -> None:
    sys.stderr.write(msg + "\n")

