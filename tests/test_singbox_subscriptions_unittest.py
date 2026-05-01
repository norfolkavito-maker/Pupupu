import base64
import unittest

from app.zapret_manager.core.singbox.subscriptions import (
    merge_subscription_nodes,
    parse_subscription_payload,
    parse_subscription_payload_detailed,
)
from app.zapret_manager.core.singbox.nodes import SingBoxNode


class TestSingBoxSubscriptions(unittest.TestCase):
    def test_parse_plain_text_links(self):
        raw = """
# comment
vless://id@h1:443#n1

trojan://pwd@h2:443#n2
"""
        links = parse_subscription_payload(raw)
        self.assertEqual(len(links), 2)

    def test_parse_base64_payload(self):
        raw_links = "vless://id@h1:443#n1\nss://YWVzLTI1Ni1nY206cGFzczFAaDg6NDQz#n2\n"
        b64 = base64.b64encode(raw_links.encode("utf-8")).decode("ascii")
        links = parse_subscription_payload(b64)
        self.assertEqual(len(links), 2)


    def test_parse_clash_yaml_ss(self):
        raw = """
port: 7890
proxies:
  - name: test
    type: ss
    server: example.com
    port: 443
    cipher: aes-256-gcm
    password: secret
proxy-groups:
  - name: auto
    type: select
    proxies:
      - test
rules:
  - MATCH,auto
"""
        links, counters, err = parse_subscription_payload_detailed(raw)
        self.assertTrue(links)
        self.assertEqual(err, "")
        self.assertIn("ss://", links[0])
        self.assertIn("example.com:443", links[0])


    def test_parse_singbox_json_outbounds(self):
        raw = """{
  "outbounds": [
    {"type": "shadowsocks", "tag": "ss1", "server": "h1", "server_port": 443, "method": "aes-256-gcm", "password": "p"}
  ]
}"""
        links, counters, err = parse_subscription_payload_detailed(raw)
        self.assertEqual(err, "")
        self.assertEqual(len(links), 1)
        self.assertTrue(links[0].startswith("ss://"))


    def test_imported_zero_returns_error(self):
        links, counters, err = parse_subscription_payload_detailed("not a subscription")
        self.assertEqual(links, [])
        self.assertTrue(err)


    def test_merge_import_and_skips(self):
        # one existing node
        existing = SingBoxNode(
            node_id="abc",
            name="n1",
            protocol="vless",
            server="h1",
            port=443,
            raw="vless://id@h1:443#n1",
            extra={},
        )
        nodes, stats = merge_subscription_nodes(current_nodes=[existing], links=["vless://id@h1:443#n1"])
        # our merge dedups by node_id; existing is forced "abc" so it will import as new
        self.assertEqual(stats.get("imported"), 1)


if __name__ == "__main__":
    unittest.main()
