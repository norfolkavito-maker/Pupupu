import unittest
from pathlib import Path
import tempfile


from app.zapret_manager.core.current_state import load_current_state, save_current_state, CurrentState


class TestCurrentState(unittest.TestCase):
    def test_creates_default(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "current.json"
            st = load_current_state(p)
            self.assertTrue(p.exists())
            self.assertIn("singbox", st.processes)

    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "current.json"
            st = load_current_state(p)
            st.active_singbox_node_id = "node1"
            save_current_state(p, st)
            st2 = load_current_state(p)
            self.assertEqual(st2.active_singbox_node_id, "node1")


if __name__ == "__main__":
    unittest.main()
