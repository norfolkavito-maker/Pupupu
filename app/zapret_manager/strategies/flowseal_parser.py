from __future__ import annotations

import re
import shlex
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedCommand:
    engine: str  # winws|winws2
    args: list[str]
    raw_exe: str


_RE_COMMENT = re.compile(r"^\s*(rem\b|::)", re.IGNORECASE)
_RE_WINWS = re.compile(
    r"""(?ix)
    (?P<prefix>^|[ \t])
    (?P<exe>
        (?:
            "%[^"]+%" |
            %[^%]+% |
            "[^"]+" |
            [^\s]+
        )
    )
    (?P<rest>.*)
    """
)


def _join_caret_lines(text: str) -> list[str]:
    lines = text.splitlines()
    out: list[str] = []
    buf = ""
    for ln in lines:
        ln = ln.rstrip()
        if not ln:
            if buf:
                out.append(buf)
                buf = ""
            continue
        if ln.endswith("^"):
            buf += ln[:-1]
            continue
        if buf:
            out.append(buf + ln)
            buf = ""
        else:
            out.append(ln)
    if buf:
        out.append(buf)
    return out


def _unescape_carets(s: str) -> str:
    # Batch escaping: ^X -> X (best-effort for argument parsing).
    out = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "^" and i + 1 < len(s):
            out.append(s[i + 1])
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _looks_like_winws(exe_token: str) -> str | None:
    t = exe_token.strip().strip('"').lower()
    if "winws2.exe" in t or t.endswith("winws2.exe"):
        return "winws2"
    if "winws.exe" in t or t.endswith("winws.exe"):
        return "winws"
    return None


def extract_winws_command(bat_text: str) -> ParsedCommand | None:
    for line in _join_caret_lines(bat_text):
        if _RE_COMMENT.match(line):
            continue
        if "winws" not in line.lower():
            continue

        line = _unescape_carets(line)
        stripped = line.strip()
        try:
            parts = shlex.split(stripped, posix=False)
        except ValueError:
            parts = [a for a in stripped.split(" ") if a]

        if not parts:
            continue

        lowered = [p.strip().strip('"').lower() for p in parts]
        try:
            idx = next(i for i, p in enumerate(lowered) if "winws.exe" in p or "winws2.exe" in p)
        except StopIteration:
            m = _RE_WINWS.search(line)
            if not m:
                continue
            exe = m.group("exe").strip()
            rest = m.group("rest").strip()
            try:
                args = shlex.split(rest, posix=False)
            except ValueError:
                args = [a for a in rest.split(" ") if a]
        else:
            exe = parts[idx]
            args = parts[idx + 1 :]

        engine = _looks_like_winws(exe)
        if not engine:
            continue

        # Normalize placeholders commonly used by Flowseal
        args2: list[str] = []
        for a in args:
            a = a.replace("%BIN%", "{BIN}")
            a = a.replace("%LISTS%", "{LISTS}")
            a = a.replace("%~dp0", "{UPSTREAM_ROOT}\\")
            args2.append(a)

        return ParsedCommand(engine=engine, args=args2, raw_exe=exe)
    return None

