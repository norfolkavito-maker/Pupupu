
import os
import json
import shutil
from pathlib import Path
from typing import Any, Optional
import stat
import datetime


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """Writes text to a file atomically, ensuring data integrity."""
    temp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        # Ensure parent directories exist for the temporary file
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        # Write to a temporary file and ensure all data is flushed to disk
        with open(temp_path, "w", encoding=encoding) as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        # Replace the original file with the temporary file atomically
        temp_path.replace(path)
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()  # Clean up temp file on error
        raise RuntimeError(f"Atomic write to {path} failed: {e}") from e


def atomic_write_json(path: Path, data: Any, encoding: str = "utf-8") -> None:
    """Writes JSON data to a file atomically, ensuring data integrity."""
    json_text = json.dumps(data, indent=4, ensure_ascii=False)
    atomic_write_text(path, json_text, encoding=encoding)


def backup_file(path: Path, backup_dir: Path, reason: str = "") -> Optional[Path]:
    """Creates a timestamped backup of a file."""
    if not path.is_file():
        return None

    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    backup_filename = f"{path.name}.{timestamp}.bak"
    if reason:
        backup_filename = f"{path.name}.{reason}.{timestamp}.bak"
    backup_path = backup_dir / backup_filename

    try:
        shutil.copy2(path, backup_path) # copy2 preserves metadata
        return backup_path
    except Exception as e:
        # TODO: Log this error using the audit logger when it's implemented
        print(f"Warning: Failed to create backup of {path} to {backup_path}: {e}")
        return None
