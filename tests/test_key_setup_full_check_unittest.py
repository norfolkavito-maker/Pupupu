import unittest
from unittest.mock import MagicMock, patch


from app.zapret_manager.features.key_setup import key_setup_full_check


class TestKeySetupFullCheck(unittest.TestCase):
    """Regression: key_setup_full_check must call control_test(ctx, domains, ...)."""

    @patch("app.zapret_manager.features.key_setup.ask", return_value="")
    @patch("app.zapret_manager.features.key_setup.stop_zapret")
    @patch("app.zapret_manager.features.key_setup.require_runtime_ok")
    @patch("app.zapret_manager.features.key_setup.update_exclude")
    @patch("app.zapret_manager.features.key_setup.sync_flowseal")
    @patch("app.zapret_manager.features.key_setup.sync_stressozz_strategies")
    @patch("app.zapret_manager.features.key_setup.test_session")
    @patch("app.zapret_manager.features.key_setup.prepare_urls")
    @patch("app.zapret_manager.features.key_setup.combine_domain_sets")
    @patch("app.zapret_manager.features.key_setup.control_test")
    def test_control_test_called_with_ctx(
        self,
        mock_control,
        mock_combine,
        mock_prepare,
        _mock_test_session,
        _mock_sync_so,
        _mock_sync_fs,
        _mock_update_excl,
        _mock_require_rt,
        _mock_stop,
        _mock_ask,
    ):
        ctx = MagicMock()
        ctx.state = MagicMock()
        ctx.paths = MagicMock()

        # hosts backup calls
        with patch("app.zapret_manager.features.key_setup.HostsManager") as HM:
            inst = HM.return_value
            inst.backup.return_value = None

            mock_combine.return_value = ["example.com"]
            # prepare_urls returns list of objects with .url
            u = MagicMock()
            u.url = "https://example.com/"
            mock_prepare.return_value = [u]

            res = MagicMock()
            res.summary_text.return_value = "OK"
            mock_control.return_value = res

            # exercise
            key_setup_full_check(ctx)

        # Verify: first arg is ctx
        args, kwargs = mock_control.call_args
        self.assertTrue(args and args[0] is ctx, "control_test first arg must be ctx")


if __name__ == "__main__":
    unittest.main()
