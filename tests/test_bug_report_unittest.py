import unittest
from pathlib import Path
import tempfile
import zipfile


from app.zapret_manager.core.report import generate_bug_report_zip


class TestBugReport(unittest.TestCase):
    def test_report_zip_created_and_masked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            logs = root / "logs"
            logs.mkdir(parents=True, exist_ok=True)
            (logs / "app.log").write_text(
                "vless://123e4567-e89b-12d3-a456-426614174000@example.com:443\n",
                encoding="utf-8",
            )
            state = root / "state.json"
            state.write_text('{"uuid": "123e4567-e89b-12d3-a456-426614174000"}', encoding="utf-8")
            cur = root / "current.json"
            cur.write_text('{"subscription_url": "https://secret.example/sub"}', encoding="utf-8")
            cfg = root / "config.yaml"
            cfg.write_text("password: secret\n", encoding="utf-8")

            out = generate_bug_report_zip(
                out_dir=root / "reports",
                logs_dir=logs,
                state_file=state,
                current_state_file=cur,
                config_file=cfg,
            )
            self.assertTrue(out.exists())
            with zipfile.ZipFile(out, "r") as z:
                # meta exists
                self.assertIn("meta.json", z.namelist())
                content = z.read("logs/app.log").decode("utf-8", errors="replace")
                self.assertNotIn("123e4567-e89b-12d3-a456-426614174000", content)
                self.assertNotIn("vless://123e", content)


    def test_report_zip_includes_problem_domains_extra_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            logs = root / "logs"
            logs.mkdir(parents=True, exist_ok=True)
            (logs / "app.log").write_text("hello\n", encoding="utf-8")

            state = root / "state.json"
            state.write_text("{}", encoding="utf-8")
            cur = root / "current.json"
            cur.write_text("{}", encoding="utf-8")
            cfg = root / "config.yaml"
            cfg.write_text("{}\n", encoding="utf-8")

            pd_json = root / "problem_domains.json"
            pd_json.write_text(
                '{"schema_version":2,"domains":{"example.com":{"first_seen":"2026-01-01T00:00:00Z","last_seen":"2026-01-01T00:00:00Z","fail_count":1,"last_error":"timeout","last_strategy":"v1","best_strategy":"","status":"failing","notes":""}}}\n',
                encoding="utf-8",
            )
            pd_txt = root / "problem_domains_summary.txt"
            pd_txt.write_text("Проблемные домены: всего 1\n", encoding="utf-8")

            out = generate_bug_report_zip(
                out_dir=root / "reports",
                logs_dir=logs,
                state_file=state,
                current_state_file=cur,
                config_file=cfg,
                extra_files=[pd_json, pd_txt],
            )
            self.assertTrue(out.exists())
            with zipfile.ZipFile(out, "r") as z:
                names = set(z.namelist())
                self.assertIn("extra/problem_domains.json", names)
                self.assertIn("extra/problem_domains_summary.txt", names)


if __name__ == "__main__":
    unittest.main()
