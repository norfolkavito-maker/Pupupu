import unittest
from types import SimpleNamespace


class TestCommandResult(unittest.TestCase):
    def test_success_shape(self):
        from app.zapret_manager.core.commands import success

        r = success("OK", details={"a": 1}, warnings=["w"])
        self.assertTrue(r.ok)
        self.assertEqual(r.message, "OK")
        self.assertEqual(r.details["a"], 1)
        self.assertEqual(r.warnings, ["w"])
        self.assertEqual(r.errors, [])

    def test_failure_shape(self):
        from app.zapret_manager.core.commands import failure

        r = failure("bad", errors=["e1"], details={"x": "y"})
        self.assertFalse(r.ok)
        self.assertEqual(r.message, "bad")
        self.assertEqual(r.errors, ["e1"])
        self.assertEqual(r.details["x"], "y")

    def test_to_dict_converts_paths(self):
        from pathlib import Path

        from app.zapret_manager.core.commands import CommandResult

        r = CommandResult(ok=True, message="m", details={"p": Path("/tmp/x")})
        d = r.to_dict()
        self.assertEqual(d["details"]["p"], "/tmp/x")


class TestCommands(unittest.TestCase):
    def test_from_exception_no_crash(self):
        from app.zapret_manager.core.commands import from_exception

        r = from_exception(RuntimeError("boom"))
        self.assertFalse(r.ok)
        self.assertTrue(r.errors)

    def test_stop_all_no_crash_when_nothing_running(self):
        # Create minimal ctx with required paths/state.
        ctx = SimpleNamespace(
            paths=SimpleNamespace(
                data_dir=__import__("pathlib").Path("/tmp"),
                root=__import__("pathlib").Path("/tmp"),
                logs_dir=__import__("pathlib").Path("/tmp"),
                state_file=__import__("pathlib").Path("/tmp/state.json"),
                config_file=__import__("pathlib").Path("/tmp/config.yaml"),
            ),
            state=SimpleNamespace(zapret=SimpleNamespace(running=False, pid=None, base_strategy="", selected_strategy="")),
        )

        from app.zapret_manager.core.commands import stop_all

        r = stop_all(ctx)
        self.assertIsNotNone(r.ok)
        self.assertIn("stopped", r.details)
        self.assertIn("skipped", r.details)

    def test_singbox_health_command_returns_text_and_report(self):
        from pathlib import Path
        from unittest.mock import patch

        # Minimal ctx with required fields
        ctx = SimpleNamespace(
            paths=SimpleNamespace(data_dir=Path("/tmp"), root=Path("/tmp")),
        )

        from app.zapret_manager.core.commands import singbox_health
        from app.zapret_manager.features.singbox_health import SingBoxHealthReport

        fake_rep = SingBoxHealthReport(
            binary_found=False,
            binary_path="",
            version_ok=False,
            version_text="",
            version_error="",
            nodes_file_exists=False,
            nodes_file_size=0,
            nodes_schema_detected="",
            load_nodes_error="",
            subscriptions_count=0,
            nodes_count=0,
            active_node_id="",
            active_node_exists=False,
            active_node_summary_masked="",
            generated_config_exists=False,
            config_validate_ok=False,
            config_validate_error="generated_config.json отсутствует",
            process_running=False,
            pid=0,
            socks_port_open=False,
            mixed_port_open=False,
            last_error="",
            recommended_action="Установите sing-box",
        )

        # commands.singbox_health imports helpers from features.singbox_health inside the function,
        # so we patch the original module functions.
        with patch("app.zapret_manager.features.singbox_health.build_singbox_health_report", return_value=fake_rep):
            with patch("app.zapret_manager.features.singbox_health.format_singbox_health_text", return_value="health text"):
                r = singbox_health(ctx)
        self.assertTrue(r.ok)
        self.assertIn("text", r.details)
        self.assertIn("report", r.details)

    def test_create_bug_report_handles_exception(self):
        from pathlib import Path
        from unittest.mock import patch

        ctx = SimpleNamespace(
            paths=SimpleNamespace(
                data_dir=Path("/tmp"),
                root=Path("/tmp"),
                logs_dir=Path("/tmp"),
                state_file=Path("/tmp/state.json"),
                config_file=Path("/tmp/config.yaml"),
            )
        )

        from app.zapret_manager.core.commands import create_bug_report

        # create_bug_report imports generate_bug_report_zip from core.report inside the function.
        with patch("app.zapret_manager.core.report.generate_bug_report_zip", side_effect=RuntimeError("boom")):
            r = create_bug_report(ctx)
        self.assertFalse(r.ok)
        self.assertTrue(r.errors)


if __name__ == "__main__":
    unittest.main()
