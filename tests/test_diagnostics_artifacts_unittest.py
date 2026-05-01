import json
import unittest
import tempfile
from pathlib import Path


from unittest.mock import MagicMock


class TestDiagnosticsArtifacts(unittest.TestCase):
    def _ctx(self, root: Path):
        ctx = MagicMock()
        ctx.paths = MagicMock()
        ctx.paths.root = root
        ctx.paths.data_root = root / "DedZapretData"
        ctx.paths.data_dir = ctx.paths.data_root / "data"
        ctx.paths.logs_dir = ctx.paths.data_dir / "logs"
        ctx.paths.cache_dir = ctx.paths.data_dir / "cache"
        ctx.paths.upstreams_dir = ctx.paths.data_dir / "upstreams"
        ctx.paths.lists_dir = ctx.paths.data_dir / "lists"
        ctx.paths.runtime_dir = ctx.paths.data_root / "runtime"
        ctx.paths.strategies_generated_dir = ctx.paths.data_dir / "strategies" / "generated"
        # create dirs
        for d in [
            ctx.paths.logs_dir,
            ctx.paths.cache_dir,
            ctx.paths.upstreams_dir,
            ctx.paths.lists_dir,
            ctx.paths.runtime_dir,
            ctx.paths.strategies_generated_dir,
        ]:
            Path(d).mkdir(parents=True, exist_ok=True)
        return ctx

    def test_latest_strategy_ranking_txt_created_from_json(self):
        from app.zapret_manager.features.diagnostics_artifacts import write_latest_strategy_ranking_artifact

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ctx = self._ctx(root)
            telem = ctx.paths.data_dir / "telemetry"
            telem.mkdir(parents=True, exist_ok=True)
            src = telem / "latest_strategy_ranking.json"
            src.write_text(
                json.dumps(
                    {
                        "created_at": "2026-01-01T00:00:00Z",
                        "domain_set": "default",
                        "mode": "quick",
                        "recommended": "v1",
                        "rows": [
                            {"strategy": "v1", "ok": 3, "fail": 0, "avg_ms": 100, "score": 99, "status": "ok"},
                            {"strategy": "v2", "ok": 1, "fail": 2, "avg_ms": 200, "score": 10, "status": "ok"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            out = write_latest_strategy_ranking_artifact(ctx)
            self.assertTrue(out.exists())
            txt = out.read_text(encoding="utf-8", errors="replace")
            self.assertIn("domain_set: default", txt)
            self.assertIn("Рекомендовано: v1", txt)
            self.assertIn("TOP-5", txt)

    def test_latest_strategy_ranking_txt_when_json_missing(self):
        from app.zapret_manager.features.diagnostics_artifacts import write_latest_strategy_ranking_artifact

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ctx = self._ctx(root)
            out = write_latest_strategy_ranking_artifact(ctx)
            self.assertTrue(out.exists())
            txt = out.read_text(encoding="utf-8", errors="replace")
            self.assertIn("Рейтинг стратегий ещё не создан", txt)

    def test_runtime_asset_report_detects_missing_fake(self):
        from app.zapret_manager.features.diagnostics_artifacts import build_runtime_asset_report

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ctx = self._ctx(root)

            # Make runtime/zapret tree exist but without fake files.
            zapret = ctx.paths.runtime_dir / "zapret"
            (zapret / "files" / "fake").mkdir(parents=True, exist_ok=True)
            # but no bins, no fakes

            rep = build_runtime_asset_report(ctx)
            self.assertIn("fake", rep.get("missing", {}))
            self.assertGreaterEqual(len(rep["missing"]["fake"]), 1)

    def test_flowseal_asset_report_no_crash_when_missing(self):
        from app.zapret_manager.features.diagnostics_artifacts import build_flowseal_asset_report

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ctx = self._ctx(root)
            # Do not create upstreams/flowseal
            rep = build_flowseal_asset_report(ctx)
            self.assertIsInstance(rep, dict)
            self.assertIn("flowseal_root", rep)


if __name__ == "__main__":
    unittest.main()
