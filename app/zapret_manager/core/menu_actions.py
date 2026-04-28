from __future__ import annotations

import functools
import logging
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, TypeVar

from app.zapret_manager.core.audit import AuditEvent, append_audit
from app.zapret_manager.core.diagnostics import diag_log
from app.zapret_manager.core.mask import mask_secrets_text
from app.zapret_manager.ui.colors import C
from app.zapret_manager.utils.console import ask, safe_print


log = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


@dataclass(frozen=True)
class MenuActionCtx:
    audit_log: Path


def _default_action_ctx(ctx) -> MenuActionCtx:
    # ctx.paths.logs_dir exists in real AppContext.
    audit = (ctx.paths.logs_dir / "audit.jsonl").resolve()  # type: ignore[attr-defined]
    return MenuActionCtx(audit_log=audit)


def menu_handler(action_id: str) -> Callable[[F], F]:
    """Decorator for menu handlers:

    - audit start/end
    - catch exceptions
    - traceback only in logs
    - user-friendly error with options
    """

    def deco(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any):
            ctx = args[0] if args else None
            actx = _default_action_ctx(ctx) if ctx is not None else None
            try:
                if actx:
                    append_audit(actx.audit_log, AuditEvent(category="action.start", action_id=action_id, ok=True))
                diag_log("action.start", "ui", {"action_id": action_id})
                res = fn(*args, **kwargs)
                if actx:
                    append_audit(actx.audit_log, AuditEvent(category="action.end", action_id=action_id, ok=True))
                diag_log("action.end", "ui", {"action_id": action_id})
                return res
            except Exception as e:
                tb = traceback.format_exc()
                log.error("menu action failed: %s: %s\n%s", action_id, e, tb)
                diag_log(
                    "action.error",
                    "ui",
                    {"action_id": action_id, "error": str(e), "traceback": tb},
                )
                if actx:
                    append_audit(
                        actx.audit_log,
                        AuditEvent(category="action.error", action_id=action_id, ok=False, message=str(e)),
                    )

                # User-facing message must be safe and not leak secrets.
                msg = mask_secrets_text(str(e))
                safe_print(f"\n{C.RED}Ошибка:{C.RESET} {msg}\n")
                safe_print("Варианты:")
                safe_print(f"{C.CYAN}R{C.RESET}) Retry")
                safe_print(f"{C.CYAN}D{C.RESET}) Diagnostics (включить в config.yaml и перезапустить)")
                safe_print(f"{C.CYAN}B{C.RESET}) Bug report")
                safe_print(f"{C.CYAN}Enter{C.RESET}) Back")
                c = ask("\nВыберите: ").strip().lower()
                if c == "r":
                    return wrapper(*args, **kwargs)
                if c == "b":
                    # lazy import to avoid cycles
                    try:
                        from app.zapret_manager.core.report import generate_bug_report_zip
                        from app.zapret_manager.core.current_state import load_current_state

                        if ctx is not None:
                            cur = load_current_state(ctx.paths.data_dir / "state" / "current.json")
                            out = generate_bug_report_zip(
                                out_dir=ctx.paths.data_dir / "reports",
                                logs_dir=ctx.paths.logs_dir,
                                state_file=ctx.paths.state_file,
                                current_state_file=ctx.paths.data_dir / "state" / "current.json",
                                config_file=ctx.paths.config_file,
                            )
                            safe_print(f"\n{C.GREEN}Bug report создан:{C.RESET} {out}\n")
                    except Exception:
                        # ignore
                        pass
                return None

        return wrapper  # type: ignore[return-value]

    return deco
