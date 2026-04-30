from __future__ import annotations

import base64
import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from app.zapret_manager.core.mask import mask_secrets_text
from app.zapret_manager.core.singbox.nodes import SingBoxNode, import_node_from_link


@dataclass(frozen=True)
class SubscriptionRecord:
    subscription_id: str
    name: str
    url: str
    enabled: bool = True
    last_update_at: str = ""
    last_error: str = ""
    node_count: int = 0


def _sub_id(name: str, url: str) -> str:
    raw = f"{name}|{url}".encode("utf-8", errors="replace")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")[:32]


def load_subscriptions(path: Path) -> list[SubscriptionRecord]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    out: list[SubscriptionRecord] = []
    if isinstance(data, list):
        for it in data:
            if not isinstance(it, dict):
                continue
            out.append(
                SubscriptionRecord(
                    subscription_id=str(it.get("subscription_id", "")),
                    name=str(it.get("name", "")),
                    url=str(it.get("url", "")),
                    enabled=bool(it.get("enabled", True)),
                    last_update_at=str(it.get("last_update_at", "")),
                    last_error=str(it.get("last_error", "")),
                    node_count=int(it.get("node_count", 0) or 0),
                )
            )
    return out


def save_subscriptions(path: Path, subs: list[SubscriptionRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [
        {
            "subscription_id": s.subscription_id,
            "name": s.name,
            "url": s.url,
            "enabled": s.enabled,
            "last_update_at": s.last_update_at,
            "last_error": s.last_error,
            "node_count": s.node_count,
        }
        for s in subs
    ]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_subscription(subs: list[SubscriptionRecord], *, name: str, url: str) -> list[SubscriptionRecord]:
    sid = _sub_id(name.strip(), url.strip())
    rec = SubscriptionRecord(subscription_id=sid, name=name.strip(), url=url.strip(), enabled=True)
    return [s for s in subs if s.subscription_id != sid] + [rec]


def parse_subscription_payload(text: str) -> list[str]:
    raw = (text or "").strip()
    if not raw:
        return []

    payload = raw
    # If no scheme-like lines detected, try base64 decode first.
    if not any(x in raw for x in ("vless://", "vmess://", "trojan://", "ss://")):
        try:
            b = raw.encode("utf-8", errors="replace")
            b += b"=" * (-len(b) % 4)
            payload = base64.b64decode(b, validate=False).decode("utf-8", errors="replace")
        except Exception:
            payload = raw

    links: list[str] = []
    for ln in payload.splitlines():
        s = ln.strip()
        if not s or s.startswith("#") or s.startswith("//"):
            continue
        if any(s.startswith(p) for p in ("vless://", "vmess://", "trojan://", "ss://")):
            links.append(s)
    return links


def download_subscription_text(url: str, *, timeout_s: float = 20.0) -> str:
    req = urllib.request.Request(url=url, headers={"User-Agent": "DedZapret/1.0"}, method="GET")
    with urllib.request.urlopen(req, timeout=timeout_s) as r:  # nosec - user action URL
        return r.read().decode("utf-8", errors="replace")


def merge_subscription_nodes(
    *,
    current_nodes: list[SingBoxNode],
    links: list[str],
) -> tuple[list[SingBoxNode], dict[str, int]]:
    by_id = {n.node_id: n for n in current_nodes}
    imported = 0
    skipped = 0
    errors = 0
    for link in links:
        try:
            n = import_node_from_link(link)
            if n.node_id in by_id:
                skipped += 1
            else:
                by_id[n.node_id] = n
                imported += 1
        except Exception:
            errors += 1
    return list(by_id.values()), {"imported": imported, "skipped": skipped, "errors": errors}


def masked_subscription_label(s: SubscriptionRecord) -> str:
    return f"{s.name} ({mask_secrets_text(s.url)})"
