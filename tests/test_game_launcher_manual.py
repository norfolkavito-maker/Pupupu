"""Unit tests for game_launcher.py .bat generation."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.zapret_manager.strategies.model import Strategy, Command, CommandType


class FakeCtx:
    """Minimal fake context for generate_bat testing."""
    class FakePaths:
        # Mocking attributes used by zapret_runtime.py
        runtime_dir = Path(".") / "zapret-win-bundle"
        zapret_runtime_dir = Path(".") / "zapret-win-bundle" / "zapret"
        lists_dir = Path(".") / "data" / "lists"
        flowseal_lists_dir = Path(".") / "data" / "upstreams" / "flowseal" / "lists"
        flowseal_bin_dir = Path(".") / "data" / "upstreams" / "flowseal" / "bin"
        state_file = Path(".") / "state.json"
        config_file = Path(".") / "config.yaml"
        sources_file = Path(".") / "sources.yaml"
        logs_dir = Path(".") / "logs"

    class FakeState:
        class FakeZapretState:
            discord_profile: str = ""
            games_profile: str = ""
            winws_path: str = ""
            winws2_path: str = ""
            installed: bool = True
        zapret = FakeZapretState()
        runtime = FakeZapretState() # Reuse for runtime paths, though it's not ideal.
    
    paths = FakePaths()
    state = FakeState()
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
            commands = [
                Command(type=CommandType.WINWS, command="--filter-tcp=443"),
                Command(type=CommandType.WINWS, command="--dpi-desync=fake"),
            ]
            return Strategy(id="v7", name="v7", commands=commands, kind="base")

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
