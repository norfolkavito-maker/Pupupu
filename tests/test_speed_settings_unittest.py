import unittest
from unittest.mock import MagicMock, patch


class TestSpeedSettings(unittest.TestCase):
    def test_get_speed_settings_defaults_and_sanitize(self):
        from app.zapret_manager.features.strategy_test import get_speed_settings

        ctx = MagicMock()
        ctx.state = MagicMock()
        # invalid values should be sanitized
        ctx.state.test = {
            "concurrency": "999",
            "connect_timeout_s": "0",
            "read_timeout_s": "-1",
            "total_domain_timeout_s": "abc",
            "max_strategy_time_s": None,
            "detailed_console_output": "1",
            "dns_cache": "",
            "deduplicate_equivalent_strategies": "0",
        }

        s = get_speed_settings(ctx)
        self.assertEqual(s["concurrency"], 16)  # clamped
        self.assertGreaterEqual(s["connect_timeout_s"], 0.1)
        self.assertGreaterEqual(s["read_timeout_s"], 0.1)
        self.assertGreaterEqual(s["total_domain_timeout_s"], 0.1)
        self.assertGreaterEqual(s["max_strategy_time_s"], 0.1)
        self.assertTrue(s["detailed_console_output"])
        self.assertFalse(s["dns_cache"])  # bool('') -> False
        self.assertFalse(s["deduplicate_equivalent_strategies"])

    def test_set_speed_settings_merges_and_saves(self):
        from app.zapret_manager.features.strategy_test import set_speed_settings

        ctx = MagicMock()
        ctx.state = MagicMock()
        ctx.state.test = {"concurrency": 4}
        ctx.paths = MagicMock()
        ctx.paths.state_file = MagicMock()

        with patch("app.zapret_manager.core.state.save_state") as mock_save:
            out = set_speed_settings(ctx, {"concurrency": 8})
            self.assertEqual(out["concurrency"], 8)
            mock_save.assert_called_once()


if __name__ == "__main__":
    unittest.main()
