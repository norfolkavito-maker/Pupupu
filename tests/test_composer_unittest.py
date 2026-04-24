"""Unit tests for composer.py discord fallback and wssize."""
from __future__ import annotations

import unittest

from zapret_manager.strategies.composer import compose
from zapret_manager.strategies.model import Strategy


class TestComposer(unittest.TestCase):
    def _base(self, name: str = "v7", args: list[str] | None = None) -> Strategy:
        return Strategy(name=name, engine="winws", args=args or ["--filter-tcp=443"], kind="base")

    def test_discord_fallback_adds_block_when_not_found(self):
        """Dv overlay on base without discord block should append, not crash."""
        base = self._base("v1", args=["--filter-tcp=443", "--dpi-desync=fake"])
        discord = Strategy(name="Dv1", engine="winws", args=["--filter-udp=443", "--dpi-desync=fake"], kind="discord")
        result = compose(base=base, youtube=None, discord=discord, discord_script="", games_profile="", rkn_enabled=False, wssize_enabled=False)
        self.assertIn("--filter-udp=443", result.args)
        self.assertTrue(any("--new" in a for a in result.args))

    def test_wssize_appends_block(self):
        base = self._base()
        result = compose(base=base, youtube=None, discord=None, discord_script="", games_profile="", rkn_enabled=False, wssize_enabled=True)
        self.assertIn("--wssize", result.args)
        self.assertIn("1:6", result.args)

    def test_timestamps_warning(self):
        base = Strategy(name="v8", engine="winws", args=["--dpi-desync=fake", "--dpi-desync-fooling=ts"], kind="base")
        result = compose(base=base, youtube=None, discord=None, discord_script="", games_profile="", rkn_enabled=False, wssize_enabled=False)
        self.assertTrue(any("timestamps" in w for w in result.warnings))


if __name__ == "__main__":
    unittest.main()
