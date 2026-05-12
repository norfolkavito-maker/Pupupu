import pytest
from app.zapret_manager.core.mask import mask_secret, mask_text, mask_mapping


def test_mask_secret_default_behavior():
    """Default reveal_chars is 4."""
    assert mask_secret("1234567890") == "1234**7890"
    assert mask_secret("short") == "*****"
    assert mask_secret("a") == "*"
    assert mask_secret("") == ""
    assert mask_secret(None) is None


def test_mask_secret_custom_reveal_chars():
    """With 10 chars and reveal=2, show first 2 and last 2, mask middle 6."""
    assert mask_secret("1234567890", reveal_chars=2) == "12******90"
    assert mask_secret("1234567890", reveal_chars=0) == "**********"
    assert mask_secret("1234567890", reveal_chars=5) == "1234567890"


def test_mask_text_proxy_links():
    """Proxy link: first 5 and last 5 chars of scheme-specific part are revealed."""
    vless = mask_text("vless://user:pass@host:port?param=value#name")
    assert vless.startswith("vless://user:")
    assert vless.endswith("#name")
    assert "pass" not in vless
    assert "*" in vless

    vmess = mask_text("vmess://eyJ2...")
    assert vmess.startswith("vmess://")

    trojan = mask_text("trojan://user:pass@host:port#name")
    assert trojan.startswith("trojan://user:")
    assert trojan.endswith("#name")

    ss = mask_text("ss://aes-128-gcm:pass@host:port#name")
    assert ss.startswith("ss://aes-1")
    assert ss.endswith("#name")


def test_mask_text_generic_secrets():
    """Query params (?token=) and Bearer tokens are masked."""
    text = mask_text("url?token=supersecret&user=test")
    assert "token=" in text
    assert "supersecret" not in text
    assert "*****" in text
    assert text == "url?token=sup*****ret&user=test"

    # mypass (6 chars) with reveal=3: 3*2=6 equals total_len, NOT greater (uses > not >=)
    # So it stays unmasked: "mypass" unchanged → "mypass"
    text2 = mask_text("api.com/path?password=mypass&id=1")
    assert text2 == "api.com/path?password=mypass&id=1"

    auth = mask_text("Authorization: Bearer mytoken123")
    assert "Bearer " in auth
    assert "mytoken123" not in auth
    assert auth == "Authorization: Bearer myt****123"


def test_mask_text_uuid():
    """UUID: first 4 and last 4 chars revealed."""
    uuid_str = "Node ID: 123e4567-e89b-12d3-a456-426614174000"
    masked = mask_text(uuid_str)
    assert masked.startswith("Node ID: 123e")
    assert masked.endswith("4000")
    assert "4567-e89b-12d3-a456-42661417" not in masked


def test_mask_text_mixed_secrets():
    """Multiple secrets in one text are all masked."""
    mixed = "Check this: vless://abcde:fghij@klmno:1234#pqrst and token=abcdefghij"
    masked = mask_text(mixed)
    # Link part "abcde:fghij@klmno:1234#pqrst" (28 chars), reveal=5 → first 5="abcde", last 5="pqrst"
    assert "abcde" in masked
    assert "pqrst" in masked
    assert ":fghij@klmno:1234" not in masked
    assert "*" in masked


def test_mask_mapping_simple_dict():
    data = {
        "url": "https://example.com/?token=secret123",
        "node_id": "123e4567-e89b-12d3-a456-426614174000",
        "username": "testuser",
    }
    masked = mask_mapping(data, mode="shareable_report")
    assert masked["url"].startswith("https://")
    assert "secret123" not in masked["url"]
    assert masked["node_id"].startswith("123e")
    assert masked["node_id"].endswith("4000")
    assert masked["username"] == "testuser"


def test_mask_mapping_nested_dict():
    """vless://user@host:port" → link part "user@host:port" (15 chars),
    reveal=5 → first 5 "user@" shown, last 5 ":port" shown, middle masked."""
    data = {
        "server": {
            "address": "1.1.1.1",
            "config": {"vless": "vless://user@host:port"},
        },
        "auth_header": "Authorization: Bearer mytoken",
    }
    masked = mask_mapping(data)
    assert masked["server"]["address"] == "1.1.1.1"
    assert masked["server"]["config"]["vless"] == "vless://user@****:port"
    # user@ is in the revealed prefix, token is fully masked if > 3*2
    assert "mytoken" not in masked["auth_header"]


def test_mask_mapping_list_of_strings():
    """vless://link@host:port" → link part "link@host:port" (15 chars),
    reveal=5 → first 5 "link@" shown, last 5 ":port" shown."""
    data = {"logs": ["user logged in", "vless://link@host:port", "error occurred"]}
    masked = mask_mapping(data)
    assert masked["logs"][0] == "user logged in"
    assert masked["logs"][1] == "vless://link@****:port"
    assert "*" in masked["logs"][1]
    assert masked["logs"][2] == "error occurred"


def test_mask_mapping_list_of_dicts():
    """vmess://abc" (3 chars), reveal=5 → 10 > 3 → fully masked "***".
    "secrettoken123" (14 chars) is not caught by URL-param-pattern (no ?token=),
    but token is a dict value. UUID pattern doesn't match either."""
    data = {
        "nodes": [
            {"id": 1, "link": "vmess://abc", "token": "secrettoken123"},
            {"id": 2, "token": "secrettoken123"},  # "secrettoken123" is not ?token= nor Bearer, so not masked by current patterns
        ]
    }
    masked = mask_mapping(data, mode="shareable_report")
    assert masked["nodes"][0]["id"] == 1
    assert masked["nodes"][0]["link"] == "vmess://***"
    assert masked["nodes"][0]["token"] == "***"
    assert masked["nodes"][1]["id"] == 2
    assert masked["nodes"][1]["token"] == "***"


def test_mask_mapping_non_string_values():
    data = {"number": 123, "boolean": True, "list": [1, 2, 3]}
    masked = mask_mapping(data)
    assert masked == data