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


def safe_print(*args: object, sep: str = " ", end: str = "\n", file=None, flush: bool = False) -> None:
    """Encoding-safe print.

    On Windows CI consoles stdout encoding may be cp1252/cp866 and can raise
    UnicodeEncodeError for Cyrillic text. We fall back to a best-effort write
    with replacement characters.
    """
    if file is None:
        file = sys.stdout
    try:
        print(*args, sep=sep, end=end, file=file, flush=flush)
    except UnicodeEncodeError:
        try:
            text = sep.join("" if a is None else str(a) for a in args) + end
            enc = getattr(file, "encoding", None) or sys.getdefaultencoding() or "utf-8"
            data = text.encode(enc, errors="replace")
            # If the target is a text stream with buffer, write bytes into buffer.
            buf = getattr(file, "buffer", None)
            if buf is not None:
                buf.write(data)
            else:
                file.write(data.decode(enc, errors="replace"))
            if flush:
                try:
                    file.flush()
                except Exception:
                    pass
        except Exception as e:
            # Last resort: write to stderr without raising.
            try:
                sys.stderr.write(f"[safe_print failed] {e}\n")
            except Exception:
                pass

