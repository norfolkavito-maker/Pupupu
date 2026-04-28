from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.zapret_manager.core.singbox.nodes import SingBoxNode


DNS_PRESETS: dict[str, list[str]] = {
    "system": [],
    "cloudflare": ["1.1.1.1", "1.0.0.1"],
    "google": ["8.8.8.8", "8.8.4.4"],
    "quad9": ["9.9.9.9", "149.112.112.112"],
    "adguard": ["94.140.14.14", "94.140.15.15"],
}


@dataclass(frozen=True)
class SingBoxBuildOptions:
    socks_listen: str = "127.0.0.1"
    socks_port: int = 2080
    http_listen: str = "127.0.0.1"
    http_port: int = 2081
    dns_mode: str = "system"


def build_config(*, node: SingBoxNode, opt: SingBoxBuildOptions) -> dict[str, Any]:
    """Build minimal sing-box config for local proxy mode."""

    inbounds = [
        {
            "type": "socks",
            "tag": "socks-in",
            "listen": opt.socks_listen,
            "listen_port": opt.socks_port,
        },
        {
            "type": "mixed",
            "tag": "mixed-in",
            "listen": opt.http_listen,
            "listen_port": opt.http_port,
        },
    ]

    outbounds = [
        {"type": "direct", "tag": "direct"},
        {"type": "block", "tag": "block"},
    ]

    # Minimal outbound mapping for local proxy.
    if node.protocol == "ss":
        if not node.method or not node.password:
            raise ValueError("shadowsocks node missing method/password")
        outbounds.insert(
            0,
            {
                "type": "shadowsocks",
                "tag": "proxy",
                "server": node.server,
                "server_port": node.port,
                "method": node.method,
                "password": node.password,
            },
        )
    elif node.protocol == "trojan":
        if not node.password:
            raise ValueError("trojan node missing password")
        outbounds.insert(
            0,
            {
                "type": "trojan",
                "tag": "proxy",
                "server": node.server,
                "server_port": node.port,
                "password": node.password,
            },
        )
    elif node.protocol == "vless":
        if not node.uuid:
            raise ValueError("vless node missing uuid")
        outbounds.insert(
            0,
            {
                "type": "vless",
                "tag": "proxy",
                "server": node.server,
                "server_port": node.port,
                "uuid": node.uuid,
            },
        )
    elif node.protocol == "vmess":
        if not node.uuid:
            raise ValueError("vmess node missing uuid")
        outbounds.insert(
            0,
            {
                "type": "vmess",
                "tag": "proxy",
                "server": node.server,
                "server_port": node.port,
                "uuid": node.uuid,
            },
        )
    else:
        raise ValueError(f"unsupported node protocol: {node.protocol}")

    dns: dict[str, Any] = {}
    servers = DNS_PRESETS.get(opt.dns_mode, [])
    if servers:
        dns = {"servers": [{"tag": "dns", "address": a} for a in servers]}

    return {
        "log": {"level": "info"},
        "inbounds": inbounds,
        "outbounds": outbounds,
        "route": {"final": "proxy"},
        **({"dns": dns} if dns else {}),
    }


def write_config(path: Path, cfg: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
