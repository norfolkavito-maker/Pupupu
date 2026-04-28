import unittest
from unittest.mock import MagicMock
from pathlib import Path


from app.zapret_manager.features.zapret_runtime import resolve_winws_args


class TestGameFilterPlaceholders(unittest.TestCase):
    def _make_ctx(self, *, games_profile: str = ""):
        ctx = MagicMock()
        ctx.state = MagicMock()
        ctx.state.zapret = MagicMock()
        ctx.state.zapret.games_profile = games_profile
        ctx.paths = MagicMock()
        ctx.paths.lists_dir = Path("/tmp/lists")
        ctx.paths.runtime_dir = Path("/tmp/runtime")
        return ctx

    def test_wf_tcp_placeholder_removed_when_game_disabled(self):
        ctx = self._make_ctx(games_profile="")
        args = ["--wf-tcp=443,%GameFilterTCP%,80"]
        out = resolve_winws_args(ctx, exe_dir=MagicMock(), args=args)
        self.assertEqual(out, ["--wf-tcp=443,80"])
        self.assertNotIn("%GameFilterTCP%", "\n".join(out))

    def test_wf_udp_placeholder_removed_when_game_disabled(self):
        ctx = self._make_ctx(games_profile="")
        args = ["--wf-udp=443,%GameFilterUDP%"]
        out = resolve_winws_args(ctx, exe_dir=MagicMock(), args=args)
        self.assertEqual(out, ["--wf-udp=443"])
        self.assertNotIn("%GameFilterUDP%", "\n".join(out))

    def test_filter_tcp_placeholder_arg_dropped_when_only_placeholder(self):
        ctx = self._make_ctx(games_profile="")
        args = ["--filter-tcp=%GameFilterTCP%"]
        out = resolve_winws_args(ctx, exe_dir=MagicMock(), args=args)
        self.assertEqual(out, [])

    def test_filter_udp_placeholder_arg_dropped_when_only_placeholder(self):
        ctx = self._make_ctx(games_profile="")
        args = ["--filter-udp=%GameFilterUDP%"]
        out = resolve_winws_args(ctx, exe_dir=MagicMock(), args=args)
        self.assertEqual(out, [])

    def test_placeholders_resolved_when_game_enabled(self):
        ctx = self._make_ctx(games_profile="Gv1")
        args = ["--wf-tcp=443,%GameFilterTCP%", "--wf-udp=%GameFilterUDP%"]
        out = resolve_winws_args(ctx, exe_dir=MagicMock(), args=args)
        joined = "\n".join(out)
        self.assertNotIn("%GameFilterTCP%", joined)
        self.assertNotIn("%GameFilterUDP%", joined)
        # Must keep the original explicit token too
        self.assertTrue(any(a.startswith("--wf-tcp=443,") for a in out))
        self.assertTrue(any(a.startswith("--wf-udp=") for a in out))


if __name__ == "__main__":
    unittest.main()
