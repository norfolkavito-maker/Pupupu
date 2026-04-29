import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.zapret_manager.ui.menus import _run_control_test, _domains_for_current_set
from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.state import AppState


class TestControlTestMenuCall(unittest.TestCase):
    """Regression tests for control_test menu call with domains."""

    def _make_ctx(self, domain_set="default"):
        """Create a minimal AppContext for testing."""
        ctx = MagicMock(spec=AppContext)
        ctx.state = MagicMock(spec=AppState)
        ctx.state.tg = {}
        ctx.state.zapret = MagicMock()
        ctx.paths = MagicMock()
        ctx.paths.results_dir = Path("/tmp/test_results")
        # Setup domain set
        ctx.state.tg = {"domain_set": domain_set}
        return ctx

    @patch("app.zapret_manager.ui.menus.control_test_mode")
    @patch("app.zapret_manager.ui.menus._domains_for_current_set")
    @patch("app.zapret_manager.ui.menus.write_results")
    @patch("app.zapret_manager.ui.menus.pause")
    @patch("app.zapret_manager.ui.menus._choose_test_mode", return_value="quick")
    def test_control_test_passes_domains(self, _mock_mode, mock_pause, mock_write, mock_domains, mock_control):
        """Test that _run_control_test passes domains to control_test_mode."""
        ctx = self._make_ctx()
        test_domains = ["https://example.com/", "https://test.com/"]
        mock_domains.return_value = test_domains
        
        # Mock control_test_mode return value
        mock_result = MagicMock()
        mock_result.summary_text.return_value = "OK 10/10"
        mock_control.return_value = mock_result
        
        _run_control_test(ctx)
        
        # Verify control_test_mode was called with ctx and domains
        mock_control.assert_called_once_with(ctx, test_domains, mode="quick", parallel=8, progress=True)
        # Verify write_results was called
        mock_write.assert_called_once()
        # Verify pause was called
        mock_pause.assert_called_once()

    @patch("app.zapret_manager.ui.menus.control_test_mode")
    @patch("app.zapret_manager.ui.menus._domains_for_current_set")
    @patch("app.zapret_manager.ui.menus.pause")
    @patch("app.zapret_manager.ui.menus.safe_print")
    def test_empty_domain_set_shows_error(self, mock_safe_print, mock_pause, mock_domains, mock_control):
        """Test that empty domain set shows error message, not traceback."""
        ctx = self._make_ctx()
        mock_domains.return_value = []  # Empty domains
        
        _run_control_test(ctx)
        
        # control_test_mode should NOT be called
        mock_control.assert_not_called()
        mock_safe_print.assert_called()
        # pause should be called to let user read the message
        mock_pause.assert_called_once()

    @patch("app.zapret_manager.ui.menus.control_test_mode")
    @patch("app.zapret_manager.ui.menus._domains_for_current_set")
    @patch("app.zapret_manager.ui.menus.write_results")
    @patch("app.zapret_manager.ui.menus.pause")
    @patch("app.zapret_manager.ui.menus._choose_test_mode", return_value="quick")
    def test_control_test_with_selected_domain_set(self, _mock_mode, mock_pause, mock_write, mock_domains, mock_control):
        """Test that control_test_mode uses the selected domain set."""
        ctx = self._make_ctx(domain_set="youtube")
        test_domains = ["https://youtube.com/", "https://googlevideo.com/"]
        mock_domains.return_value = test_domains
        
        mock_result = MagicMock()
        mock_result.summary_text.return_value = "OK"
        mock_control.return_value = mock_result
        
        _run_control_test(ctx)
        
        # Verify _domains_for_current_set was called
        mock_domains.assert_called_once_with(ctx)
        # Verify control_test received the domains
        mock_control.assert_called_once_with(ctx, test_domains, mode="quick", parallel=8, progress=True)

    def test_no_old_call_control_test_ctx_only(self):
        """Verify there are no old-style control_test(ctx) calls in menus.py."""
        import inspect
        from app.zapret_manager.ui import menus
        
        source = inspect.getsource(menus)
        # Check that control_test is called with at least 2 arguments (ctx and domains)
        # This is a static analysis to ensure we don't regress
        lines = source.split("\n")
        for i, line in enumerate(lines):
            # Only check calls to control_test, not _run_control_test
            if "control_test(" in line and "_run_control_test(" not in line and "def " not in line:
                # Check if it's called with ctx as first arg
                # Simple check: ensure no line has "control_test(ctx)" without domains
                stripped = line.strip()
                if "control_test(ctx)" in stripped or "control_test(ctx,)" in stripped:
                    # This would be the old broken call
                    self.fail(f"Found old-style control_test(ctx) call at line {i+1}: {stripped}")


class TestDomainsForCurrentSet(unittest.TestCase):
    """Tests for _domains_for_current_set helper."""

    def test_returns_list(self):
        """Test that _domains_for_current_set returns a list."""
        ctx = MagicMock()
        ctx.state = MagicMock()
        ctx.state.tg = {"domain_set": "default"}
        
        # Mock DOMAIN_SETS with a mock object
        mock_ds = MagicMock()
        mock_ds.key = "default"
        mock_ds.file_path.return_value = Path("/tmp/test.txt")
        
        with patch("app.zapret_manager.ui.menus.DOMAIN_SETS", [mock_ds]):
            with patch("app.zapret_manager.ui.menus.read_domain_set_file", return_value=["example.com", "test.com"]):
                result = _domains_for_current_set(ctx)
                self.assertIsInstance(result, list)
                self.assertGreater(len(result), 0)

    def test_empty_domains_fallback(self):
        """Test that when domain set is empty, fallback to DEFAULT_TEST_DOMAINS."""
        ctx = MagicMock()
        ctx.state = MagicMock()
        ctx.state.tg = {"domain_set": "default"}
        
        # Mock DOMAIN_SETS with a mock object
        mock_ds = MagicMock()
        mock_ds.key = "default"
        mock_ds.file_path.return_value = Path("/tmp/test.txt")
        
        with patch("app.zapret_manager.ui.menus.DOMAIN_SETS", [mock_ds]):
            with patch("app.zapret_manager.ui.menus.read_domain_set_file", return_value=[]):
                with patch("app.zapret_manager.ui.menus.DEFAULT_TEST_DOMAINS", ["example.com", "test.com"]):
                    result = _domains_for_current_set(ctx)
                    self.assertIsInstance(result, list)


if __name__ == "__main__":
    unittest.main()