from __future__ import annotations

import socket
from pathlib import Path

from app.zapret_manager.core.current_state import load_current_state


def is_tcp_port_open(host: str, port: int, *, timeout_s: float = 0.4) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout_s):
            return True
    except Exception:
        return False


def singbox_health_summary(current_state_path: Path) -> dict[str, object]:
    cur = load_current_state(current_state_path)
    p = cur.processes.get("singbox")
    running = bool(p and p.running)
    pid = int(p.pid) if (p and p.pid) else 0
    socks = is_tcp_port_open("127.0.0.1", 2080)
    mixed = is_tcp_port_open("127.0.0.1", 2081)
    return {
        "running": running,
        "pid": pid,
        "ports": {"2080": socks, "2081": mixed},
        "ok": bool(running and socks and mixed),
    }
