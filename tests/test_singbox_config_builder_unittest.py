import unittest


from app.zapret_manager.core.singbox.nodes import SingBoxNode
from app.zapret_manager.core.singbox.config_builder import build_config, SingBoxBuildOptions


class TestSingBoxConfigBuilder(unittest.TestCase):
    def test_inbounds_ports(self):
        node = SingBoxNode(
            node_id="id",
            name="n",
            protocol="vless",
            server="example.com",
            port=443,
            raw="vless://***",
            extra={},
            uuid="123e4567-e89b-12d3-a456-426614174000",
        )
        cfg = build_config(node=node, opt=SingBoxBuildOptions())
        inb = {x["tag"]: x for x in cfg["inbounds"]}
        self.assertEqual(inb["socks-in"]["listen_port"], 2080)
        self.assertEqual(inb["mixed-in"]["listen_port"], 2081)

    def test_ss_requires_password_method(self):
        node = SingBoxNode(
            node_id="id",
            name="n",
            protocol="ss",
            server="example.com",
            port=443,
            raw="ss://***",
            extra={},
        )
        with self.assertRaises(ValueError):
            build_config(node=node, opt=SingBoxBuildOptions())


if __name__ == "__main__":
    unittest.main()
