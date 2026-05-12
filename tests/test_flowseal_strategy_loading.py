"""Tests for Flowseal strategy loading and discovery."""

import pytest
from pathlib import Path
import tempfile
import shutil

from app.zapret_manager.strategies.store import list_strategies
from app.zapret_manager.strategies.model import Strategy


class TestFlowsealStrategyLoading:
    """Test Flowseal strategy loading and discovery."""

    def test_flowseal_resource_yaml_loads(self):
        """Test that a single Flowseal resource YAML loads correctly."""
        from pathlib import Path
        resource_file = Path(__file__).parent.parent / "resources" / "flowseal" / "strategies" / "flowseal_general.yaml"
        
        assert resource_file.exists(), "Flowseal resource file should exist"
        
        strategies = list_strategies(None, resource_file.parent, kind="base")
        assert len(strategies) > 0, "Should load at least one strategy"
        
        # Find the flowseal_general strategy
        flowseal_general = None
        for strategy in strategies:
            if strategy.id == "flowseal_general":
                flowseal_general = strategy
                break
        
        assert flowseal_general is not None, "Should find flowseal_general strategy"
        assert flowseal_general.name == "Flowseal General", "Strategy name should match"
        assert len(flowseal_general.commands) > 0, "Strategy should have commands"
        assert flowseal_general.kind == "base", "Strategy kind should be base"

    def test_flowseal_resource_catalog_loads(self):
        """Test that all Flowseal resource YAML files load."""
        from pathlib import Path
        resources_dir = Path(__file__).parent.parent / "resources" / "flowseal" / "strategies"
        
        assert resources_dir.exists(), "Flowseal resources directory should exist"
        
        strategies = list_strategies(None, resources_dir, kind="base")
        assert len(strategies) >= 19, f"Should load at least 19 strategies, got {len(strategies)}"
        
        # Check that all strategies have required fields
        for strategy in strategies:
            assert strategy.id, f"Strategy {strategy} should have an id"
            assert strategy.name, f"Strategy {strategy} should have a name"
            assert len(strategy.commands) > 0, f"Strategy {strategy} should have commands"

    def test_generated_flowseal_recursive_scan(self):
        """Test that recursive scan discovers Flowseal strategies in subdirectories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create directory structure: generated/flowseal/
            generated_dir = temp_path / "generated"
            flowseal_dir = generated_dir / "flowseal"
            flowseal_dir.mkdir(parents=True)
            
            # Copy a few Flowseal strategy files
            resources_dir = Path(__file__).parent.parent / "resources" / "flowseal" / "strategies"
            
            # Copy first 3 Flowseal strategies
            flowseal_files = list(resources_dir.glob("flowseal_general*.yaml"))[:3]
            assert len(flowseal_files) >= 3, "Should have at least 3 flowseal_general files"
            
            for flowseal_file in flowseal_files:
                shutil.copy2(flowseal_file, flowseal_dir / flowseal_file.name)
            
            # Test that list_strategies discovers files in subdirectory
            strategies = list_strategies(None, generated_dir, kind="base")
            assert len(strategies) >= 3, f"Should load at least 3 strategies from subdirectory, got {len(strategies)}"
            
            # Verify the strategies are from the flowseal subdirectory
            flowseal_strategies = [s for s in strategies if "flowseal" in s.source_file]
            assert len(flowseal_strategies) >= 3, f"Should have at least 3 flowseal strategies, got {len(flowseal_strategies)}"

    def test_unknown_metadata_does_not_break_strategy_load(self):
        """Test that unknown metadata fields in Flowseal YAML don't break loading."""
        # Create a test YAML with unknown metadata fields
        test_yaml = """id: test_flowseal_unknown
name: Test Flowseal Unknown
source: flowseal
source_repo: Flowseal/zapret-discord-youtube
source_ref: main
source_sha256: abc123def456
required_assets:
  fake:
  - test.bin
  lists:
  - test.txt
tags:
- test
- flowseal
warnings:
- Test warning
conflicts:
  may_overlap_layers:
  - test
requires_profile_composer: true
commands:
- type: winws
  command: --test
kind: base
"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test_flowseal_unknown.yaml"
            test_file.write_text(test_yaml)
            
            # Should load without crashing
            strategies = list_strategies(None, temp_path, kind="base")
            assert len(strategies) == 1, "Should load exactly one strategy"
            
            strategy = strategies[0]
            assert strategy.id == "test_flowseal_unknown", "Strategy ID should match"
            assert strategy.name == "Test Flowseal Unknown", "Strategy name should match"
            assert len(strategy.commands) == 1, "Should have one command"
            assert strategy.commands[0].type.value == "winws", "Command type should be winws"
            
            # Check that required_assets were normalized to missing_assets
            assert len(strategy.missing_assets) >= 2, "Should have missing assets from required_assets"
            assert any("fake/test.bin" in asset for asset in strategy.missing_assets), "Should have fake asset"
            assert any("lists/test.txt" in asset for asset in strategy.missing_assets), "Should have lists asset"

    def test_no_sync_required_for_bundled_flowseal_listing(self):
        """Test that listing Flowseal strategies doesn't require sync/network calls."""
        from pathlib import Path
        resources_dir = Path(__file__).parent.parent / "resources" / "flowseal" / "strategies"
        
        # This should work without any network calls or sync operations
        strategies = list_strategies(None, resources_dir, kind="base")
        assert len(strategies) >= 19, "Should load Flowseal strategies without sync"
