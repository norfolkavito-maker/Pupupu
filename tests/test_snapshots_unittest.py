import unittest
from pathlib import Path
import tempfile


from app.zapret_manager.core.snapshots import create_snapshot


class TestSnapshots(unittest.TestCase):
    def test_creates_snapshot_dir(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f = root / "a.txt"
            f.write_text("hello", encoding="utf-8")
            out = create_snapshot(snapshots_root=root / "snapshots", reason="test", paths=[f])
            self.assertTrue(out.exists())
            self.assertTrue((out / "a.txt").exists())


if __name__ == "__main__":
    unittest.main()
