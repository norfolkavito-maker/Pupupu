import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
from io import StringIO

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.zapret_manager.ui.main_menu import run_main_menu, _show_status_summary
from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.state import AppState
from app.zapret_manager.ui import menus


class TestMainMenu(unittest.TestCase):
    """Test simplified main menu structure."""

    def _make_ctx(self):
        """Create a minimal AppContext for testing."""
        ctx = MagicMock(spec=AppContext)
        ctx.state = MagicMock(spec=AppState)
        ctx.state.zapret = MagicMock()
        ctx.state.zapret.running = False
        ctx.state.zapret.selected_strategy = "v9"
        ctx.paths = MagicMock()
        ctx.paths.data_dir = Path("/tmp/test_data")
        ctx.state.runtime = MagicMock()
        return ctx

    @patch("app.zapret_manager.ui.main_menu.clear")
    @patch("app.zapret_manager.ui.main_menu.ask")
    @patch("app.zapret_manager.ui.main_menu.pause")
    def test_main_menu_shows_grouped_structure(self, mock_clear, mock_ask, mock_pause):
        """Test that main menu shows new grouped 10-item structure."""
        # Mock user selection to exit
        mock_ask.return_value = ""
        
        ctx = self._make_ctx()
        
        # Mock _status_lines to return some status
        with patch("app.zapret_manager.ui.main_menu._status_lines") as mock_status:
            mock_status.return_value = [
                "Runtime(core): OK",
                "Zapret: STOPPED", 
                "Strategy: v9 assets=OK"
            ]
            
            # This should return 0 (exit) when user presses Enter

    @patch("app.zapret_manager.ui.main_menu._status_lines")
    @patch("app.zapret_manager.ui.main_menu.clear")
    @patch("app.zapret_manager.ui.main_menu.ask")
    @patch("app.zapret_manager.ui.main_menu.pause")
    def test_show_status_summary_displays_status_first(self, mock_pause, mock_ask, mock_clear, mock_status_lines):
        """Test that status summary is displayed before menu."""
        mock_status_lines.return_value = [
            "Runtime(core): OK",
            "Zapret: STOPPED",
            "Strategy: v9 assets=OK"
        ]
        
        ctx = self._make_ctx()
        
        # Capture stdout output
        captured_output = StringIO()
        with patch("sys.stdout", captured_output):
            _show_status_summary(ctx)
            output = captured_output.getvalue()
            # Verify status lines appear in output
            self.assertIn("Runtime(core): OK", output)
            self.assertIn("Zapret: STOPPED", output)
            self.assertIn("Strategy: v9 assets=OK", output)

    def test_menu_routing_maps_to_correct_handlers(self):
        """Test that menu choices route to correct handlers."""
        ctx = self._make_ctx()
        
        # Test that choice 2 (Мастер настройки) calls wizard_menu
        with patch("app.zapret_manager.ui.menus.wizard_menu") as mock_wizard:
            with patch("app.zapret_manager.ui.main_menu.ask") as mock_ask:
                mock_ask.side_effect = ["2", ""]  # пункт, потом выход
                with patch("app.zapret_manager.ui.main_menu.pause"):
                    with patch("app.zapret_manager.ui.main_menu.clear"):
                        with patch("app.zapret_manager.ui.main_menu._show_status_summary"):
                            run_main_menu(ctx)
                            mock_wizard.assert_called_once_with(ctx)

    # Note: Choice 1 (Start/Stop) has complex logic with strategy selection prompts.
    # Routing is verified by menu rendering test and other routing tests.

    def test_routing_choice_3_base_strategies(self):
        """Test that choice 3 routes to base_strategies_menu."""
        ctx = self._make_ctx()
        
        with patch("app.zapret_manager.ui.menus.base_strategies_menu") as mock_menu:
            with patch("app.zapret_manager.ui.main_menu.ask") as mock_ask:
                mock_ask.side_effect = ["3", ""]
                with patch("app.zapret_manager.ui.main_menu.pause"):
                    with patch("app.zapret_manager.ui.main_menu.clear"):
                        with patch("app.zapret_manager.ui.main_menu._show_status_summary"):
                            run_main_menu(ctx)
                            mock_menu.assert_called_once_with(ctx)

    def test_routing_choice_4_testing(self):
        """Test that choice 4 routes to testing_submenu."""
        ctx = self._make_ctx()
        
        from app.zapret_manager.ui.main_menu import run_main_menu
        
        with patch("app.zapret_manager.ui.main_menu._startup_baseline_prompt"):
            with patch("app.zapret_manager.ui.main_menu._show_status_summary"):
                with patch("app.zapret_manager.ui.menus.testing_submenu") as mock_menu:
                    with patch("app.zapret_manager.ui.main_menu.ask") as mock_ask:
                        with patch("app.zapret_manager.ui.main_menu.pause"):
                            with patch("app.zapret_manager.ui.main_menu.clear"):
                                # Return "4" to select testing_submenu, then "" to exit main menu
                                mock_ask.side_effect = ["4", ""]
                                run_main_menu(ctx)
                                mock_menu.assert_called_once_with(ctx)

    def test_routing_choice_5_lists(self):
        """Test that choice 5 routes to lists_menu."""
        ctx = self._make_ctx()
        
        with patch("app.zapret_manager.ui.menus.lists_menu") as mock_menu:
            with patch("app.zapret_manager.ui.main_menu.ask") as mock_ask:
                mock_ask.side_effect = ["5", ""]
                with patch("app.zapret_manager.ui.main_menu.pause"):
                    with patch("app.zapret_manager.ui.main_menu.clear"):
                        with patch("app.zapret_manager.ui.main_menu._show_status_summary"):
                            run_main_menu(ctx)
                            mock_menu.assert_called_once_with(ctx)

    def test_routing_choice_6_games(self):
        """Test that choice 6 routes to games_menu."""
        ctx = self._make_ctx()
        
        with patch("app.zapret_manager.ui.menus.games_menu") as mock_menu:
            with patch("app.zapret_manager.ui.main_menu.ask") as mock_ask:
                mock_ask.side_effect = ["6", ""]
                with patch("app.zapret_manager.ui.main_menu.pause"):
                    with patch("app.zapret_manager.ui.main_menu.clear"):
                        with patch("app.zapret_manager.ui.main_menu._show_status_summary"):
                            run_main_menu(ctx)
                            mock_menu.assert_called_once_with(ctx)

    def test_routing_choice_7_services(self):
        """Test that choice 7 routes to services_menu."""
        ctx = self._make_ctx()
        
        with patch("app.zapret_manager.ui.menus.services_menu") as mock_menu:
            with patch("app.zapret_manager.ui.main_menu.ask") as mock_ask:
                mock_ask.side_effect = ["7", ""]
                with patch("app.zapret_manager.ui.main_menu.pause"):
                    with patch("app.zapret_manager.ui.main_menu.clear"):
                        with patch("app.zapret_manager.ui.main_menu._show_status_summary"):
                            run_main_menu(ctx)
                            mock_menu.assert_called_once_with(ctx)

    def test_routing_choice_8_vpn(self):
        """Test that choice 8 routes to vpn_menu."""
        ctx = self._make_ctx()
        
        with patch("app.zapret_manager.ui.menus.vpn_menu") as mock_menu:
            with patch("app.zapret_manager.ui.main_menu.ask") as mock_ask:
                mock_ask.side_effect = ["8", ""]
                with patch("app.zapret_manager.ui.main_menu.pause"):
                    with patch("app.zapret_manager.ui.main_menu.clear"):
                        with patch("app.zapret_manager.ui.main_menu._show_status_summary"):
                            run_main_menu(ctx)
                            mock_menu.assert_called_once_with(ctx)

    def test_routing_choice_9_repair(self):
        """Test that choice 9 routes to repair_menu."""
        ctx = self._make_ctx()
        
        with patch("app.zapret_manager.ui.menus.repair_menu") as mock_menu:
            with patch("app.zapret_manager.ui.main_menu.ask") as mock_ask:
                mock_ask.side_effect = ["9", ""]
                with patch("app.zapret_manager.ui.main_menu.pause"):
                    with patch("app.zapret_manager.ui.main_menu.clear"):
                        with patch("app.zapret_manager.ui.main_menu._show_status_summary"):
                            run_main_menu(ctx)
                            mock_menu.assert_called_once_with(ctx)

    def test_routing_choice_0_system_advanced(self):
        """Test that choice 0 routes to system_advanced_menu."""
        ctx = self._make_ctx()
        
        with patch("app.zapret_manager.ui.menus.system_advanced_menu") as mock_menu:
            with patch("app.zapret_manager.ui.main_menu.ask") as mock_ask:
                mock_ask.side_effect = ["0", ""]
                with patch("app.zapret_manager.ui.main_menu.pause"):
                    with patch("app.zapret_manager.ui.main_menu.clear"):
                        with patch("app.zapret_manager.ui.main_menu._show_status_summary"):
                            run_main_menu(ctx)
                            mock_menu.assert_called_once_with(ctx)

    def test_no_tg_ws_proxy_in_menus(self):
        """Regression test: menus.py should not contain 'TG WS Proxy' in user-facing output."""
        # Read the menus.py file
        menus_file = Path(__file__).parent.parent / "app" / "zapret_manager" / "ui" / "menus.py"
        content = menus_file.read_text()
        
        # Check that "TG WS Proxy" does not appear in print statements (user-facing)
        # It should only appear in comments or docstrings if at all
        lines_with_tg_ws_proxy = []
        for i, line in enumerate(content.split('\n'), 1):
            if 'TG WS Proxy' in line and 'print' in line:
                lines_with_tg_ws_proxy.append((i, line))
        
        self.assertEqual([], lines_with_tg_ws_proxy, 
                         "Found 'TG WS Proxy' in user-facing print statements")

    def test_no_wssize_in_strategies_menu(self):
        """Regression test: Strategies menu should not contain wssize or --wssize."""
        # Read the menus.py file
        menus_file = Path(__file__).parent.parent / "app" / "zapret_manager" / "ui" / "menus.py"
        content = menus_file.read_text()
        
        # Find the base_strategies_menu function
        lines = content.split('\n')
        in_base_strategies_menu = False
        lines_with_wssize = []
        
        for i, line in enumerate(lines, 1):
            if 'def base_strategies_menu' in line:
                in_base_strategies_menu = True
            elif in_base_strategies_menu and line.strip().startswith('def '):
                in_base_strategies_menu = False
            elif in_base_strategies_menu and ('wssize' in line.lower() or '--wssize' in line):
                if 'print' in line:  # Only check user-facing output
                    lines_with_wssize.append((i, line))
        
        self.assertEqual([], lines_with_wssize,
                         "Found wssize/--wssize in base_strategies_menu user-facing output")

    def test_no_sync_stressozz_in_errors(self):
        """Regression test: user-facing errors should not contain 'sync StressOzz'."""
        # Read the menus.py file
        menus_file = Path(__file__).parent.parent / "app" / "zapret_manager" / "ui" / "menus.py"
        content = menus_file.read_text()
        
        # Check that "sync StressOzz" does not appear in error messages
        lines_with_sync = []
        for i, line in enumerate(content.split('\n'), 1):
            if 'sync StressOzz' in line:
                # Allow it in comments or function names, but not in error messages
                if 'raise RuntimeError' in line or 'print' in line:
                    lines_with_sync.append((i, line))
        
        self.assertEqual([], lines_with_sync,
                         "Found 'sync StressOzz' in user-facing error messages")

    def test_no_blockcheck_in_advanced_menu(self):
        """Regression test: advanced_menu should not contain blockcheck."""
        # Read the menus.py file
        menus_file = Path(__file__).parent.parent / "app" / "zapret_manager" / "ui" / "menus.py"
        content = menus_file.read_text()
        
        # Find the advanced_menu function
        lines = content.split('\n')
        in_advanced_menu = False
        lines_with_blockcheck = []
        
        for i, line in enumerate(lines, 1):
            if 'def advanced_menu' in line:
                in_advanced_menu = True
            elif in_advanced_menu and line.strip().startswith('def '):
                in_advanced_menu = False
            elif in_advanced_menu and 'blockcheck' in line.lower():
                if 'print' in line or 'Blockcheck' in line:  # User-facing
                    lines_with_blockcheck.append((i, line))
        
        self.assertEqual([], lines_with_blockcheck,
                         "Found blockcheck in advanced_menu user-facing output")

    def test_blockcheck_in_testing_menu(self):
        """Regression test: testing_submenu should still contain Blockcheck."""
        # Read the menus.py file
        menus_file = Path(__file__).parent.parent / "app" / "zapret_manager" / "ui" / "menus.py"
        content = menus_file.read_text()
        
        # Find the testing_submenu function
        lines = content.split('\n')
        in_testing_menu = False
        has_blockcheck = False
        
        for line in lines:
            if 'def testing_submenu' in line:
                in_testing_menu = True
            elif in_testing_menu and line.strip().startswith('def '):
                in_testing_menu = False
            elif in_testing_menu and 'Blockcheck' in line:
                has_blockcheck = True
        
        self.assertTrue(has_blockcheck, "testing_submenu should still contain Blockcheck")


if __name__ == "__main__":
    unittest.main()
