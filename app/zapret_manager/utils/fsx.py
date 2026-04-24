from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from pathlib import Path


def ensure_empty_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def atomic_replace_dir(src: Path, dst: Path) -> None:
    """Replaces *dst* with *src* and rolls back on failure."""
    if not src.exists():
        raise FileNotFoundError(src)

    dst_parent = dst.parent
    dst_parent.mkdir(parents=True, exist_ok=True)

    rollback_root = Path(tempfile.mkdtemp(prefix="zapret_old_"))
    tmp_old = rollback_root / dst.name
    moved_old = False
    try:
        if dst.exists():
            shutil.move(str(dst), str(tmp_old))
            moved_old = True

        shutil.move(str(src), str(dst))

        if moved_old and tmp_old.exists():
            shutil.rmtree(tmp_old, ignore_errors=True)
    except Exception:
        if moved_old and tmp_old.exists() and not dst.exists():
            shutil.move(str(tmp_old), str(dst))
        raise
    finally:
        shutil.rmtree(rollback_root, ignore_errors=True)


def copytree_overwrite(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def safe_extract_zip(zf: zipfile.ZipFile, dest: Path) -> None:
    """Safely extracts zip members, preventing path traversal."""
    dest = dest.resolve()
    for member in zf.infolist():
        member_name = member.filename
        if not member_name or member_name.endswith("/"):
            continue
        target = (dest / member_name).resolve()
        if not str(target).startswith(str(dest) + os.sep):
            raise RuntimeError(f"Unsafe archive entry: {member_name}")
    zf.extractall(dest)

