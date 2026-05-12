import unittest
from unittest.mock import patch


from app.zapret_manager.features.strategy_test import test_strategy
from app.zapret_manager.features.zapret_runtime import WinwsStartError
from app.zapret_manager.strategies.model import Strategy, Command, CommandType


class TestStrategyInvalidWhenWinwsFails(unittest.TestCase):
    def test_strategy_returns_invalid_and_skips_domain_checks(self):
        # minimal ctx stub
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

        class _Ctx:
            state = _State()
            paths = _Paths()

        ctx = _Ctx()
        st = Strategy(id="v1", name="v1", commands=[Command(type=CommandType.WINWS, command="--new")], engine="winws", kind="base")

        with patch("app.zapret_manager.features.strategy_test.stop_zapret") as _stop, patch(
            "app.zapret_manager.features.strategy_test.start_zapret_interactive",
            side_effect=WinwsStartError("winws died"),
        ) as _start, patch(
            "app.zapret_manager.features.strategy_test.check_domains_detailed"
        ) as _check:
            r = test_strategy(ctx, st, ["https://example.com/"], parallel=1, show_progress=False)
            self.assertEqual(r.status, "invalid")
            self.assertIn("winws", r.error)
            _check.assert_not_called()


if __name__ == "__main__":
    unittest.main()
