from __future__ import annotations

import base64
import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

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


def parse_subscription_payload_detailed(text: str) -> tuple[list[str], dict[str, int], str]:
    """Parse subscription payload and return (links, counters, last_error).

    Supported best-effort formats:
    - plain list of links
    - base64 list of links
    - Clash YAML (limited): imports Shadowsocks proxies only
    - sing-box JSON: imports outbounds of type shadowsocks/trojan/vless (minimal)
    """

    raw = (text or "").strip()
    if not raw:
        return ([], {"unsupported_lines": 0}, "empty subscription payload")

    # 1) Try sing-box JSON
    if raw.lstrip().startswith("{"):
        try:
            obj = json.loads(raw)
            links, unsupported = _parse_singbox_json_outbounds(obj)
            if links:
                return (links, {"unsupported_lines": unsupported}, "")
            return ([], {"unsupported_lines": unsupported}, "no supported outbounds in sing-box json")
        except Exception as e:
            # Fallthrough to other formats
            last_err = f"failed to parse sing-box json: {e}"

    else:
        last_err = ""

    # 2) Try Clash YAML (best-effort, no external yaml dependency)
    if "proxies:" in raw and "proxy-groups:" in raw:
        try:
            links, unsupported = _parse_clash_yaml_shadowsocks(raw)
            if links:
                return (links, {"unsupported_lines": unsupported}, "")
            return ([], {"unsupported_lines": unsupported}, "no supported proxies in clash yaml")
        except Exception as e:
            last_err = f"failed to parse clash yaml: {e}"

    # 3) Plain/base64 list of links (backward compatible)
    links = parse_subscription_payload(raw)
    if links:
        # Count non-empty non-comment lines that were not recognized as links.
        unsupported = 0
        for ln in _try_base64_decode_if_needed(raw).splitlines():
            s = ln.strip()
            if not s or s.startswith("#") or s.startswith("//"):
                continue
            if not any(s.startswith(p) for p in ("vless://", "vmess://", "trojan://", "ss://")):
                unsupported += 1
        return (links, {"unsupported_lines": unsupported}, "")

    # Nothing recognized
    return ([], {"unsupported_lines": 0}, last_err or "unsupported subscription format")


def _try_base64_decode_if_needed(raw: str) -> str:
    """Decode base64 subscription payload if it does not look like link list."""
    if any(x in raw for x in ("vless://", "vmess://", "trojan://", "ss://")):
        return raw
    try:
        b = raw.encode("utf-8", errors="replace")
        b += b"=" * (-len(b) % 4)
        return base64.b64decode(b, validate=False).decode("utf-8", errors="replace")
    except Exception:
        return raw


def _parse_clash_yaml_shadowsocks(text: str) -> tuple[list[str], int]:
    """Parse a subset of Clash YAML: Shadowsocks proxies only.

    We intentionally avoid external YAML libraries.
    """
    links: list[str] = []
    unsupported = 0

    in_proxies = False
    cur: dict[str, str] = {}
    cur_indent = None

    def flush() -> None:
        nonlocal cur, unsupported
        if not cur:
            return
        t = (cur.get("type") or "").strip().lower()
        if t != "ss":
            unsupported += 1
            cur = {}
            return
        server = (cur.get("server") or "").strip()
        port = (cur.get("port") or "").strip()
        cipher = (cur.get("cipher") or cur.get("method") or "").strip()
        password = (cur.get("password") or "").strip()
        name = (cur.get("name") or "ss").strip()
        if not (server and port.isdigit() and cipher and password):
            unsupported += 1
            cur = {}
            return

        # Build ss://method:password@server:port#name (import_node_from_link supports this form)
        user = quote(cipher, safe="")
        pwd = quote(password, safe="")
        frag = quote(name, safe="")
        links.append(f"ss://{user}:{pwd}@{server}:{int(port)}#{frag}")
        cur = {}

    for ln in text.splitlines():
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        if ln.startswith("proxies:"):
            in_proxies = True
            continue
        if in_proxies and (ln.startswith("proxy-groups:") or ln.startswith("rules:")):
            flush()
            break
        if not in_proxies:
            continue

        # Detect new item: "  - name: ..."
        stripped = ln.lstrip(" ")
        indent = len(ln) - len(stripped)
        if stripped.startswith("-"):
            # new item begins
            flush()
            cur_indent = indent
            stripped = stripped[1:].strip()
            if ":" in stripped:
                k, v = stripped.split(":", 1)
                cur[k.strip()] = v.strip().strip('"').strip("'")
            continue

        # key/value continuation inside current item
        if cur_indent is not None and indent <= cur_indent:
            # outside of current item
            flush()
            cur_indent = None
            continue

        if ":" in stripped:
            k, v = stripped.split(":", 1)
            cur[k.strip()] = v.strip().strip('"').strip("'")

    flush()
    return links, unsupported


def _parse_singbox_json_outbounds(obj: Any) -> tuple[list[str], int]:
    links: list[str] = []
    unsupported = 0

    outbounds = obj.get("outbounds") if isinstance(obj, dict) else None
    if not isinstance(outbounds, list):
        return ([], 0)

    for ob in outbounds:
        if not isinstance(ob, dict):
            unsupported += 1
            continue
        t = str(ob.get("type") or "").lower()
        tag = str(ob.get("tag") or ob.get("name") or t or "node")
        server = str(ob.get("server") or "")
        port = int(ob.get("server_port") or ob.get("port") or 0)
        if not server or not port:
            unsupported += 1
            continue

        if t == "shadowsocks":
            method = str(ob.get("method") or "")
            password = str(ob.get("password") or "")
            if not method or not password:
                unsupported += 1
                continue
            links.append(
                f"ss://{quote(method, safe='')}:{quote(password, safe='')}@{server}:{port}#{quote(tag, safe='')}"
            )
            continue

        if t == "trojan":
            password = str(ob.get("password") or "")
            if not password:
                unsupported += 1
                continue
            links.append(f"trojan://{quote(password, safe='')}@{server}:{port}#{quote(tag, safe='')}")
            continue

        if t == "vless":
            uuid = str(ob.get("uuid") or ob.get("id") or "")
            if not uuid:
                unsupported += 1
                continue
            links.append(f"vless://{quote(uuid, safe='')}@{server}:{port}#{quote(tag, safe='')}")
            continue

        unsupported += 1

    return (links, unsupported)


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
    unsupported_lines = 0
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
    return list(by_id.values()), {
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "unsupported_lines": unsupported_lines,
    }


def masked_subscription_label(s: SubscriptionRecord) -> str:
    return f"{s.name} ({mask_secrets_text(s.url)})"
