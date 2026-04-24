from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ImportedHostsBlock:
    key: str
    title: str
    lines: list[str]

    def to_json(self) -> dict[str, Any]:
        return {"key": self.key, "title": self.title, "lines": self.lines}


def _extract_var(script: str, name: str) -> str | None:
    # NAME="...."
    m = re.search(rf'(?s)\b{name}\s*=\s*"([^"]*)"', script)
    if m:
        return m.group(1)
    m = re.search(rf"(?s)\b{name}\s*=\s*'([^']*)'", script)
    if m:
        return m.group(1)
    return None


def _decode_body(body: str) -> list[str]:
    body = body.replace("\\n", "\n")
    lines = []
    for ln in body.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        if ln.startswith("#"):
            continue
        # collapse multiple spaces
        ln = re.sub(r"\s+", " ", ln)
        lines.append(ln)
    return lines


def import_hosts_blocks_from_stressozz_script(script_text: str, *, out_file: Path) -> list[ImportedHostsBlock]:
    mapping = [
        ("NALOG", "nalog.ru"),
        ("RUTOR", "rutor.info"),
        ("NTC", "ntc.party"),
        ("INSTAGRAM", "Instagram & Facebook"),
        ("LIBRUSEC", "lib.rus.ec"),
        ("AI", "AI сервисы"),
        ("TWCH", "Twitch"),
        ("TGWeb", "Telegram Web"),
        ("SPFY", "Spotify"),
        ("SCell", "Supercell"),
    ]
    blocks: list[ImportedHostsBlock] = []
    for var, title in mapping:
        body = _extract_var(script_text, var)
        if not body:
            continue
        blocks.append(ImportedHostsBlock(key=var, title=title, lines=_decode_body(body)))

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(
        json.dumps({"blocks": [b.to_json() for b in blocks]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return blocks

