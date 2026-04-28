import unittest
from pathlib import Path
import tempfile


from app.zapret_manager.core.singbox.nodes import import_node_from_link, save_nodes, load_nodes


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
            # but raw link must never be stored unmasked.
            self.assertNotIn("vless://123e4567-e89b-12d3-a456-426614174000@", txt)
            self.assertIn("vless://***@", txt)
            nodes2 = load_nodes(p)
            self.assertEqual(len(nodes2), 1)


if __name__ == "__main__":
    unittest.main()
