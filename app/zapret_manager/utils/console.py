from __future__ import annotations

import os
import sys

from zapret_manager.ui.colors import C


def clear() -> None:
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def pause(prompt: str = "Нажмите Enter...") -> None:
    try:
        input(prompt)
    except EOFError:
        return


def ask(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        return ""


def print_err(msg: str) -> None:
    sys.stderr.write(msg + "\n")

