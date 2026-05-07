
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Result:
    ok: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)

    @staticmethod
    def ok_result(
        message: str = "Success",
        details: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None,
        next_actions: Optional[List[str]] = None,
    ) -> "Result":
        return Result(
            ok=True,
            message=message,
            details=details or {},
            warnings=warnings or [],
            errors=[],
            next_actions=next_actions or [],
        )

    @staticmethod
    def fail_result(
        message: str = "Failure",
        details: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None,
        next_actions: Optional[List[str]] = None,
    ) -> "Result":
        return Result(
            ok=False,
            message=message,
            details=details or {},
            warnings=[],
            errors=errors or [],
            next_actions=next_actions or [],
        )
