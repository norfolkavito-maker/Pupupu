from __future__ import annotations

import re
from typing import Any, Dict, List, Union, Optional


re_IGNORECASE = re.IGNORECASE


# Regex patterns for various secrets

# Proxy links: capture protocol (group 1) and the rest of the link (group 2)
PROXY_LINK_PATTERN = re.compile(
    r"(vless|vmess|trojan|ss|http|https)://([^\s]+)", re_IGNORECASE
)

# Generic secrets: capture prefix (group 1 & 2) and value (group 2 & 4)
GENERIC_SECRET_PATTERN = re.compile(
    r"([?&](?:token|password|pass|key|secret|auth|authorization)=)([^&\s]+)|(Authorization: Bearer )([^\s]+)",
    re_IGNORECASE,
)

# UUID-like credentials: capture the full UUID string (group 1)
UUID_PATTERN = re.compile(
    r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b",
    re_IGNORECASE,
)


def mask_secret(value: str, mask_char: str = "*", reveal_chars: int = 4) -> str:
    """Masks a secret string, revealing only a few characters at the beginning and end."""
    if not isinstance(value, str) or not value:
        return value

    total_len = len(value)
    if reveal_chars * 2 > total_len:
        # Not enough characters to show both start and end; mask everything
        return mask_char * total_len

    start = value[:reveal_chars]
    end = value[total_len - reveal_chars:]
    masked_len = total_len - (reveal_chars * 2)
    return f"{start}{mask_char * masked_len}{end}"


def mask_text(text: str) -> str:
    """Applies various masking patterns to a given text."""
    if not isinstance(text, str):
        return text

    masked_text = text

    # Mask proxy links: group 1 is type, group 2 is the entire rest of the link
    masked_text = PROXY_LINK_PATTERN.sub(
        lambda m: f"{m.group(1)}://{mask_secret(m.group(2), reveal_chars=5)}", masked_text
    )

    # Mask generic secrets: group 1 & 2 for query param, group 3 & 4 for auth header
    masked_text = GENERIC_SECRET_PATTERN.sub(
        lambda m: (m.group(1) + mask_secret(m.group(2), reveal_chars=3)) if m.group(1) else \
                   (m.group(3) + mask_secret(m.group(4), reveal_chars=3)),
        masked_text,
    )

    # Mask UUIDs: group 1 is the full UUID
    masked_text = UUID_PATTERN.sub(lambda m: mask_secret(m.group(1), reveal_chars=4), masked_text)

    return masked_text


SENSITIVE_KEYS = {
    "password", "pass", "passwd", "pwd",
    "secret", "token", "access_token", "refresh_token",
    "api_key", "key", "private_key",
    "uuid", "raw", "subscription", "subscription_url",
}

def mask_mapping(data: Dict[str, Any], mode: Optional[str] = None) -> Dict[str, Any]:
    """Recursively masks secrets in string values within a dictionary."""
    if mode == "local_debug":
        return data

    if not isinstance(data, dict):
        return data

    masked_data = {}
    for key, value in data.items():
        key_l = str(key).lower()
        
        if isinstance(value, str):
            # Mask sensitive keys completely
            if key_l in SENSITIVE_KEYS:
                masked_data[key] = "***"
            else:
                # Apply masking to non-sensitive string values
                masked_data[key] = mask_secrets(value, mode=mode)
        elif isinstance(value, dict):
            # Recurse into nested dictionaries
            masked_data[key] = mask_mapping(value, mode=mode)
        elif isinstance(value, list):
            # Recurse into lists (e.g., list of dicts or strings)
            masked_data[key] = [
                mask_mapping(item, mode=mode) if isinstance(item, dict) else mask_secrets(item, mode=mode) if isinstance(item, str) else item
                for item in value
            ]
        else:
            # Keep other types as is
            masked_data[key] = value
    return masked_data


def mask_secrets_text(text: str, mode: Optional[str] = None) -> str:
    """Alias for mask_secrets for backward compatibility."""
    return mask_secrets(text, mode=mode)


def mask_text_for_shareable_report(text: str) -> str:
    """Masks text for shareable reports (GitHub issues, public sharing)."""
    return mask_text(text)


def mask_text_for_local_debug(text: str) -> str:
    """Preserves text for local debug mode (may contain sensitive data)."""
    return text


def mask_secrets(text: str, mode: Optional[str] = None) -> str:
    """
    Masks secrets in text based on explicit mode.
    
    Args:
        text: Text to mask
        mode: 'shareable_report' (default) or 'local_debug'
    """
    if mode == "local_debug":
        return mask_text_for_local_debug(text)
    else:  # Default to shareable_report mode
        return mask_text_for_shareable_report(text)