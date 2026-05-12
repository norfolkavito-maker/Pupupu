"""
Strategy normalization functions for path placeholders and upstream references.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.zapret_manager.core.app_context import AppContext

from app.zapret_manager.core.paths import Paths


class PlaceholderNormalizer:
    """Normalizes strategy placeholders to canonical DedZapret format."""
    
    def __init__(self, ctx: "AppContext"):
        self.ctx = ctx
        self.paths = Paths.from_root(Paths.detect_root())
        
        # Legacy Flowseal mappings
        self.flowseal_mappings = {
            "%BIN%": "{FLOWSEAL_BIN}",
            "%LISTS%": "{FLOWSEAL_LISTS}",
            "%~dp0": "{FLOWSEAL_ROOT}\\",
            "{UPSTREAM_ROOT}": "{FLOWSEAL_ROOT}",
        }
        
        # Linux path mappings for StressOzz
        self.linux_mappings = {
            "/opt/zapret/files/fake/": "{FAKE:",
            "/opt/zapret/ipset/": "{LISTS}",
            "/opt/zapret/lists/": "{LISTS}",
        }
    
    def normalize_flowseal_placeholders(self, command: str) -> str:
        """Convert Flowseal placeholders to DedZapret canonical format."""
        result = command
        for old, new in self.flowseal_mappings.items():
            result = result.replace(old, new)
        return result
    
    def normalize_linux_paths(self, command: str) -> str:
        """Convert Linux paths from StressOzz to canonical placeholders."""
        result = command
        for old, new in self.linux_mappings.items():
            result = result.replace(old, new)
        
        # Fix {FAKE:filename.bin} patterns
        result = re.sub(r"\{FAKE:([^ ]+)\.bin", r"{FAKE:\1.bin}", result)
        return result
    
    def normalize_all_placeholders(self, command: str) -> str:
        """Apply all placeholder normalizations."""
        result = command
        result = self.normalize_flowseal_placeholders(result)
        result = self.normalize_linux_paths(result)
        return result
    
    def extract_placeholders(self, command: str) -> List[str]:
        """Extract all placeholder patterns from a command."""
        placeholders = []
        
        # Standard placeholders
        for placeholder in ["{DATA}", "{RUNTIME}", "{LISTS}", "{MGR_LISTS}", 
                          "{FLOWSEAL_LISTS}", "{FLOWSEAL_BIN}", "{FLOWSEAL_ROOT}"]:
            if placeholder in command:
                placeholders.append(placeholder)
        
        # FAKE asset placeholders
        fake_pattern = r"\{FAKE:([^}]+)\}"
        for match in re.finditer(fake_pattern, command):
            placeholders.append(f"{{FAKE:{match.group(1)}}}")
        
        return placeholders
    
    def resolve_placeholders(self, command: str) -> Dict[str, Path]:
        """Resolve known placeholders to actual paths."""
        resolved = {}
        
        # Standard path resolutions
        if "{DATA}" in command:
            resolved["{DATA}"] = self.paths.data_dir
        
        if "{RUNTIME}" in command:
            resolved["{RUNTIME}"] = self.paths.runtime_dir
        
        if "{LISTS}" in command:
            resolved["{LISTS}"] = self.paths.lists_dir
        
        if "{MGR_LISTS}" in command:
            resolved["{MGR_LISTS}"] = self.paths.lists_dir
        
        # Flowseal-specific resolutions (if upstream cache exists)
        if "{FLOWSEAL_LISTS}" in command or "{FLOWSEAL_BIN}" in command:
            flowseal_cache = self.paths.upstreams_dir / "flowseal"
            if flowseal_cache.exists():
                if "{FLOWSEAL_LISTS}" in command:
                    resolved["{FLOWSEAL_LISTS}"] = flowseal_cache / "lists"
                if "{FLOWSEAL_BIN}" in command:
                    resolved["{FLOWSEAL_BIN}"] = flowseal_cache / "bin"
                if "{FLOWSEAL_ROOT}" in command:
                    resolved["{FLOWSEAL_ROOT}"] = flowseal_cache
        
        return resolved
    
    def validate_placeholders(self, command: str) -> List[str]:
        """Validate that all placeholders are known and resolvable."""
        placeholders = self.extract_placeholders(command)
        resolved = self.resolve_placeholders(command)
        
        unresolved = []
        for placeholder in placeholders:
            if placeholder not in resolved:
                # Check if it's a FAKE placeholder - these are validated separately
                if not placeholder.startswith("{FAKE:"):
                    unresolved.append(placeholder)
        
        return unresolved


def normalize_strategy_args(args: List[str], ctx: "AppContext") -> List[str]:
    """Normalize a list of strategy arguments."""
    normalizer = PlaceholderNormalizer(ctx)
    return [normalizer.normalize_all_placeholders(arg) for arg in args]


def extract_and_validate_placeholders(command: str, ctx: "AppContext") -> Dict[str, any]:
    """Extract placeholders and return validation info."""
    normalizer = PlaceholderNormalizer(ctx)
    
    placeholders = normalizer.extract_placeholders(command)
    resolved = normalizer.resolve_placeholders(command)
    unresolved = normalizer.validate_placeholders(command)
    
    return {
        "placeholders": placeholders,
        "resolved_paths": resolved,
        "unresolved_placeholders": unresolved,
        "has_unresolved": len(unresolved) > 0,
    }
