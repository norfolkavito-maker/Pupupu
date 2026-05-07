
import pytest

from app.zapret_manager.core.errors import (
    DedZapretError,
    ConfigError,
    StateError,
    SecurityError,
    SafeExtractError,
    ProcessExecutionError,
    AdminRequiredError,
)


def test_dedzapret_error_base_exception():
    with pytest.raises(DedZapretError, match="Base DedZapret error"):
        raise DedZapretError("Base DedZapret error")


def test_config_error_inherits_dedzapret_error():
    with pytest.raises(ConfigError, match="Config error"):
        raise ConfigError("Config error")
    with pytest.raises(DedZapretError):
        raise ConfigError("Config error")


def test_state_error_inherits_dedzapret_error():
    with pytest.raises(StateError, match="State error"):
        raise StateError("State error")
    with pytest.raises(DedZapretError):
        raise StateError("State error")


def test_security_error_inherits_dedzapret_error():
    with pytest.raises(SecurityError, match="Security issue"):
        raise SecurityError("Security issue")
    with pytest.raises(DedZapretError):
        raise SecurityError("Security issue")


def test_safe_extract_error_inherits_security_error():
    with pytest.raises(SafeExtractError, match="Extraction failed"):
        raise SafeExtractError("Extraction failed")
    with pytest.raises(SecurityError):
        raise SafeExtractError("Extraction failed")
    with pytest.raises(DedZapretError):
        raise SafeExtractError("Extraction failed")


def test_process_execution_error_details():
    try:
        raise ProcessExecutionError(
            "Command failed", returncode=1, stdout="output", stderr="error"
        )
    except ProcessExecutionError as e:
        assert e.message == "Command failed"
        assert e.returncode == 1
        assert e.stdout == "output"
        assert e.stderr == "error"
    with pytest.raises(DedZapretError):
        raise ProcessExecutionError("Command failed")


def test_admin_required_error_inherits_dedzapret_error():
    with pytest.raises(AdminRequiredError, match="Admin rights needed"):
        raise AdminRequiredError("Admin rights needed")
    with pytest.raises(DedZapretError):
        raise AdminRequiredError("Admin rights needed")
