#!/usr/bin/env python3
"""
Test sing-box path contract in AppContext.
"""

import unittest
from pathlib import Path

from app.zapret_manager.core.app_context import AppContext


class TestSingBoxPathContract(unittest.TestCase):
    """Test that AppContext exposes canonical sing-box binary path."""

    def test_appcontext_has_singbox_bin_property(self):
        """Test that ctx.paths has singbox_bin property."""
        ctx = AppContext.bootstrap([])
        self.assertTrue(hasattr(ctx.paths, "singbox_bin"), "ctx.paths must have singbox_bin property")

    def test_singbox_bin_resolves_to_correct_path(self):
        """Test that singbox_bin resolves to bin/sing-box/sing-box.exe."""
        ctx = AppContext.bootstrap([])
        expected = ctx.paths.root / "bin" / "sing-box" / "sing-box.exe"
        self.assertEqual(ctx.paths.singbox_bin, expected.resolve())

    def test_singbox_bin_is_absolute(self):
        """Test that singbox_bin is an absolute path."""
        ctx = AppContext.bootstrap([])
        self.assertTrue(ctx.paths.singbox_bin.is_absolute())


if __name__ == "__main__":
    unittest.main()
