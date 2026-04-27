from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from app.zapret_manager.core.app_context import AppContext


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RepairItem:
    name: str
    status: str  # OK|CREATED|COPIED|MISSING
    details: str = ""


def _repo_builtin_lists_dir() -> Path:
    # We ship a minimal set of lists in repo under data/lists.
    return (Path(__file__).resolve().parents[3] / "data" / "lists").resolve()


def ensure_base_lists(ctx: AppContext) -> list[RepairItem]:
    """Ensure minimal list assets exist in canonical manager lists dir.

    - Creates DedZapretData/data/lists
    - Copies base lists from repo (if present in this build)
    - Does NOT download from network (safe for unit tests)
    """
    out: list[RepairItem] = []
    target = ctx.paths.lists_dir.resolve()
    if not target.exists():
        target.mkdir(parents=True, exist_ok=True)
        out.append(RepairItem("lists_dir", "CREATED", str(target)))
    else:
        out.append(RepairItem("lists_dir", "OK", str(target)))

    src_dir = _repo_builtin_lists_dir()
    base_names = [
        # builtin strategies use these (at least)
        "google.txt",
        "exclude.txt",
        # optional but used by overlays
        "rkn.txt",
    ]

    for name in base_names:
        dest = (target / name).resolve()
        if dest.exists() and dest.stat().st_size > 0:
            out.append(RepairItem(name, "OK", str(dest)))
            continue

        # Try to copy from repo assets (dev/source builds).
        candidates = [
            src_dir / name,
            src_dir / f"list-{name}",
        ]
        copied = False
        for c in candidates:
            if c.exists() and c.is_file() and c.stat().st_size > 0:
                dest.write_bytes(c.read_bytes())
                out.append(RepairItem(name, "COPIED", f"{c} -> {dest}"))
                copied = True
                break
        if copied:
            continue

        out.append(RepairItem(name, "MISSING", f"not found in {target} and no bundled source to copy"))

    return out
