from __future__ import annotations

"""Tray-friendly status mapping.

Tray must stay lightweight and must not touch heavy runtime checks.
We build status based on `core.commands.get_status_summary()` only.
"""

from dataclasses import dataclass

from app.zapret_manager.core.commands import CommandResult
from app.zapret_manager.tray.tray_worker import TrayJobSnapshot


@dataclass(frozen=True)
class TrayStatus:
    level: str  # gray|green|blue|purple|yellow|red
    title: str
    tooltip: str


def status_from_command_result(res: CommandResult, *, job: TrayJobSnapshot | None = None) -> TrayStatus:
    if not res.ok:
        msg = (res.message or "Ошибка")
        err = (res.errors[0] if res.errors else "")
        tooltip = "\n".join(["DedZapret: ERROR", f"Причина: {msg}", err]).strip()
        return TrayStatus(level="red", title="DedZapret: ERROR", tooltip=tooltip)

    d = res.details or {}
    zap = d.get("zapret") if isinstance(d.get("zapret"), dict) else {}
    sb = d.get("singbox") if isinstance(d.get("singbox"), dict) else {}
    pd = d.get("problem_domains") if isinstance(d.get("problem_domains"), dict) else {}
    assets = d.get("runtime_assets") if isinstance(d.get("runtime_assets"), dict) else {}
    latest = d.get("latest_ranking") if isinstance(d.get("latest_ranking"), dict) else {}

    zap_running = bool(zap.get("running"))
    st = str(zap.get("active_strategy") or "").strip()
    engine_mode = str(zap.get("engine_mode") or "auto").strip().lower() or "auto"
    sb_running = bool(sb.get("running"))
    pd_count = int(pd.get("count") or 0)
    runtime_ok = bool(assets.get("ok"))
    recommended = str(latest.get("recommended") or "").strip()

    # Running background job (tray-only) overrides status level.
    if job and job.state in {"running", "cancel_requested"}:
        title = "DedZapret: BUSY"
        tooltip_lines = [
            title,
            f"Задача: {job.name or '-'}",
            f"Статус: {job.state}",
        ]
        if job.message:
            tooltip_lines.append(job.message)
        return TrayStatus(level="purple", title=title, tooltip="\n".join(tooltip_lines).strip())

    # warnings first
    if (not runtime_ok) or pd_count > 0:
        level = "yellow"
    else:
        # active signals
        if zap_running:
            level = "green"
        elif sb_running:
            level = "blue"
        else:
            level = "gray"

    state = "ACTIVE" if zap_running else ("VPN" if sb_running else "OFF")
    title = f"DedZapret: {state}"

    tooltip_lines = [
        title,
        f"Стратегия: {st or 'нет'}",
        f"Engine: {engine_mode}",
        f"VPN: {'ON' if sb_running else 'OFF'}",
        f"Проблемные домены: {pd_count}",
    ]
    if recommended:
        tooltip_lines.append(f"Recommended: {recommended}")
    if not runtime_ok:
        tooltip_lines.append("Runtime: MISSING/BROKEN")
    return TrayStatus(level=level, title=title, tooltip="\n".join(tooltip_lines))
