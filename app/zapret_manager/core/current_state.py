from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ManagedProcessState:
    name: str
    pid: int | None = None
    running: bool = False
    started_utc: str = ""
    exit_code: int | None = None
    last_error: str = ""


@dataclass
class CurrentState:
    version: int = 1
    active_backend: str = "zapret"  # zapret|singbox (future)
    active_singbox_node_id: str = ""
    singbox_dns_mode: str = "system"  # system|cloudflare|google|quad9|adguard|custom
    last_good_singbox_config: str = ""  # path string
    update_lock: bool = False
    last_error: str = ""
    processes: dict[str, ManagedProcessState] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "active_backend": self.active_backend,
            "active_singbox_node_id": self.active_singbox_node_id,
            "singbox_dns_mode": self.singbox_dns_mode,
            "last_good_singbox_config": self.last_good_singbox_config,
            "update_lock": self.update_lock,
            "last_error": self.last_error,
            "processes": {
                k: {
                    "name": v.name,
                    "pid": v.pid,
                    "running": v.running,
                    "started_utc": v.started_utc,
                    "exit_code": v.exit_code,
                    "last_error": v.last_error,
                }
                for k, v in self.processes.items()
            },
        }


def default_current_state() -> CurrentState:
    st = CurrentState()
    st.processes["singbox"] = ManagedProcessState(name="singbox")
    return st


def load_current_state(path: Path) -> CurrentState:
    if not path.exists():
        st = default_current_state()
        save_current_state(path, st)
        return st
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        broken = path.with_suffix(path.suffix + ".broken")
        shutil.move(str(path), str(broken))
        st = default_current_state()
        save_current_state(path, st)
        return st

    st = default_current_state()
    st.version = int(data.get("version", 1) or 1)
    st.active_backend = str(data.get("active_backend", st.active_backend) or st.active_backend)
    st.active_singbox_node_id = str(data.get("active_singbox_node_id", "") or "")
    st.singbox_dns_mode = str(data.get("singbox_dns_mode", st.singbox_dns_mode) or st.singbox_dns_mode)
    st.last_good_singbox_config = str(data.get("last_good_singbox_config", "") or "")
    st.update_lock = bool(data.get("update_lock", False))
    st.last_error = str(data.get("last_error", "") or "")

    procs = data.get("processes", {}) or {}
    if isinstance(procs, dict):
        for k, v in procs.items():
            if not isinstance(v, dict):
                continue
            st.processes[str(k)] = ManagedProcessState(
                name=str(v.get("name", k)),
                pid=v.get("pid"),
                running=bool(v.get("running", False)),
                started_utc=str(v.get("started_utc", "") or ""),
                exit_code=v.get("exit_code"),
                last_error=str(v.get("last_error", "") or ""),
            )

    if "singbox" not in st.processes:
        st.processes["singbox"] = ManagedProcessState(name="singbox")

    return st


def save_current_state(path: Path, state: CurrentState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_json(), ensure_ascii=False, indent=2), encoding="utf-8")
