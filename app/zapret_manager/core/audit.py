
import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.zapret_manager.core.paths import AppPaths
from app.zapret_manager.core.atomic_write import atomic_write_text # We'll append, not fully atomic rewrite for logs
from app.zapret_manager.core.mask import mask_mapping


class AuditLogger:
    def __init__(self, audit_log_path: Path):
        self.audit_log_path = audit_log_path
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        action: str,
        component: str,
        success: bool,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
    ) -> None:
        event = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "action": action,
            "component": component,
            "success": success,
            "message": message,
            "details": mask_mapping(details) if details else {},
            "warnings": warnings or [],
            "errors": errors or [],
        }
        try:
            # Append to the log file. Not fully atomic for append, but safe enough for JSONL.
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception as e:
            # Fallback for audit logging failure - print to console
            print(f"WARNING: Failed to write audit event to {self.audit_log_path}: {e}")
            print(f"Failed audit event: {json.dumps(event, ensure_ascii=False)}")


def create_audit_logger(paths: AppPaths) -> AuditLogger:
    return AuditLogger(paths.logs_dir / "audit.jsonl")
