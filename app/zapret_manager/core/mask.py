
import re
from typing import Any, Dict, List, Union


# Regex patterns for various secrets
# VLESS/VMESS/TROJAN/SS links (simplified for common patterns, might need refinement)
PROXY_LINK_PATTERN = re.compile(
    r"((vless|vmess|trojan|ss)://[^\s]+)", re.IGNORECASE
)
# Generic tokens/passwords in query parameters or headers
GENERIC_SECRET_PATTERN = re.compile(
    r"([?&](?:token|password|pass|key|secret)=[^&\s]+)|(Authorization: Bearer [^\s]+)",
    re.IGNORECASE,
)
# UUID-like credentials (e.g., node UUIDs)
UUID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)


def mask_secret(value: str, mask_char: str = "*", reveal_chars: int = 4) -> str:
    """Masks a secret string, revealing only a few characters at the beginning and end."""
    if not isinstance(value, str) or not value:
        return value

    if len(value) <= reveal_chars * 2:
        return mask_char * len(value)

    start = value[:reveal_chars]
    end = value[-reveal_chars:]
    return f"{start}{mask_char * (len(value) - 2 * reveal_chars)}{end}"


def mask_text(text: str) -> str:
    """Applies various masking patterns to a given text."""
    if not isinstance(text, str):
        return text

    masked_text = text

    # Mask proxy links
    masked_text = PROXY_LINK_PATTERN.sub(
        lambda m: mask_secret(m.group(0), reveal_chars=5), masked_text
    )

    # Mask generic secrets (query params, auth headers)
    masked_text = GENERIC_SECRET_PATTERN.sub(
        lambda m: mask_secret(m.group(0), reveal_chars=3), masked_text
    )

    # Mask UUIDs
    masked_text = UUID_PATTERN.sub(lambda m: mask_secret(m.group(0)), masked_text)

    return masked_text


def mask_mapping(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively masks secrets in string values within a dictionary."""
    if not isinstance(data, dict):
        return data

    masked_data = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Apply masking to string values
            masked_data[key] = mask_text(value)
        elif isinstance(value, dict):
            # Recurse into nested dictionaries
            masked_data[key] = mask_mapping(value)
        elif isinstance(value, list):
            # Recurse into lists (e.g., list of dicts or strings)
            masked_data[key] = [
                mask_mapping(item) if isinstance(item, dict) else mask_text(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            # Keep other types as is
            masked_data[key] = value
    return masked_data
