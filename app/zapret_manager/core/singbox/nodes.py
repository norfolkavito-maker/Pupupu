from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from app.zapret_manager.core.mask import mask_secrets_text


@dataclass(frozen=True)
class SingBoxNode:
    node_id: str
    name: str
    protocol: str
    server: str
    port: int
    # raw may contain secrets. We keep it in-memory but never write unmasked.
    raw: str
    extra: dict[str, Any]

    # Auth (optional per protocol)
    uuid: str = ""
    password: str = ""
    method: str = ""  # shadowsocks cipher

    def masked_summary(self) -> str:
        return mask_secrets_text(f"{self.name} [{self.protocol}] {self.server}:{self.port}")


def _gen_id(proto: str, server: str, port: int) -> str:
    s = f"{proto}:{server}:{port}".encode("utf-8")
    return base64.urlsafe_b64encode(s).decode("ascii").rstrip("=")


def load_nodes(path: Path) -> list[SingBoxNode]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    out: list[SingBoxNode] = []
    if isinstance(data, list):
        for it in data:
            if not isinstance(it, dict):
                continue
            out.append(
                SingBoxNode(
                    node_id=str(it.get("node_id", "")),
                    name=str(it.get("name", "")),
                    protocol=str(it.get("protocol", "")),
                    server=str(it.get("server", "")),
                    port=int(it.get("port", 0) or 0),
                    raw=str(it.get("raw", "")),
                    extra=it.get("extra", {}) or {},
                    uuid=str(it.get("uuid", "") or ""),
                    password=str(it.get("password", "") or ""),
                    method=str(it.get("method", "") or ""),
                )
            )
    return out


def serialize_nodes_for_report(nodes: list[SingBoxNode]) -> list[dict[str, Any]]:
    """Serialize nodes for shareable reports with full masking."""
    return [
        {
            "node_id": n.node_id,
            "name": n.name,
            "protocol": n.protocol,
            "server": mask_secrets_text(n.server, mode="shareable_report"),
            "port": n.port,
            "raw": mask_secrets_text(n.raw, mode="shareable_report"),
            "extra": n.extra,
            "uuid": "***",  # Always mask UUID in reports
            "password": "***",  # Always mask password in reports
            "method": n.method,
        }
        for n in nodes
    ]


def save_nodes(path: Path, nodes: list[SingBoxNode]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [
        {
            "node_id": n.node_id,
            "name": n.name,
            "protocol": n.protocol,
            "server": n.server,
            "port": n.port,
            # raw link must NOT be saved as-is. store masked raw for trace.
            "raw": mask_secrets_text(n.raw),
            "extra": n.extra,
            # secrets stored locally (not included in bug report)
            "uuid": n.uuid,
            "password": n.password,
            "method": n.method,
        }
        for n in nodes
    ]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def import_node_from_link(link: str) -> SingBoxNode:
    link = link.strip()
    if not link:
        raise ValueError("empty link")

    u = urlparse(link)
    proto = (u.scheme or "").lower()
    if proto not in {"vless", "vmess", "trojan", "ss"}:
        raise ValueError(f"unsupported scheme: {proto}")

    # Minimal parse: server/port only (no secrets stored)
    server = u.hostname or ""
    port = int(u.port or 0)
    if not server or not port:
        raise ValueError("invalid link: missing server/port")

    name = ""
    if u.fragment:
        name = u.fragment
    elif u.path and u.path != "/":
        name = u.path.strip("/")
    if not name:
        name = f"{proto}@{server}:{port}"

    extra: dict[str, Any] = {}
    if u.query:
        q = parse_qs(u.query)
        extra = {k: v[0] if len(v) == 1 else v for k, v in q.items()}

    uuid = ""
    password = ""
    method = ""

    if proto in {"vless", "trojan"}:
        # userinfo (before @) is uuid/password
        userinfo = (u.username or "")
        if userinfo:
            if proto == "vless":
                uuid = userinfo
            else:
                password = userinfo
    elif proto == "ss":
        # ss://method:password@server:port
        if u.username:
            method = u.username
        if u.password:
            password = u.password
    elif proto == "vmess":
        # vmess://base64(json)
        try:
            # remove vmess://
            raw = link.split("vmess://", 1)[1]
            raw += "=" * (-len(raw) % 4)
            decoded = base64.b64decode(raw.encode("utf-8"), validate=False).decode("utf-8", errors="replace")
            j = json.loads(decoded)
            uuid = str(j.get("id") or j.get("uuid") or "")
            # host/port already parsed from URL may be empty; fill from JSON if needed
            if not server:
                server = str(j.get("add") or j.get("host") or "")
            if not port:
                try:
                    port = int(j.get("port") or 0)
                except Exception:
                    port = 0
            extra.update({"vmess": {k: v for k, v in j.items() if k not in {"id"}}})
        except Exception:
            pass

    node_id = _gen_id(proto, server, port)
    return SingBoxNode(
        node_id=node_id,
        name=name,
        protocol=proto,
        server=server,
        port=port,
        raw=link,
        extra=extra,
        uuid=uuid,
        password=password,
        method=method,
    )
