import unittest
from pathlib import Path
from types import SimpleNamespace


from app.zapret_manager.features.runtime_assets import ensure_base_lists


class TestRuntimeAssetsRepair(unittest.TestCase):
    def test_repair_creates_lists_dir(self):
        root = Path(".tmp_test_repair").resolve()
        # simulate portable layout
        lists_dir = root / "DedZapretData" / "data" / "lists"
        if lists_dir.exists():
            # cleanup from previous run
            for p in lists_dir.glob("*"):
                p.unlink()
        ctx = SimpleNamespace(paths=SimpleNamespace(lists_dir=lists_dir))
        items = ensure_base_lists(ctx)
        self.assertTrue(lists_dir.exists())
        # at minimum lists_dir entry exists
        self.assertTrue(any(i.name == "lists_dir" for i in items))


if __name__ == "__main__":
    unittest.main()
