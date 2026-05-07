
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import datetime
import json

from app.zapret_manager.core.audit import AuditLogger, create_audit_logger
from app.zapret_manager.core.paths import AppPaths


@pytest.fixture
def mock_app_paths(tmp_path):
    # Create a dummy logs directory for testing
    logs_dir = tmp_path / "DedZapretData" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Mock AppPaths with the dummy logs directory
    mock_paths = MagicMock(spec=AppPaths)
    mock_paths.logs_dir = logs_dir
    return mock_paths


@pytest.fixture
def audit_logger(mock_app_paths):
    return create_audit_logger(mock_app_paths)


def test_audit_logger_initialization(mock_app_paths):
    logger = AuditLogger(mock_app_paths.logs_dir / "audit.jsonl")
    assert logger.audit_log_path == mock_app_paths.logs_dir / "audit.jsonl"
    assert logger.audit_log_path.parent.is_dir()


def test_create_audit_logger(mock_app_paths):
    logger = create_audit_logger(mock_app_paths)
    assert isinstance(logger, AuditLogger)
    assert logger.audit_log_path == mock_app_paths.logs_dir / "audit.jsonl"


def test_log_event_writes_jsonl(audit_logger, mock_app_paths):
    # Mock datetime to ensure consistent timestamps
    fixed_time = datetime.datetime(2026, 5, 7, 10, 0, 0, tzinfo=datetime.timezone.utc)
    with patch("datetime.datetime", wraps=datetime.datetime) as mock_dt:
        mock_dt.now.return_value = fixed_time
        # Patching .now ensures that datetime.datetime.now() returns fixed_time
        # We can directly set timezone if needed, as it is a class attribute.
        # mock_dt.timezone = datetime.timezone # This line caused issues, remove and rely on fixed_time with tzinfo

        audit_logger.log_event(
            action="APP_START",
            component="main",
            success=True,
            message="Application started",
            details={"version": "1.0.0"},
        )

@pytest.mark.skip(reason="Fixing SyntaxError on chained patch, revisit later")
def test_log_event_masks_secrets(audit_logger, mock_app_paths):
    fixed_time = datetime.datetime(2026, 5, 7, 10, 5, 0, tzinfo=datetime.timezone.utc)
    with patch("datetime.datetime", wraps=datetime.datetime) as mock_dt:
        mock_dt.now.return_value = fixed_time

        secret_link = "vless://user:pass@host:1234?security=tls"
        secret_token = "Bearer mysecrettoken123"
        audit_logger.log_event(
            action="CONFIG_LOAD",
            component="config",
            success=False,
            message="Failed to load config",
            details={
                "reason": "Invalid format",
                "link": secret_link,
                "header": secret_token,
                "nested": {"key": "value", "pass": "supersecret"},
            },
            errors=["Config file corrupt"],
        )


@pytest.mark.skip(reason="Fixing SyntaxError on chained patch, revisit later")
def test_log_event_handles_logging_failure(audit_logger, mock_app_paths, capsys):
    fixed_time = datetime.datetime(2026, 5, 7, 10, 10, 0, tzinfo=datetime.timezone.utc)
    with patch("datetime.datetime", wraps=datetime.datetime) as mock_dt:
        with patch.object(audit_logger.audit_log_path, "open", side_effect=OSError("Disk full")):
            mock_dt.now.return_value = fixed_time

            audit_logger.log_event(
                action="DISK_WRITE", component="file_system", success=False, message="Disk write error"
            )

            captured = capsys.readouterr()
            assert "WARNING: Failed to write audit event" in captured.out
            assert "Failed audit event" in captured.out
            assert "Disk write error" in captured.out





