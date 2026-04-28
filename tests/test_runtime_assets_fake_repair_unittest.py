import unittest
from pathlib import Path
from unittest.mock import MagicMock
import tempfile


from app.zapret_manager.features.runtime_assets import ensure_fake_assets


class TestRuntimeAssetsFakeRepair(unittest.TestCase):
    def _make_ctx(self, runtime_dir: Path) -> MagicMock:
        ctx = MagicMock()
        ctx.paths = MagicMock()
        ctx.paths.runtime_dir = runtime_dir
        # lists_dir isn't used by ensure_fake_assets but some helpers may touch it later
        ctx.paths.lists_dir = runtime_dir / "data" / "lists"
        return ctx

    def test_fake_asset_copied_from_nested_location(self):
        with tempfile.TemporaryDirectory() as td:
            rt = Path(td) / "runtime"
            # canonical target
            target = rt / "zapret" / "files" / "fake"
            target.mkdir(parents=True, exist_ok=True)

            # simulate upstream weird location
            src = rt / "zapret" / "blockcheck" / "zapret" / "files" / "fake"
            src.mkdir(parents=True, exist_ok=True)
            (src / "quic_initial_www_google_com.bin").write_bytes(b"abc")

            ctx = self._make_ctx(rt)
            items = ensure_fake_assets(ctx)

            dst = target / "quic_initial_www_google_com.bin"
            self.assertTrue(dst.exists())
            self.assertEqual(dst.read_bytes(), b"abc")


if __name__ == "__main__":
    unittest.main()
