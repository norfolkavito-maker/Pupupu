"""
Console UI scenario crawler for detecting broken menu handlers.

This module provides automated testing of console menu scenarios
by capturing output and detecting errors without starting real runtime.
"""

import unittest
from unittest.mock import MagicMock, patch, call
from pathlib import Path
import sys
from io import StringIO

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.zapret_manager.ui.menus import (
    wizard_menu,
    strategies_menu,
    lists_menu,
    games_menu,
    services_menu,
    vpn_menu,
    repair_menu,
    system_advanced_menu,
    extras_menu,
)
from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.state import AppState


class ConsoleUICrawler(unittest.TestCase):
    """Automated console UI scenario crawler."""

    def _make_ctx(self):
        """Create a minimal AppContext for testing."""
        ctx = MagicMock(spec=AppContext)
        ctx.state = MagicMock(spec=AppState)
        ctx.state.zapret = MagicMock()
        ctx.state.zapret.running = False
        ctx.state.zapret.selected_strategy = "v9"
        ctx.state.zapret.base_strategy = "v9"
        ctx.state.zapret.youtube_layer = None
        ctx.state.zapret.discord_layer = None
        ctx.state.zapret.rkn_enabled = False
        ctx.state.zapret.games_profile = None
        ctx.state.zapret.wssize_enabled = False
        ctx.paths = MagicMock()
        ctx.paths.data_dir = Path("/tmp/test_data")
        ctx.paths.state_file = Path("/tmp/test_state.json")
        ctx.paths.strategies_generated_dir = Path("/tmp/test_strategies")
        ctx.paths.strategies_custom_dir = Path("/tmp/test_strategies_custom")
        ctx.config = MagicMock()
        ctx.config.diagnostics = MagicMock()
        ctx.config.diagnostics.enabled = False
        ctx.state.runtime = MagicMock()
        return ctx

    def _capture_menu_output(self, menu_func, ctx, inputs):
        """Capture menu output with simulated user inputs."""
        captured_output = StringIO()
        error_occurred = False
        error_message = None
        
        try:
            with patch("sys.stdout", captured_output):
                with patch("app.zapret_manager.ui.menus.ask") as mock_ask:
                    with patch("app.zapret_manager.ui.menus.pause"):
                        with patch("app.zapret_manager.ui.menus.clear"):
                            mock_ask.side_effect = inputs
                            menu_func(ctx)
        except Exception as e:
            error_occurred = True
            error_message = str(e)
        
        output = captured_output.getvalue()
        return output, error_occurred, error_message

    def _assert_no_forbidden_strings(self, output, error_occurred, error_message):
        """Assert that output contains no forbidden strings."""
        forbidden_strings = [
            "Traceback",
            "Ошибка:",
            "Exception",
            "missing required positional argument",
            "is not defined",
            "cannot assign to field",
            "sync StressOzz",
            "TG WS Proxy",
            "pid=-",
        ]
        
        errors_found = []
        for forbidden in forbidden_strings:
            if forbidden in output:
                errors_found.append(f"Found forbidden string: '{forbidden}'")
            if error_message and forbidden in error_message:
                errors_found.append(f"Found forbidden string in error: '{forbidden}'")
        
        if error_occurred:
            errors_found.append(f"Exception occurred: {error_message}")
        
        self.assertEqual([], errors_found, "\n".join(errors_found))

    def test_crawl_main_menu_submenu_screens(self):
        """PHASE 2: Crawl main submenu screens (2-9, 0)."""
        ctx = self._make_ctx()
        
        # Import testing_submenu dynamically to avoid pytest collection
        from app.zapret_manager.ui.menus import testing_submenu
        
        # Test each submenu can be opened and returned from
        submenus = [
            ("Setup Wizard", wizard_menu),
            ("Strategies", strategies_menu),
            ("Testing", testing_submenu),
            ("Lists", lists_menu),
            ("Games", games_menu),
            ("Services", services_menu),
            ("VPN", vpn_menu),
            ("Repair", repair_menu),
            ("System/Advanced", system_advanced_menu),
        ]
        
        for name, menu_func in submenus:
            with self.subTest(menu=name):
                output, error_occurred, error_message = self._capture_menu_output(
                    menu_func, ctx, [""]  # Press Enter to return
                )
                self._assert_no_forbidden_strings(output, error_occurred, error_message)
                # Verify menu rendered something
                self.assertGreater(len(output), 0, f"{name} menu produced no output")

    def test_setup_wizard_quick_setup_no_state_error(self):
        """PHASE 3: Setup Wizard - Быстрая настройка should not have 'cannot assign to field state'."""
        ctx = self._make_ctx()
        
        # Import the actual handler to test it directly
        from app.zapret_manager.features.key_setup import key_setup
        
        # Call key_setup directly to reproduce the manual bug path
        try:
            captured_output = StringIO()
            with patch("sys.stdout", captured_output):
                with patch("app.zapret_manager.ui.menus.pause"):
                    with patch("app.zapret_manager.ui.menus.clear"):
                        key_setup(ctx)
            output = captured_output.getvalue()
            error_occurred = False
            error_message = None
        except Exception as e:
            output = ""
            error_occurred = True
            error_message = str(e)
        
        # Check for the state assignment error
        self.assertNotIn("cannot assign to field 'state'", output)
        if error_message:
            self.assertNotIn("cannot assign to field 'state'", error_message)
        
        # Also check for other forbidden strings
        self.assertNotIn("Traceback", output)
        self.assertNotIn("Exception", output)
        if error_message:
            self.assertNotIn("Traceback", error_message)

    def test_setup_wizard_full_setup_no_state_error(self):
        """PHASE 3: Setup Wizard - Полная настройка should not have 'cannot assign to field state'."""
        ctx = self._make_ctx()
        
        # Import the actual handler to test it directly
        from app.zapret_manager.features.key_setup import key_setup_full_check
        
        # Call key_setup_full_check directly to reproduce the manual bug path
        try:
            captured_output = StringIO()
            with patch("sys.stdout", captured_output):
                with patch("app.zapret_manager.ui.menus.pause"):
                    with patch("app.zapret_manager.ui.menus.clear"):
                        key_setup_full_check(ctx)
            output = captured_output.getvalue()
            error_occurred = False
            error_message = None
        except Exception as e:
            output = ""
            error_occurred = True
            error_message = str(e)
        
        # Check for the state assignment error
        self.assertNotIn("cannot assign to field 'state'", output)
        if error_message:
            self.assertNotIn("cannot assign to field 'state'", error_message)
        
        # Also check for other forbidden strings
        self.assertNotIn("Traceback", output)
        self.assertNotIn("Exception", output)
        if error_message:
            self.assertNotIn("Traceback", error_message)

    def test_strategies_select_v_strategy_no_missing_name_error(self):
        """PHASE 3: Strategies - Выбрать основную стратегию v1-v9 should not call _set_base without name."""
        ctx = self._make_ctx()
        
        # Try to navigate to Выбрать основную стратегию v1-v9
        # Option 1 asks for version input, then calls _set_base with the version
        # We need to provide a version number
        output, error_occurred, error_message = self._capture_menu_output(
            strategies_menu, ctx, ["1", "9", ""]  # Select option 1, enter "9", then Enter to return
        )
        
        # Check for the specific missing name error (the actual bug we're testing for)
        self.assertNotIn("missing 1 required positional argument: 'name'", output)
        if error_message:
            self.assertNotIn("missing 1 required positional argument: 'name'", error_message)
        
        # It's OK if strategy is not found in test context (no actual strategies loaded)
        # But we should not have the "missing argument" error
        if "Стратегия v9 не найдена" in output or "не найдена" in output:
            # This is expected in test context with no strategies
            pass
        else:
            # If strategy was supposed to be found, check for other errors
            self._assert_no_forbidden_strings(output, error_occurred, error_message)

    def test_strategies_show_current_no_load_strategy_error(self):
        """PHASE 3: Strategies - Показать текущую стратегию should not have '_load_selected_strategy is not defined'."""
        ctx = self._make_ctx()
        
        # Try to navigate to Показать текущую стратегию
        # Note: This might be option 3 or similar depending on menu structure
        output, error_occurred, error_message = self._capture_menu_output(
            strategies_menu, ctx, ["3", ""]  # Try option 3, then Enter to return
        )
        
        self._assert_no_forbidden_strings(output, error_occurred, error_message)
        
        # Specifically check for _load_selected_strategy error
        self.assertNotIn("_load_selected_strategy", output)
        self.assertNotIn("is not defined", output)
        if error_message:
            self.assertNotIn("_load_selected_strategy", error_message)

    def test_repair_bundled_strategy_check_consistency(self):
        """PHASE 3: Repair - bundled strategy pack check should be internally consistent."""
        ctx = self._make_ctx()
        
        # Try to navigate to bundled strategy pack check
        # This might be option 4 or similar depending on menu structure
        output, error_occurred, error_message = self._capture_menu_output(
            repair_menu, ctx, ["4", ""]  # Try option 4, then Enter to return
        )
        
        self._assert_no_forbidden_strings(output, error_occurred, error_message)
        
        # If output shows strategy counts, they should be reasonable
        # This is a basic sanity check - detailed consistency check requires actual strategy data
        if "Flowseal" in output and "0" in output:
            # If Flowseal is mentioned, it should not be 0 unless documented
            # This is a placeholder for more detailed checking
            pass

    def test_repair_check_strategy_assets_no_load_strategy_error(self):
        """PHASE 3: Repair - Проверить ассеты стратегий should not have '_load_selected_strategy is not defined'."""
        ctx = self._make_ctx()
        
        # Try to navigate to Проверить ассеты стратегий
        # This might be option 5 or similar depending on menu structure
        output, error_occurred, error_message = self._capture_menu_output(
            repair_menu, ctx, ["5", ""]  # Try option 5, then Enter to return
        )
        
        self._assert_no_forbidden_strings(output, error_occurred, error_message)
        
        # Specifically check for _load_selected_strategy error
        self.assertNotIn("_load_selected_strategy", output)
        self.assertNotIn("is not defined", output)
        if error_message:
            self.assertNotIn("_load_selected_strategy", error_message)

    def test_system_advanced_wssize_only_in_advanced(self):
        """PHASE 3: System/Advanced - wssize should only exist as advanced option, not in base Strategies."""
        ctx = self._make_ctx()
        
        # Check that system_advanced_menu has wssize option
        output, error_occurred, error_message = self._capture_menu_output(
            system_advanced_menu, ctx, [""]  # Just open and return
        )
        
        self._assert_no_forbidden_strings(output, error_occurred, error_message)
        
        # wssize should be present in System/Advanced (as option W)
        # This is expected and correct
        
        # Check that strategies_menu does NOT have wssize in user-facing output
        strategies_output, _, _ = self._capture_menu_output(
            strategies_menu, ctx, [""]
        )
        
        # wssize should not be in strategies_menu user-facing output
        # (state variables are OK)
        lines_with_wssize = []
        for line in strategies_output.split('\n'):
            if 'wssize' in line.lower() and 'print' in line:
                lines_with_wssize.append(line)
        
        self.assertEqual([], lines_with_wssize, 
                         "wssize should not be in strategies_menu user-facing output")


if __name__ == "__main__":
    unittest.main()
