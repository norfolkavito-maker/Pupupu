
import pytest
from app.zapret_manager.core.mask import mask_secret, mask_text, mask_mapping


def test_mask_secret_default_behavior():
    assert mask_secret("1234567890") == "1234**7890"
    assert mask_secret("short") == "*****"
    assert mask_secret("a") == "*"
    assert mask_secret("") == ""
    assert mask_secret(None) is None


def test_mask_secret_custom_reveal_chars():
    assert mask_secret("1234567890", reveal_chars=2) == "12**90"
    assert mask_secret("1234567890", reveal_chars=0) == "**********"
    assert mask_secret("1234567890", reveal_chars=5) == "1234567890" # reveal all or more


def test_mask_text_proxy_links():
    vless_link = "vless://user:pass@host:port?param=value#name"
    vmess_link = "vmess://eyJ2..."
    trojan_link = "trojan://user:pass@host:port#name"
    ss_link = "ss://aes-128-gcm:pass@host:port#name"

    assert "vless://u***h#name" in mask_text(vless_link)
    assert "vmess://e****S" in mask_text(vmess_link) # Check if it masks part of base64
    assert "trojan://u***h#name" in mask_text(trojan_link)
    assert "ss://a***h#name" in mask_text(ss_link)


def test_mask_text_generic_secrets():
    text_with_token = "url?token=supersecret&user=test"
    text_with_password = "api.com/path?password=mypass&id=1"
    text_with_auth_header = "GET / HTTP/1.1\r\nAuthorization: Bearer mytoken123\r\n"

    assert "url?token=s***t&user=test" in mask_text(text_with_token)
    assert "api.com/path?password=m***s&id=1" in mask_text(text_with_password)
    assert "Authorization: Bearer m***3" in mask_text(text_with_auth_header)


def test_mask_text_uuid():
    uuid_str = "Node ID: 123e4567-e89b-12d3-a456-426614174000"
    assert "Node ID: 123e****4000" in mask_text(uuid_str)


def test_mask_text_mixed_secrets():
    mixed_text = f"Check this: vless://abcde:fghij@klmno:1234#pqrst and token=abcdefghij"
    masked_text = mask_text(mixed_text)
    assert "vless://a***t and token=a***j" in masked_text


def test_mask_mapping_simple_dict():
    data = {
        "url": "https://example.com/?token=secret123",
        "node_id": "123e4567-e89b-12d3-a456-426614174000",
        "username": "testuser",
    }
    masked_data = mask_mapping(data)
    assert masked_data["url"].startswith("https://example.com/?token=s***3")
    assert masked_data["node_id"].startswith("123e****4000")
    assert masked_data["username"] == "testuser"


def test_mask_mapping_nested_dict():
    data = {
        "server": {
            "address": "1.1.1.1",
            "config": {"vless": "vless://user@host:port"},
        },
        "auth_header": "Authorization: Bearer mytoken",
    }
    masked_data = mask_mapping(data)
    assert masked_data["server"]["address"] == "1.1.1.1"
    assert "vless://u***t" in masked_data["server"]["config"]["vless"]
    assert "Authorization: Bearer m***n" in masked_data["auth_header"]


def test_mask_mapping_list_of_strings():
    data = {"logs": ["user logged in", "vless://link@host:port", "error occurred"]}
    masked_data = mask_mapping(data)
    assert masked_data["logs"][0] == "user logged in"
    assert "vless://l***t" in masked_data["logs"][1]
    assert masked_data["logs"][2] == "error occurred"


def test_mask_mapping_list_of_dicts():
    data = {
        "nodes": [
            {"id": 1, "link": "vmess://abc"},
            {"id": 2, "token": "secrettoken123"},
        ]
    }
    masked_data = mask_mapping(data)
    assert masked_data["nodes"][0]["id"] == 1
    assert "vmess://a***c" in masked_data["nodes"][0]["link"]
    assert masked_data["nodes"][1]["id"] == 2
    assert "secrettoken123" not in masked_data["nodes"][1]["token"]
    assert "s***3" in masked_data["nodes"][1]["token"]


def test_mask_mapping_non_string_values():
    data = {"number": 123, "boolean": True, "list": [1, 2, 3]}
    masked_data = mask_mapping(data)
    assert masked_data == data
