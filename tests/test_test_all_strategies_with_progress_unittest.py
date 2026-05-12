import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestAllStrategiesWithProgress(unittest.TestCase):
    def _make_ctx(self, tmp: Path):
        ctx = MagicMock()
        ctx.paths = MagicMock()
        ctx.paths.data_dir = tmp / "DedZapretData" / "data"
        ctx.paths.root = tmp
        ctx.paths.results_dir = tmp / "DedZapretData" / "data" / "results"
        ctx.paths.strategies_builtin_dir = tmp / "DedZapretData" / "data" / "strategies" / "builtin"
        ctx.paths.strategies_generated_dir = tmp / "DedZapretData" / "data" / "strategies" / "generated"
        ctx.paths.strategies_custom_dir = tmp / "DedZapretData" / "data" / "strategies" / "custom"
        ctx.paths.results_dir.mkdir(parents=True, exist_ok=True)
        ctx.paths.data_dir.mkdir(parents=True, exist_ok=True)
        ctx.paths.strategies_builtin_dir.mkdir(parents=True, exist_ok=True)
        ctx.paths.strategies_generated_dir.mkdir(parents=True, exist_ok=True)
        ctx.paths.strategies_custom_dir.mkdir(parents=True, exist_ok=True)
        ctx.state = MagicMock()
        ctx.state.zapret = MagicMock()
        ctx.state.zapret.running = False
        return ctx

    @patch("app.zapret_manager.features.strategy_test.test_strategy")
    @patch("app.zapret_manager.features.strategy_test.list_strategies")
    @patch("app.zapret_manager.features.strategy_test.save_strategy")
    @patch("app.zapret_manager.features.strategy_test.stop_zapret")
    @patch("app.zapret_manager.features.strategy_test.start_zapret_interactive")
    def test_quick_mode_builtin_only(self, _mock_start, _mock_stop, mock_save, mock_list, mock_test_strategy):
        from app.zapret_manager.features.strategy_test import test_all_strategies_with_progress
        from app.zapret_manager.features.strategy_test import DomainCheck

        tmp = Path("/tmp") / "dedzapret_test_quick"
        # Ensure clean-ish
        if tmp.exists():
            for p in sorted(tmp.rglob("*"), reverse=True):
                try:
                    p.unlink()
                except Exception:
                    pass
        ctx = self._make_ctx(tmp)

        # list_strategies is called for builtin/generated/custom depending on mode.
        # For quick: builtin only.
        st1 = MagicMock(); st1.name = "v1"; st1.args = []; st1.kind = "base"
        st2 = MagicMock(); st2.name = "v2"; st2.args = []; st2.kind = "base"
        def _ls(ctx, path, kind=None):
            if str(path).endswith("builtin"):
                return [st1, st2]
            return []
        mock_list.side_effect = _ls

        # Make all strategies appear OK with deterministic ms.
        r1 = MagicMock(); r1.strategy = "v1"; r1.ok = 2; r1.total = 2
        r1.checks = [
            DomainCheck(domain="example.com", url="https://example.com/", ok=True, elapsed_ms=100),
            DomainCheck(domain="test.com", url="https://test.com/", ok=True, elapsed_ms=300),
        ]
        r1.status = "ok"; r1.error = ""

        r2 = MagicMock(); r2.strategy = "v2"; r2.ok = 1; r2.total = 2
        r2.checks = [
            DomainCheck(domain="example.com", url="https://example.com/", ok=True, elapsed_ms=200),
            DomainCheck(domain="test.com", url="https://test.com/", ok=False, elapsed_ms=200, error="timeout"),
        ]
        r2.status = "ok"; r2.error = ""
        mock_test_strategy.side_effect = [r1, r2]

        summary, rows, ranking_json = test_all_strategies_with_progress(
            ctx,
            domains=["https://example.com/"],
            domain_set="default",
            mode="quick",
            parallel=None,
        )

        # Ensure list_strategies wasn't asked for generated/custom.
        calls = [str(c.args[1]) for c in mock_list.call_args_list]
        self.assertTrue(any(s.endswith("builtin") for s in calls))
        self.assertFalse(any(s.endswith("generated") for s in calls))
        self.assertFalse(any(s.endswith("custom") for s in calls))

        # JSONL created
        jsonl = (ctx.paths.data_dir / "telemetry" / "strategy_runs.jsonl")
        self.assertTrue(jsonl.exists())
        lines = [ln for ln in jsonl.read_text(encoding="utf-8").splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1)
        obj = json.loads(lines[0])
        self.assertEqual(obj["mode"], "quick")
        self.assertEqual(obj["domain_set"], "default")

        # ranking stable ordering by score/ok
        self.assertTrue(ranking_json.exists())
        payload = json.loads(ranking_json.read_text(encoding="utf-8"))
        self.assertEqual(payload["mode"], "quick")
        self.assertEqual(payload["domain_set"], "default")
        self.assertGreaterEqual(len(payload["rows"]), 1)

    def test_score_penalizes_invalid(self):
        from app.zapret_manager.features.strategy_test import _score_run

        ok_score = _score_run(ok=10, total=10, missing_assets=0, crashed=False, avg_ms=100)
        bad_score = _score_run(ok=0, total=0, missing_assets=0, crashed=True, avg_ms=0)
        self.assertGreater(ok_score, bad_score)

    @patch("app.zapret_manager.ui.menus.get_problem_domain_list", return_value=[])
    def test_problem_domains_empty_does_not_crash(self, _mock_pd):
        from app.zapret_manager.ui.menus import _choose_domain_set_extended

        ctx = MagicMock()
        ctx.state = MagicMock(); ctx.state.tg = {"domain_set": "default"}
        ctx.paths = MagicMock(); ctx.paths.data_dir = Path("/tmp")

        with patch("app.zapret_manager.ui.menus.ask", side_effect=["5"]):
            # selecting Problem domains, but list is empty -> do not fallback here
            key, domains = _choose_domain_set_extended(ctx)
            self.assertEqual(key, "problem")
            self.assertIsInstance(domains, list)
            self.assertEqual(len(domains), 0)


if __name__ == "__main__":
    unittest.main()
