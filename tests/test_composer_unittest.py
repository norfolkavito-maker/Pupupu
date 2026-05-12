"""Unit tests for composer.py discord fallback and wssize."""
from __future__ import annotations

import unittest

from app.zapret_manager.strategies.composer import compose
from app.zapret_manager.strategies.model import Strategy, Command, CommandType


class TestComposer(unittest.TestCase):
    def _base(self, name: str = "v7", commands: list[Command] | None = None, kind: str = "base") -> Strategy:
        if commands is None:
            commands = [Command(type=CommandType.WINWS, command="--filter-tcp=443")]
        return Strategy(id=name, name=name, commands=commands, kind=kind)

    def test_discord_fallback_adds_block_when_not_found(self):
        """Dv overlay on base without discord block should append, not crash."""
        base_commands = [Command(type=CommandType.WINWS, command="--filter-tcp=443"), Command(type=CommandType.WINWS, command="--dpi-desync=fake")]
        base = self._base("v1", commands=base_commands)
        discord_commands = [Command(type=CommandType.WINWS, command="--filter-udp=443"), Command(type=CommandType.WINWS, command="--dpi-desync=fake")]
        discord = self._base("Dv1", commands=discord_commands, kind="discord")
        result = compose(base=base, youtube=None, discord=discord, discord_script="", games_profile="", rkn_enabled=False, wssize_enabled=False)
        self.assertIn("--filter-udp=443", result.args)
        self.assertTrue(any("--new" in a for a in result.args))

    def test_wssize_appends_block(self):
        base = self._base()
        result = compose(base=base, youtube=None, discord=None, discord_script="", games_profile="", rkn_enabled=False, wssize_enabled=True)
        self.assertIn("--wssize", result.args)
        self.assertIn("1:6", result.args)

    def test_timestamps_warning(self):
        base_commands = [Command(type=CommandType.WINWS, command="--dpi-desync=fake"), Command(type=CommandType.WINWS, command="--dpi-desync-fooling=ts")]
        base = self._base("v8", commands=base_commands)
        result = compose(base=base, youtube=None, discord=None, discord_script="", games_profile="", rkn_enabled=False, wssize_enabled=False)
        self.assertTrue(any("timestamps" in w for w in result.warnings))


if __name__ == "__main__":
    unittest.main()
