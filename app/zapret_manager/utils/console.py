from __future__ import annotations

import os
import sys

from colorama import Fore, Style, init as colorama_init


colorama_init()


class C:
    GREEN = Fore.LIGHTGREEN_EX
    RED = Fore.LIGHTRED_EX
    CYAN = Fore.LIGHTCYAN_EX
    YELLOW = Fore.LIGHTYELLOW_EX
    MAGENTA = Fore.LIGHTMAGENTA_EX
    BLUE = Fore.LIGHTBLUE_EX
    DIM = Style.DIM
    RESET = Style.RESET_ALL


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

