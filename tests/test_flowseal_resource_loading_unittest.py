#!/usr/bin/env python3
"""
Test Flowseal resource loading from resources/flowseal/strategies.
"""

import unittest
from pathlib import Path

from app.zapret_manager.strategies.store import list_strategies


class TestFlowsealResourceLoading(unittest.TestCase):
    """Test that Flowseal strategies can be loaded from resources directory."""

    def test_flowseal_resources_load_with_kind_none(self):
        """Test Flowseal resources load >=19 strategies with kind=None."""
        resources_flowseal = Path("resources/flowseal/strategies")
        if not resources_flowseal.exists():
            self.skipTest("resources/flowseal/strategies does not exist in dev environment")
        
        items = list_strategies(None, resources_flowseal, kind=None)
        self.assertGreaterEqual(len(items), 19, f"Expected >=19 Flowseal strategies, got {len(items)}")

    def test_flowseal_resources_load_with_kind_base(self):
        """Test Flowseal resources load >=19 strategies with kind=base."""
        resources_flowseal = Path("resources/flowseal/strategies")
        if not resources_flowseal.exists():
            self.skipTest("resources/flowseal/strategies does not exist in dev environment")
        
        items = list_strategies(None, resources_flowseal, kind="base")
        self.assertGreaterEqual(len(items), 19, f"Expected >=19 Flowseal base strategies, got {len(items)}")

    def test_flowseal_strategies_have_commands(self):
        """Test that loaded Flowseal strategies have commands."""
        resources_flowseal = Path("resources/flowseal/strategies")
        if not resources_flowseal.exists():
            self.skipTest("resources/flowseal/strategies does not exist in dev environment")
        
        items = list_strategies(None, resources_flowseal, kind="base")
        for s in items[:5]:
            self.assertIsInstance(s.commands, list)
            self.assertGreater(len(s.commands), 0)


if __name__ == "__main__":
    unittest.main()
