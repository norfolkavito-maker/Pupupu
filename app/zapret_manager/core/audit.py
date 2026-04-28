from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass(frozen=True)
class AuditEvent:
    category: str
    action_id: str
    ok: bool
    message: str = ""
    payload: Any = None


def append_audit(log_file: Path, ev: AuditEvent) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": _utc_iso(),
        "category": ev.category,
        "action_id": ev.action_id,
        "ok": bool(ev.ok),
        "message": ev.message,
        "payload": ev.payload,
    }
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
