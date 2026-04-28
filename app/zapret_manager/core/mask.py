from __future__ import annotations

import base64
import json
import re
from dataclasses import is_dataclass, asdict
from typing import Any


_UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)


def _mask_uuid(s: str) -> str:
    def repl(m: re.Match[str]) -> str:
        u = m.group(0)
        return u[:8] + "-****-****-****-" + u[-4:]

    return _UUID_RE.sub(repl, s)


def _mask_url_credentials(s: str) -> str:
    # user:pass@host
    s = re.sub(r"(://[^/\s:@]+):([^@/\s]+)@", r"\1:***@", s)
    return s


def _mask_query_params(s: str) -> str:
    # Mask common secret query params.
    for k in [
        "uuid",
        "password",
        "pass",
        "token",
        "key",
        "private_key",
        "pk",
        "secret",
        "sni",
        "host",
        "server",
        "address",
    ]:
        s = re.sub(
            rf"([?&]{re.escape(k)}=)([^&#\s]+)",
            r"\1***",
            s,
            flags=re.IGNORECASE,
        )
    return s


def _mask_vless_like_links(s: str) -> str:
    # vless://UUID@server:port?...
    s = re.sub(r"\b(vless|vmess|trojan)://([^@/\s]+)@", r"\1://***@", s, flags=re.IGNORECASE)
    # ss://BASE64 or ss://method:pass@host:port
    s = re.sub(r"\bss://([^@/\s]+)@", r"ss://***@", s, flags=re.IGNORECASE)
    return s


def _mask_hostnames(s: str) -> str:
    # Best-effort masking of IPs and hostnames inside links/configs.
    # IP v4
    s = re.sub(r"\b(\d{1,3}\.){3}\d{1,3}\b", "***.***.***.***", s)
    # Hostnames (keep TLD)
    s = re.sub(
        r"\b([a-zA-Z0-9-]{2,})\.([a-zA-Z]{2,})\b",
        lambda m: (m.group(1)[:2] + "***." + m.group(2)) if len(m.group(1)) > 2 else ("***." + m.group(2)),
        s,
    )
    return s


def mask_secrets_text(text: str) -> str:
    if not text:
        return text
    s = str(text)
    s = _mask_uuid(s)
    s = _mask_url_credentials(s)
    s = _mask_query_params(s)
    s = _mask_vless_like_links(s)
    # Keep host masking last to not break earlier regexes.
    s = _mask_hostnames(s)
    return s


def mask_secrets(obj: Any) -> Any:
    """Recursively mask secrets in dict/list/str/dataclass.

    Rules:
    - Do not preserve raw VLESS/VMess/Trojan/SS links.
    - Hide UUID/password/private keys/subscription URLs.
    """
    if obj is None:
        return None

    if isinstance(obj, str):
        return mask_secrets_text(obj)

    if isinstance(obj, bytes):
        # Avoid binary blobs in reports; represent in a stable masked way.
        try:
            s = obj.decode("utf-8", errors="replace")
            return mask_secrets_text(s)
        except Exception:
            return "<bytes>"

    if isinstance(obj, (int, float, bool)):
        return obj

    if is_dataclass(obj):
        return mask_secrets(asdict(obj))

    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            ks = str(k)
            # Key-based masking
            if ks.lower() in {
                "password",
                "pass",
                "uuid",
                "token",
                "secret",
                "private_key",
                "subscription",
                "subscription_url",
                "url",
                "link",
                "server",
                "address",
            }:
                out[ks] = "***"
            else:
                out[ks] = mask_secrets(v)
        return out

    if isinstance(obj, list):
        return [mask_secrets(x) for x in obj]

    # Try JSON strings that may contain configs.
    try:
        if isinstance(obj, str) and obj.strip().startswith("{"):
            data = json.loads(obj)
            return json.dumps(mask_secrets(data), ensure_ascii=False)
    except Exception:
        pass

    return mask_secrets_text(str(obj))
