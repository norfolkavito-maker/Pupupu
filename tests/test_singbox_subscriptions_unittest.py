import base64
import unittest

from app.zapret_manager.core.singbox.subscriptions import parse_subscription_payload


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


if __name__ == "__main__":
    unittest.main()
