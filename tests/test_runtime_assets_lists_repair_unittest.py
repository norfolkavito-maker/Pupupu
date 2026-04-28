import unittest
from pathlib import Path
from unittest.mock import MagicMock
import tempfile


from app.zapret_manager.features.runtime_assets import ensure_base_lists


class TestRuntimeAssetsListsRepair(unittest.TestCase):
    def _make_ctx(self, lists_dir: Path) -> MagicMock:
        ctx = MagicMock()
        ctx.paths = MagicMock()
        ctx.paths.lists_dir = lists_dir
        return ctx

    def test_optional_user_files_created_empty(self):
        with tempfile.TemporaryDirectory() as td:
            lists_dir = Path(td) / "lists"
            ctx = self._make_ctx(lists_dir)

            items = ensure_base_lists(ctx)

            # optional files should exist now
            for name in [
                "list-general-user.txt",
                "list-exclude-user.txt",
                "ipset-exclude-user.txt",
                # ipset placeholders for preflight compatibility
                "ipset-exclude.txt",
                "list-ipset-exclude.txt",
                "ipset-all.txt",
                "list-ipset-all.txt",
            ]:
                p = lists_dir / name
                self.assertTrue(p.exists(), name)
                self.assertEqual(p.read_text(encoding="utf-8"), "")

    def test_google_alias_copy(self):
        with tempfile.TemporaryDirectory() as td:
            lists_dir = Path(td) / "lists"
            lists_dir.mkdir(parents=True, exist_ok=True)
            (lists_dir / "google.txt").write_text("x\n", encoding="utf-8")
            ctx = self._make_ctx(lists_dir)

            ensure_base_lists(ctx)

            self.assertTrue((lists_dir / "list-google.txt").exists())
            self.assertEqual((lists_dir / "list-google.txt").read_text(encoding="utf-8"), "x\n")

    def test_exclude_alias_copy(self):
        with tempfile.TemporaryDirectory() as td:
            lists_dir = Path(td) / "lists"
            lists_dir.mkdir(parents=True, exist_ok=True)
            (lists_dir / "list-exclude.txt").write_text("y\n", encoding="utf-8")
            ctx = self._make_ctx(lists_dir)

            ensure_base_lists(ctx)

            self.assertTrue((lists_dir / "exclude.txt").exists())
            self.assertEqual((lists_dir / "exclude.txt").read_text(encoding="utf-8"), "y\n")


if __name__ == "__main__":
    unittest.main()
