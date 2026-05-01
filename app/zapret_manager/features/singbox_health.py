from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.zapret_manager.core.current_state import load_current_state
from app.zapret_manager.core.mask import mask_secrets_text
from app.zapret_manager.core.singbox.binary import detect_singbox_binary, singbox_version
from app.zapret_manager.core.singbox.health import singbox_health_summary
from app.zapret_manager.core.singbox.nodes import load_nodes


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class SingBoxHealthReport:
    # binary
    binary_found: bool
    binary_path: str
    version_ok: bool
    version_text: str
    version_error: str

    # nodes
    nodes_count: int
    active_node_id: str
    active_node_exists: bool
    active_node_summary_masked: str

    # config
    generated_config_exists: bool
    config_validate_ok: bool
    config_validate_error: str

    # process/ports
    process_running: bool
    pid: int
    socks_port_open: bool
    mixed_port_open: bool

    # state
    last_error: str

    # recommendation
    recommended_action: str

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def _config_path(data_dir: Path) -> Path:
    return (data_dir / "singbox" / "generated_config.json").resolve()


def _recommendation(
    *,
    binary_found: bool,
    nodes_count: int,
    active_node_id: str,
    active_node_exists: bool,
    generated_config_exists: bool,
    running: bool,
    socks_open: bool,
    mixed_open: bool,
) -> str:
    if not binary_found:
        return "Установите sing-box (sing-box.exe отсутствует в bin/sing-box)."

    if nodes_count <= 0:
        return "Обновите подписки. Если ноды не появились — проверьте формат подписки."

    if not active_node_id or not active_node_exists:
        return "Выберите active node или повторите Update subscriptions для auto-select."

    if not generated_config_exists:
        return "Сгенерируйте конфиг (Generate config preview) и затем запустите sing-box local proxy."

    if not running:
        return "Запустите sing-box local proxy."

    if not (socks_open and mixed_open):
        return "Похоже, sing-box запущен, но порты не открыты. Попробуйте Restart sing-box."

    return "Состояние OK."


def build_singbox_health_report(*, data_dir: Path, root_dir: Path) -> SingBoxHealthReport:
    """Aggregate sing-box state into a single health report.

    This is a high-level aggregator/formatter. Low-level port/process checks are
    delegated to core.singbox.health.singbox_health_summary().
    """

    cur_path = (data_dir / "state" / "current.json").resolve()
    cur = load_current_state(cur_path)

    # binary + version
    bin = detect_singbox_binary(root_dir)
    binary_found = bool(bin)
    binary_path = str(bin.path) if bin else ""
    version_text = ""
    version_error = ""
    version_ok = False
    if bin:
        try:
            version_text = singbox_version(bin.path)
            version_ok = bool(version_text.strip())
        except Exception as e:
            version_error = str(e)
            version_ok = False

    # nodes + active
    nodes_path = (data_dir / "singbox" / "nodes.json").resolve()
    nodes = load_nodes(nodes_path)
    nodes_count = len(nodes)
    active_node_id = (cur.active_singbox_node_id or "").strip()
    active = next((n for n in nodes if n.node_id == active_node_id), None) if active_node_id else None
    active_node_exists = bool(active)
    active_node_summary_masked = active.masked_summary() if active else ""

    # config presence (we don't have a real sing-box "check" command wired; keep best-effort)
    cfg_path = _config_path(data_dir)
    generated_config_exists = cfg_path.exists() and cfg_path.is_file() and cfg_path.stat().st_size > 0
    config_validate_ok = generated_config_exists
    config_validate_error = "" if generated_config_exists else "generated_config.json отсутствует"

    # process/ports via core
    hs = singbox_health_summary(cur_path)
    running = bool(hs.get("running"))
    pid = int(hs.get("pid") or 0)
    ports = hs.get("ports") or {}
    socks_open = bool(ports.get("2080"))
    mixed_open = bool(ports.get("2081"))

    last_error = mask_secrets_text(cur.last_error or "")

    recommended_action = _recommendation(
        binary_found=binary_found,
        nodes_count=nodes_count,
        active_node_id=active_node_id,
        active_node_exists=active_node_exists,
        generated_config_exists=generated_config_exists,
        running=running,
        socks_open=socks_open,
        mixed_open=mixed_open,
    )

    return SingBoxHealthReport(
        binary_found=binary_found,
        binary_path=binary_path,
        version_ok=version_ok,
        version_text=mask_secrets_text(version_text),
        version_error=mask_secrets_text(version_error),
        nodes_count=nodes_count,
        active_node_id=active_node_id,
        active_node_exists=active_node_exists,
        active_node_summary_masked=mask_secrets_text(active_node_summary_masked),
        generated_config_exists=generated_config_exists,
        config_validate_ok=config_validate_ok,
        config_validate_error=mask_secrets_text(config_validate_error),
        process_running=running,
        pid=pid,
        socks_port_open=socks_open,
        mixed_port_open=mixed_open,
        last_error=last_error,
        recommended_action=recommended_action,
    )


def format_singbox_health_text(r: SingBoxHealthReport) -> str:
    def ok(v: bool) -> str:
        return "OK" if v else "FAIL"

    def yn(v: bool) -> str:
        return "yes" if v else "no"

    lines: list[str] = []
    lines.append("sing-box health")
    lines.append("---------------")

    lines.append(f"Бинарник: {ok(r.binary_found)}" + (f" ({r.binary_path})" if r.binary_found and r.binary_path else ""))
    if r.binary_found:
        if r.version_ok:
            first = (r.version_text.splitlines() or [""])[0].strip()
            lines.append(f"Версия: OK, {first or 'sing-box'}")
        else:
            lines.append(f"Версия: FAIL{(': ' + r.version_error) if r.version_error else ''}")

    lines.append(f"Ноды: {r.nodes_count}")
    if not r.active_node_id:
        lines.append("Активная нода: отсутствует")
    else:
        if r.active_node_exists:
            lines.append(f"Активная нода: OK, {r.active_node_summary_masked}")
        else:
            lines.append("Активная нода: отсутствует")

    lines.append(f"Конфиг: {'OK' if r.generated_config_exists else 'отсутствует'}")
    if r.generated_config_exists:
        lines.append(f"Validate config: {ok(r.config_validate_ok)}")
    else:
        lines.append("Validate config: skip")

    lines.append(f"Процесс: {'running' if r.process_running else 'stopped'}" + (f" pid={r.pid}" if r.pid else ""))
    lines.append(f"SOCKS порт: {'open' if r.socks_port_open else 'closed'}")
    lines.append(f"HTTP/Mixed порт: {'open' if r.mixed_port_open else 'closed'}")

    if r.last_error:
        lines.append("")
        lines.append(f"last_error: {r.last_error}")

    lines.append("")
    lines.append("Рекомендация:")
    lines.append(r.recommended_action)
    lines.append("")
    return "\n".join(lines)


def write_singbox_health_artifacts(*, data_dir: Path, report: SingBoxHealthReport) -> tuple[Path, Path]:
    """Write health artifacts into data_dir/singbox for bug report attachment."""
    out_dir = (data_dir / "singbox").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    p_json = (out_dir / "singbox_health.json").resolve()
    p_txt = (out_dir / "singbox_health.txt").resolve()
    p_json.write_text(json.dumps(report.to_json(), ensure_ascii=False, indent=2), encoding="utf-8")
    p_txt.write_text(format_singbox_health_text(report), encoding="utf-8")
    return p_json, p_txt
