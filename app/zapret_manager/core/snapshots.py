from __future__ import annotations

import shutil
import time
from pathlib import Path


def _ts_dir() -> str:
    return time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())


def create_snapshot(
    *,
    snapshots_root: Path,
    reason: str,
    paths: list[Path],
) -> Path:
    """Create a pre-change snapshot by copying selected paths.

    This is best-effort: missing files are ignored.
    """
    safe_reason = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in (reason or "snapshot"))
    out = (snapshots_root / f"{_ts_dir()}_{safe_reason}").resolve()
    out.mkdir(parents=True, exist_ok=True)
    for p in paths:
        try:
            if not p.exists():
                continue
            dst = out / p.name
            if p.is_dir():
                shutil.copytree(p, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(p, dst)
        except Exception:
            continue
    return out
