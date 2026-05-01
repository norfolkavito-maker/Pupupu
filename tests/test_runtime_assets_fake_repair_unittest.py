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


    def test_stun_bin_is_supported(self):
        with tempfile.TemporaryDirectory() as td:
            rt = Path(td) / "runtime"
            target = rt / "zapret" / "files" / "fake"
            target.mkdir(parents=True, exist_ok=True)

            # put stun.bin in a non-canonical place
            src = rt / "zapret" / "blockcheck" / "zapret" / "files" / "fake"
            src.mkdir(parents=True, exist_ok=True)
            (src / "stun.bin").write_bytes(b"zzz")

            ctx = self._make_ctx(rt)
            ensure_fake_assets(ctx)

            dst = target / "stun.bin"
            self.assertTrue(dst.exists())
            self.assertEqual(dst.read_bytes(), b"zzz")


    def test_v3_v8_fake_assets_are_supported(self):
        with tempfile.TemporaryDirectory() as td:
            rt = Path(td) / "runtime"
            target = rt / "zapret" / "files" / "fake"
            target.mkdir(parents=True, exist_ok=True)

            # put a few v3/v8 assets in a non-canonical place
            src = rt / "zapret" / "blockcheck" / "zapret" / "files" / "fake"
            src.mkdir(parents=True, exist_ok=True)
            (src / "tls_clienthello_vk_com.bin").write_bytes(b"vk")
            (src / "tls_clienthello_gosuslugi_ru.bin").write_bytes(b"gos")
            (src / "4pda.bin").write_bytes(b"4pda")
            (src / "t2.bin").write_bytes(b"t2")

            ctx = self._make_ctx(rt)
            ensure_fake_assets(ctx)

            for name, expected in [
                ("tls_clienthello_vk_com.bin", b"vk"),
                ("tls_clienthello_gosuslugi_ru.bin", b"gos"),
                ("4pda.bin", b"4pda"),
                ("t2.bin", b"t2"),
            ]:
                dst = target / name
                self.assertTrue(dst.exists(), name)
                self.assertEqual(dst.read_bytes(), expected, name)


if __name__ == "__main__":
    unittest.main()
