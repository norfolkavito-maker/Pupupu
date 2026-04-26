"""Unit tests for game_launcher.py .bat generation."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.zapret_manager.strategies.model import Strategy


class FakeCtx:
    """Minimal fake context for generate_bat testing."""
    class FakeConfig:
        class FakeZapret:
            winws_path = r".\zapret-win-bundle\winws.exe"
        class FakePaths:
            lists_dir = r".\data\lists"
            fake_files_dir = r".\zapret-win-bundle\files\fake"
        zapret = FakeZapret()
        paths = FakePaths()
    config = FakeConfig()
    root = Path(".")


class TestGameLauncher(unittest.TestCase):
    def test_generate_bat_contains_real_args_not_strategy_flag(self):
        from app.zapret_manager.features.game_launcher import generate_bat
        from app.zapret_manager.core.config import GameLauncherProfile

        profile = GameLauncherProfile(name="test", exe_path=r"C:\Games\test.exe", strategy_name="v7")

        # Temporarily patch find_strategy to return a known strategy
        import app.zapret_manager.features.game_launcher as gl
        original_find = gl.find_strategy

        def fake_find(ctx, name, kind=None):
            return Strategy(
                name="v7",
                engine="winws",
                args=["--filter-tcp=443", "--dpi-desync=fake"],
                kind="base",
            )

        gl.find_strategy = fake_find
        try:
            with tempfile.TemporaryDirectory() as td:
                out = Path(td) / "test.bat"
                generate_bat(FakeCtx(), profile, out)
                text = out.read_text(encoding="utf-8")
                self.assertNotIn("--strategy=", text)
                self.assertIn("winws.exe", text)
                self.assertIn("--filter-tcp=443", text)
                self.assertIn("--dpi-desync=fake", text)
                self.assertIn("taskkill /f /im winws.exe", text)
        finally:
            gl.find_strategy = original_find


if __name__ == "__main__":
    unittest.main()
