#!/usr/bin/env python3
"""
Test Flowseal runtime path loading from data/strategies/generated/flowseal.
This simulates the Windows release layout where Flowseal strategies are bundled.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from app.zapret_manager.strategies.store import list_strategies


class TestFlowsealRuntimePath(unittest.TestCase):
    """Test that Flowseal strategies load from runtime generated/flowseal path."""

    def test_temp_generated_flowseal_loads_with_kind_base(self):
        """Test that temp generated/flowseal with kind=base loads strategies."""
        # Use real Flowseal YAML from resources
        resources_flowseal = Path("resources/flowseal/strategies")
        if not resources_flowseal.exists():
            self.skipTest("resources/flowseal/strategies does not exist in dev environment")

        with tempfile.TemporaryDirectory() as td:
            # Create runtime layout: data/strategies/generated/flowseal
            generated_flowseal = Path(td) / "data" / "strategies" / "generated" / "flowseal"
            generated_flowseal.mkdir(parents=True)

            # Copy real Flowseal YAML files (they have kind: base)
            for src in list(resources_flowseal.glob("*.yaml"))[:5]:
                shutil.copy(src, generated_flowseal / src.name)

            # Load using the same path and kind as the menu
            items = list_strategies(None, generated_flowseal, kind="base")
            self.assertGreater(len(items), 0, f"Expected >0 strategies from temp generated/flowseal, got {len(items)}")

            # Verify loaded strategies have kind=base
            for s in items:
                self.assertEqual(s.kind, "base")

    def test_temp_generated_flowseal_loads_with_kind_none(self):
        """Test that temp generated/flowseal with kind=None loads strategies."""
        resources_flowseal = Path("resources/flowseal/strategies")
        if not resources_flowseal.exists():
            self.skipTest("resources/flowseal/strategies does not exist in dev environment")

        with tempfile.TemporaryDirectory() as td:
            generated_flowseal = Path(td) / "data" / "strategies" / "generated" / "flowseal"
            generated_flowseal.mkdir(parents=True)

            for src in list(resources_flowseal.glob("*.yaml"))[:5]:
                shutil.copy(src, generated_flowseal / src.name)

            items = list_strategies(None, generated_flowseal, kind=None)
            self.assertGreater(len(items), 0, f"Expected >0 strategies with kind=None, got {len(items)}")


if __name__ == "__main__":
    unittest.main()
