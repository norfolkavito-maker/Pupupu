from __future__ import annotations

"""Tray menu builder.

This module must not import pystray at import time.
We return a plain-Python menu spec that the tray app can convert to pystray.Menu.
"""

from dataclasses import dataclass
import threading

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.commands import (
    CommandResult,
    create_bug_report,
    get_status_summary,
    repair_runtime,
    restart_current,
    run_test_all,
    stop_all,
    update_subscriptions,
)
from app.zapret_manager.tray.tray_worker import TrayWorker


@dataclass(frozen=True)
class MenuItemSpec:
    title: str
    action_id: str
    enabled: bool = True


@dataclass(frozen=True)
class TrayMenuSpec:
    items: list[MenuItemSpec]


def build_tray_menu_spec(ctx: AppContext, worker: TrayWorker) -> TrayMenuSpec:
    """Build menu spec based on current lightweight status."""
    # Called for side-effect only: if summary fails we still want menu to exist.
    _ = get_status_summary(ctx)
    # NOTE: keep this as future hook; we currently do not show recommended in menu
    # to avoid overcomplicating the first tray MVP.

    job = worker.snapshot()
    job_suffix = f" ({job.name})" if job.state in {"running", "cancel_requested"} and job.name else ""

    items: list[MenuItemSpec] = [
        MenuItemSpec(title=f"DedZapret{job_suffix}", action_id="noop", enabled=False),
        MenuItemSpec(title="Перезапустить текущий режим", action_id="restart_current"),
        MenuItemSpec(title="Отключить всё", action_id="stop_all"),
        MenuItemSpec(title=f"Тест всех стратегий...{job_suffix}", action_id="test_all", enabled=worker.can_start()),
        MenuItemSpec(title="Остановить задачу", action_id="cancel_job", enabled=job.state == "running"),
        MenuItemSpec(title="Обновить подписки VPN", action_id="update_subs", enabled=worker.can_start()),
        MenuItemSpec(title="Починить runtime assets", action_id="repair_runtime", enabled=worker.can_start()),
        MenuItemSpec(title="Создать bug report", action_id="bug_report", enabled=worker.can_start()),
        MenuItemSpec(title="Выход", action_id="exit"),
    ]
    return TrayMenuSpec(items=items)


def handle_menu_action(
    *,
    ctx: AppContext,
    worker: TrayWorker,
    action_id: str,
) -> CommandResult | None:
    """Execute menu action.

    For long actions returns None (handled by worker).
    For immediate actions returns CommandResult.
    """
    if action_id == "noop":
        return None
    if action_id == "stop_all":
        return stop_all(ctx)
    if action_id == "restart_current":
        return restart_current(ctx)
    if action_id == "cancel_job":
        ok = worker.request_cancel()
        return CommandResult(ok=ok, message="Отмена запрошена." if ok else "Нет активной задачи.")

    # long jobs
    if action_id == "test_all":
        def _job(cancel: threading.Event) -> str:
            # Current test engine cancellation is only wired via Ctrl+C; here we only
            # provide best-effort cooperative cancel for future.
            if cancel.is_set():
                return "Отменено"
            r = run_test_all(ctx, domain_set="default", mode="quick")
            return r.message

        if not worker.start(name="test_all", fn=_job):
            return CommandResult(ok=False, message="Уже выполняется задача.")
        return None

    if action_id == "update_subs":
        def _job(cancel: threading.Event) -> str:
            if cancel.is_set():
                return "Отменено"
            r = update_subscriptions(ctx)
            return r.message

        if not worker.start(name="update_subscriptions", fn=_job):
            return CommandResult(ok=False, message="Уже выполняется задача.")
        return None

    if action_id == "repair_runtime":
        def _job(cancel: threading.Event) -> str:
            if cancel.is_set():
                return "Отменено"
            r = repair_runtime(ctx)
            return r.message

        if not worker.start(name="repair_runtime", fn=_job):
            return CommandResult(ok=False, message="Уже выполняется задача.")
        return None

    if action_id == "bug_report":
        def _job(cancel: threading.Event) -> str:
            if cancel.is_set():
                return "Отменено"
            r = create_bug_report(ctx)
            return r.message

        if not worker.start(name="bug_report", fn=_job):
            return CommandResult(ok=False, message="Уже выполняется задача.")
        return None

    return CommandResult(ok=False, message=f"Неизвестное действие: {action_id}")
