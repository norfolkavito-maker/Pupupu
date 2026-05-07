
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import os
import json
import time

from app.zapret_manager.core.atomic_write import (
    atomic_write_text,
    atomic_write_json,
    backup_file,
)


@pytest.fixture
def temp_file(tmp_path):
    file_path = tmp_path / "test_file.txt"
    yield file_path


@pytest.fixture
def temp_json_file(tmp_path):
    file_path = tmp_path / "test_json_file.json"
    yield file_path


@pytest.fixture
def temp_backup_dir(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    yield backup_dir


def test_atomic_write_text_success(temp_file):
    content = "Hello, atomic world!"
    atomic_write_text(temp_file, content)
    assert temp_file.read_text() == content
    assert not any(f.suffix == ".tmp" for f in temp_file.parent.iterdir())


def test_atomic_write_text_creates_parent_dirs(tmp_path):
    nested_path = tmp_path / "sub" / "sub2" / "test.txt"
    content = "Nested content"
    atomic_write_text(nested_path, content)
    assert nested_path.read_text() == content
    assert nested_path.parent.is_dir()


def test_atomic_write_text_failure_cleans_up_temp_file(temp_file):
    content = "Failing write"
    
    with patch("os.fsync", side_effect=OSError("Disk full")):
        with pytest.raises(RuntimeError):
            atomic_write_text(temp_file, content)
    
    assert not temp_file.exists()
    assert not any(f.suffix == ".tmp" for f in temp_file.parent.iterdir())


def test_atomic_write_json_success(temp_json_file):
    data = {"key": "value", "number": 123}
    atomic_write_json(temp_json_file, data)
    read_data = json.loads(temp_json_file.read_text())
    assert read_data == data
    assert not any(f.suffix == ".tmp" for f in temp_json_file.parent.iterdir())


def test_backup_file_creates_backup(temp_file, temp_backup_dir):
    original_content = "Original file content."
    temp_file.write_text(original_content)

    # Introduce a slight delay to ensure distinct timestamps for backup files
    time.sleep(0.01)

    backup_path = backup_file(temp_file, temp_backup_dir)

    assert backup_path is not None
    assert backup_path.is_file()
    assert backup_path.read_text() == original_content
    assert backup_path.parent == temp_backup_dir
    assert temp_file.exists()


def test_backup_file_with_reason(temp_file, temp_backup_dir):
    original_content = "Content for reason backup."
    temp_file.write_text(original_content)

    time.sleep(0.01)

    reason = "pre_update"
    backup_path = backup_file(temp_file, temp_backup_dir, reason=reason)

    assert backup_path is not None
    assert reason in backup_path.name
    assert backup_path.is_file()
    assert backup_path.read_text() == original_content


def test_backup_file_non_existent_file(temp_backup_dir):
    non_existent_file = temp_backup_dir / "non_existent.txt"
    backup_path = backup_file(non_existent_file, temp_backup_dir)
    assert backup_path is None
    assert not temp_backup_dir.joinpath(f"{non_existent_file.name}.*.bak").exists()


def test_backup_file_preserves_metadata(tmp_path, temp_backup_dir):
    original_file = tmp_path / "original.txt"
    original_file.write_text("test data")
    os.chmod(original_file, 0o755)  # Set some permissions
    original_stat = original_file.stat()

    time.sleep(0.01)

    backup_path = backup_file(original_file, temp_backup_dir)
    assert backup_path is not None

    backup_stat = backup_path.stat()
    assert backup_stat.st_mode & 0o777 == original_stat.st_mode & 0o777
    assert backup_stat.st_size == original_stat.st_size
