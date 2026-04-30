import tempfile
import unittest
from pathlib import Path

from app.zapret_manager.core.current_state import default_current_state, save_current_state
from app.zapret_manager.core.singbox.health import singbox_health_summary


class TestSingBoxHealth(unittest.TestCase):
    def test_health_summary_shape(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "current.json"
            st = default_current_state()
            save_current_state(p, st)
            h = singbox_health_summary(p)
            self.assertIn("running", h)
            self.assertIn("ports", h)
            self.assertIn("ok", h)


if __name__ == "__main__":
    unittest.main()
