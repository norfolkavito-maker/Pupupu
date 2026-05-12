import unittest
from pathlib import Path
import tempfile


from app.zapret_manager.core.singbox.nodes import import_node_from_link, save_nodes, load_nodes
from app.zapret_manager.core.singbox.config_builder import build_config, SingBoxBuildOptions


class TestSingBoxNodes(unittest.TestCase):
    def test_import_vless_minimal(self):
        n = import_node_from_link("vless://123e4567-e89b-12d3-a456-426614174000@host.example:443#my")
        self.assertEqual(n.protocol, "vless")
        self.assertEqual(n.port, 443)
        self.assertTrue(n.node_id)

    def test_save_masks_raw(self):
        n = import_node_from_link("vless://123e4567-e89b-12d3-a456-426614174000@host.example:443#my")
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "nodes.json"
            save_nodes(p, [n])
            txt = p.read_text(encoding="utf-8")
            # nodes.json is local storage and may contain secrets (uuid/password),
            # but raw link should never be stored unmasked.
            self.assertNotIn("vless://123e4567-e89b-12d3-a456-426614174000@", txt)
            self.assertIn("vless://123e4", txt)  # First 5 chars shown
            self.assertIn("43#my", txt)  # Last 5 chars shown
            nodes2 = load_nodes(p)
            self.assertEqual(len(nodes2), 1)

    def test_save_load_preserves_working_node(self):
        """Test that save/load cycle preserves node functionality for config rebuild."""
        # Import VLESS node
        original = import_node_from_link("vless://123e4567-e89b-12d3-a456-426614174000@host.example:443#my")
        
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "nodes.json"
            
            # Save node to local storage
            save_nodes(p, [original])
            
            # Load node back from local storage
            loaded_nodes = load_nodes(p)
            self.assertEqual(len(loaded_nodes), 1)
            loaded = loaded_nodes[0]
            
            # Verify essential fields for config rebuild are preserved
            self.assertEqual(loaded.protocol, original.protocol)
            self.assertEqual(loaded.server, original.server)
            self.assertEqual(loaded.port, original.port)
            self.assertEqual(loaded.uuid, original.uuid)
            self.assertEqual(loaded.password, original.password)
            self.assertEqual(loaded.method, original.method)
            self.assertEqual(loaded.name, original.name)
            
            # Verify we can build sing-box config from loaded node
            opt = SingBoxBuildOptions()
            config = build_config(node=loaded, opt=opt)
            
            # Verify config contains expected server/port
            outbounds = config.get("outbounds", [])
            proxy_outbound = None
            for outbound in outbounds:
                if outbound.get("tag") == "proxy":
                    proxy_outbound = outbound
                    break
            
            self.assertIsNotNone(proxy_outbound, "Proxy outbound not found in config")
            self.assertEqual(proxy_outbound["server"], original.server)
            self.assertEqual(proxy_outbound["server_port"], original.port)
            if original.protocol == "vless":
                self.assertEqual(proxy_outbound["uuid"], original.uuid)


if __name__ == "__main__":
    unittest.main()
