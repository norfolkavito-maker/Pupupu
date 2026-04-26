from __future__ import annotations

import os
import sys

from app.zapret_manager.core.diagnostics import diag_log



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

