#!/usr/bin/env python3
"""
Static test to ensure no stale list_strategies calls remain in app code.
All list_strategies calls must include ctx as first argument.
"""

import ast
import unittest
from pathlib import Path


class TestStaleListStrategiesCalls(unittest.TestCase):
    """Test that no stale list_strategies calls exist in app code."""

    def test_no_stale_list_strategies_calls_in_app(self):
        """Ensure all list_strategies calls in app code include ctx argument."""
        app_dir = Path(__file__).parent.parent / "app"
        
        stale_calls = []
        
        for py_file in app_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name) and node.func.id == "list_strategies":
                            # Check if first argument is ctx or similar
                            if len(node.args) < 2:  # Should have ctx and dir_path
                                stale_calls.append((str(py_file), node.lineno))
                            elif len(node.args) >= 2:
                                # Check if first arg is clearly ctx
                                first_arg = node.args[0]
                                if isinstance(first_arg, ast.Name) and first_arg.id not in {"ctx", "self", "context"}:
                                    stale_calls.append((str(py_file), node.lineno))
            except Exception:
                # Skip files that can't be parsed
                pass
        
        if stale_calls:
            self.fail(
                f"Found {len(stale_calls)} stale list_strategies calls:\n"
                + "\n".join(f"{file}:{line}" for file, line in stale_calls)
            )

    def test_no_flowseal_with_kind_generated(self):
        """Ensure list_strategies never uses kind='generated' with flowseal path."""
        app_dir = Path(__file__).parent.parent / "app"
        
        forbidden_calls = []
        
        for py_file in app_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name) and node.func.id == "list_strategies":
                            # Check for kind="generated" keyword argument
                            has_kind_generated = False
                            for kw in node.keywords:
                                if kw.arg == "kind":
                                    if isinstance(kw.value, ast.Constant) and kw.value.value == "generated":
                                        has_kind_generated = True
                            
                            # Check if path contains "flowseal"
                            has_flowseal_path = False
                            if len(node.args) >= 2:
                                path_arg = node.args[1]
                                if isinstance(path_arg, ast.BinOp):
                                    # Check for path / "flowseal"
                                    if isinstance(path_arg.op, ast.Div):
                                        right = path_arg.right
                                        if isinstance(right, ast.Constant) and "flowseal" in str(right.value).lower():
                                            has_flowseal_path = True
                            
                            if has_kind_generated and has_flowseal_path:
                                forbidden_calls.append((str(py_file), node.lineno))
            except Exception:
                # Skip files that can't be parsed
                pass
        
        if forbidden_calls:
            self.fail(
                f"Found {len(forbidden_calls)} forbidden list_strategies calls with kind='generated' and flowseal path:\n"
                + "\n".join(f"{file}:{line}" for file, line in forbidden_calls)
            )


if __name__ == "__main__":
    unittest.main()
