from __future__ import annotations

"""Color constants used by UI.

We keep all UI colors in a single place so a missing constant never crashes the
application.

If colorama is unavailable (shouldn't happen in bundled builds), we gracefully
fall back to empty strings.
"""

try:
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

except Exception:  # pragma: no cover

    class C:
        GREEN = ""
        RED = ""
        CYAN = ""
        YELLOW = ""
        MAGENTA = ""
        BLUE = ""
        DIM = ""
        RESET = ""
