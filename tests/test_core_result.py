
import pytest
from app.zapret_manager.core.result import Result


def test_result_dataclass_defaults():
    result = Result(ok=True, message="Test")
    assert result.ok is True
    assert result.message == "Test"
    assert result.details == {}
    assert result.warnings == []
    assert result.errors == []
    assert result.next_actions == []


def test_result_dataclass_custom_values():
    result = Result(
        ok=False,
        message="Error",
        details={"code": 404},
        warnings=["Low disk space"],
        errors=["File not found"],
        next_actions=["Check path"],
    )
    assert result.ok is False
    assert result.message == "Error"
    assert result.details == {"code": 404}
    assert result.warnings == ["Low disk space"]
    assert result.errors == ["File not found"]
    assert result.next_actions == ["Check path"]


def test_ok_result_static_method():
    result = Result.ok_result("Operation successful", details={"id": 123})
    assert result.ok is True
    assert result.message == "Operation successful"
    assert result.details == {"id": 123}
    assert result.warnings == []
    assert result.errors == []
    assert result.next_actions == []


def test_ok_result_static_method_with_warnings_and_actions():
    result = Result.ok_result(
        "Partial success",
        warnings=["Some issues found"],
        next_actions=["Review logs"],
    )
    assert result.ok is True
    assert result.message == "Partial success"
    assert result.details == {}
    assert result.warnings == ["Some issues found"]
    assert result.errors == []
    assert result.next_actions == ["Review logs"]


def test_fail_result_static_method():
    result = Result.fail_result("Operation failed", errors=["Access denied"])
    assert result.ok is False
    assert result.message == "Operation failed"
    assert result.details == {}
    assert result.warnings == []
    assert result.errors == ["Access denied"]
    assert result.next_actions == []


def test_fail_result_static_method_with_details_and_actions():
    result = Result.fail_result(
        "Critical error",
        details={"component": "DB"},
        errors=["Connection refused"],
        next_actions=["Restart DB", "Check firewall"],
    )
    assert result.ok is False
    assert result.message == "Critical error"
    assert result.details == {"component": "DB"}
    assert result.warnings == []
    assert result.errors == ["Connection refused"]
    assert result.next_actions == ["Restart DB", "Check firewall"]
