from __future__ import annotations

"""Tray menu builder.

This module must not import pystray at import time.
We return a plain-Python menu spec that the tray app can convert to pystray.Menu.
"""

from dataclasses import dataclass, field
import threading

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.commands import (
    CommandResult,
    apply_recommended_strategy,
    create_bug_report,
    get_status_summary,
    open_logs_dir,
    repair_runtime,
    restart_current,
    run_test_all,
    set_engine_mode,
    singbox_restart,
    singbox_set_active_node,
    singbox_start_local_proxy,
    singbox_stop,
    stop_all,
    update_subscriptions,
)
from app.zapret_manager.tray.tray_worker import TrayWorker


@dataclass(frozen=True)
class MenuItemSpec:
    title: str
    action_id: str = ""
    enabled: bool = True
    checked: bool | None = None
    radio: bool = False
    children: list["MenuItemSpec"] = field(default_factory=list)


@dataclass(frozen=True)
class TrayMenuSpec:
    items: list[MenuItemSpec]


def build_tray_menu_spec(ctx: AppContext, worker: TrayWorker, *, status: CommandResult | None = None) -> TrayMenuSpec:
    """Build menu spec based on current lightweight status."""
    st = status or get_status_summary(ctx)
    d = st.details or {}
    zap = d.get("zapret") if isinstance(d.get("zapret"), dict) else {}
    sb = d.get("singbox") if isinstance(d.get("singbox"), dict) else {}
    latest = d.get("latest_ranking") if isinstance(d.get("latest_ranking"), dict) else {}

    zap_running = bool(zap.get("running"))
    cur_strategy = str(zap.get("active_strategy") or "").strip() or "-"
    engine_mode = str(zap.get("engine_mode") or "auto").strip().lower() or "auto"
    vpn_running = bool(sb.get("running"))
    recommended = str(latest.get("recommended") or "").strip() or "-"

    job = worker.snapshot()
    busy = job.state in {"running", "cancel_requested"}
    can_start = worker.can_start()

    def _group(title: str, children: list[MenuItemSpec]) -> MenuItemSpec:
        return MenuItemSpec(title=title, enabled=True, children=children)

    # VPN nodes submenu (masked labels only).
    node_items: list[MenuItemSpec] = []
    try:
        from app.zapret_manager.core.singbox.nodes import load_nodes

        nodes = load_nodes((ctx.paths.nodes_dir / "nodes.json").resolve())
        for n in nodes[:30]:
            label = n.masked_summary()
            node_items.append(MenuItemSpec(title=label, action_id=f"vpn.select_node:{n.node_id}", enabled=can_start))
        if not nodes:
            node_items.append(MenuItemSpec(title="(нет нод)", action_id="noop", enabled=False))
    except Exception:
        node_items.append(MenuItemSpec(title="(не удалось загрузить ноды)", action_id="noop", enabled=False))

    items: list[MenuItemSpec] = [
        MenuItemSpec(title="DedZapret", action_id="noop", enabled=False),
        MenuItemSpec(title=f"Статус: {'ACTIVE' if zap_running else ('VPN' if vpn_running else 'OFF')}", action_id="noop", enabled=False),
        _group(
            "Основное",
            [
                MenuItemSpec(title="Включить Recommended", action_id="apply_recommended", enabled=can_start),
                MenuItemSpec(title="Отключить всё", action_id="stop_all", enabled=True),
                MenuItemSpec(title="Перезапустить текущий режим", action_id="restart_current", enabled=True),
            ],
        ),
        _group(
            "VPN",
            [
                MenuItemSpec(title="Активировать VPN (local proxy)", action_id="vpn.start", enabled=can_start),
                MenuItemSpec(title="Отключить VPN", action_id="vpn.stop", enabled=can_start),
                MenuItemSpec(title="Перезапустить VPN", action_id="vpn.restart", enabled=can_start),
                _group("Выбрать локацию", node_items),
                MenuItemSpec(title="Обновить подписку", action_id="update_subs", enabled=can_start),
            ],
        ),
        _group(
            "Стратегии",
            [
                MenuItemSpec(title=f"Recommended: {recommended}", action_id="noop", enabled=False),
                MenuItemSpec(title=f"Текущая: {cur_strategy}", action_id="noop", enabled=False),
                MenuItemSpec(title="Выбрать стратегию... (в консоли)", action_id="noop", enabled=False),
                MenuItemSpec(title=f"Тест всех стратегий...{(' (' + job.name + ')') if busy and job.name else ''}", action_id="test_all", enabled=can_start),
                MenuItemSpec(title="Остановить тест/задачу", action_id="cancel_job", enabled=job.state == "running"),
            ],
        ),
        _group(
            "Диагностика",
            [
                MenuItemSpec(title="Диагностика sing-box", action_id="singbox_health", enabled=can_start),
                MenuItemSpec(title="Починить runtime assets", action_id="repair_runtime", enabled=can_start),
                MenuItemSpec(title="Создать отчёт об ошибке (bug report)", action_id="bug_report", enabled=can_start),
                MenuItemSpec(title="Открыть логи", action_id="open_logs", enabled=True),
            ],
        ),
        _group(
            "Настройки",
            [
                MenuItemSpec(title="Автозапуск: (ещё не реализовано)", action_id="noop", enabled=False),
                MenuItemSpec(title="Запускать в трей: меняется в config.yaml", action_id="noop", enabled=False),
                _group(
                    "Runtime engine",
                    [
                        MenuItemSpec(title="Auto", action_id="engine.auto", enabled=True, checked=engine_mode == "auto", radio=True),
                        MenuItemSpec(title="winws", action_id="engine.winws", enabled=True, checked=engine_mode == "winws", radio=True),
                        MenuItemSpec(title="winws2", action_id="engine.winws2", enabled=True, checked=engine_mode == "winws2", radio=True),
                    ],
                ),
                MenuItemSpec(title="Открыть полное меню (в консоли)", action_id="noop", enabled=False),
            ],
        ),
        MenuItemSpec(title="Выход", action_id="exit", enabled=True),
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
    if action_id == "apply_recommended":
        return apply_recommended_strategy(ctx, restart_if_running=True)
    if action_id == "open_logs":
        return open_logs_dir(ctx)
    if action_id == "engine.auto":
        return set_engine_mode(ctx, "auto")
    if action_id == "engine.winws":
        return set_engine_mode(ctx, "winws")
    if action_id == "engine.winws2":
        return set_engine_mode(ctx, "winws2")

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

    if action_id == "vpn.start":
        def _job(cancel: threading.Event) -> str:
            if cancel.is_set():
                return "Отменено"
            r = singbox_start_local_proxy(ctx)
            return r.message

        if not worker.start(name="vpn_start", fn=_job):
            return CommandResult(ok=False, message="Уже выполняется задача.")
        return None

    if action_id == "vpn.stop":
        def _job(cancel: threading.Event) -> str:
            if cancel.is_set():
                return "Отменено"
            r = singbox_stop(ctx)
            return r.message

        if not worker.start(name="vpn_stop", fn=_job):
            return CommandResult(ok=False, message="Уже выполняется задача.")
        return None

    if action_id == "vpn.restart":
        def _job(cancel: threading.Event) -> str:
            if cancel.is_set():
                return "Отменено"
            r = singbox_restart(ctx)
            return r.message

        if not worker.start(name="vpn_restart", fn=_job):
            return CommandResult(ok=False, message="Уже выполняется задача.")
        return None

    if action_id.startswith("vpn.select_node:"):
        node_id = action_id.split(":", 1)[1].strip()

        def _job(cancel: threading.Event) -> str:
            if cancel.is_set():
                return "Отменено"
            r = singbox_set_active_node(ctx, node_id, restart=True)
            return r.message

        if not worker.start(name="vpn_select_node", fn=_job):
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

    if action_id == "singbox_health":
        # Lightweight: allow sync call.
        from app.zapret_manager.core.commands import singbox_health

        return singbox_health(ctx)

    return CommandResult(ok=False, message=f"Неизвестное действие: {action_id}")
