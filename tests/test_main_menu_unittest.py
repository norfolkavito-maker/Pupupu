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
    def test_main_menu_shows_simplified_structure(self, mock_clear, mock_ask, mock_pause):
        """Test that main menu shows simplified 11-item structure."""
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
        
        # Test that choice 2 (Быстрый статус) calls auto_setup_menu
        with patch("app.zapret_manager.ui.menus.auto_setup_menu") as mock_auto:
            with patch("app.zapret_manager.ui.main_menu.ask") as mock_ask:
                mock_ask.side_effect = ["2", ""]  # пункт, потом выход
                with patch("app.zapret_manager.ui.main_menu.pause"):
                    with patch("app.zapret_manager.ui.main_menu.clear"):
                        with patch("app.zapret_manager.ui.main_menu._show_status_summary"):
                            run_main_menu(ctx)
                            mock_auto.assert_called_once_with(ctx)


if __name__ == "__main__":
    unittest.main()
