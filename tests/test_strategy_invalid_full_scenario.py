import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
from pathlib import Path

from app.zapret_manager.features.strategy_test import test_strategy
from app.zapret_manager.features.zapret_runtime import WinwsStartError
from app.zapret_manager.strategies.model import Strategy


class TestStrategyInvalidFullScenario(unittest.TestCase):
    def test_full_invalid_scenario_no_domain_checks(self):
        """Test complete invalid scenario: winws failed, no domain checks, status=invalid, error contains reason."""
        
        # Mock context
        class _Zapret:
            running = False
            base_strategy = ""
            selected_strategy = ""
            youtube_layer = ""
            discord_layer = ""
            discord_script = ""
            games_profile = ""
            rkn_enabled = False
            wssize_enabled = False

        class _Runtime:
            installed = True
            winws_path = "C:/winws.exe"
            winws2_path = ""

        class _State:
            zapret = _Zapret()
            runtime = _Runtime()

        class _Paths:
            state_file = None
            logs_dir = Path(tempfile.mkdtemp())
            results_dir = Path(tempfile.mkdtemp())

        class _Ctx:
            state = _State()
            paths = _Paths()

        ctx = _Ctx()
        st = Strategy(name="v1", engine="winws", args=["--new"], kind="base")
        test_domains = ["https://example.com/", "https://google.com/"]
        
        # Mock stderr content
        mock_stderr = "winws failed to start: WinDivert driver not loaded\n"
        
        with patch("app.zapret_manager.features.strategy_test.stop_zapret") as mock_stop, \
             patch("app.zapret_manager.features.strategy_test.start_zapret_interactive") as mock_start, \
             patch("app.zapret_manager.features.strategy_test.check_domains_detailed") as mock_check:
            
            # Configure mocks
            mock_start.side_effect = WinwsStartError(
                message="winws запустился, но завершился сразу — стратегия не активна",
                stderr_tail=mock_stderr
            )
            
            # Run test
            result = test_strategy(
                ctx, 
                st, 
                test_domains, 
                parallel=1, 
                show_progress=False
            )
            
            # Verify invalid status
            self.assertEqual(result.status, "invalid")
            self.assertIn("winws", result.error)
            self.assertIn("завершился сразу", result.error)
            
            # Verify no domain checks were run
            self.assertEqual(len(result.checks), 0)
            
            # Verify domain checks were not called
            mock_check.assert_not_called()
            
            # Verify stop was called (cleanup)
            mock_stop.assert_called()
            
        # Cleanup temp dirs
        shutil.rmtree(ctx.paths.logs_dir, ignore_errors=True)
        shutil.rmtree(ctx.paths.results_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()