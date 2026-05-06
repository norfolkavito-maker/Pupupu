import unittest


class TestTrayStatus(unittest.TestCase):
    def test_status_red_when_command_failed(self):
        from app.zapret_manager.core.commands import CommandResult
        from app.zapret_manager.tray.tray_status import status_from_command_result

        res = CommandResult(ok=False, message="fail", errors=["x"])
        st = status_from_command_result(res)
        self.assertEqual(st.level, "red")
        self.assertIn("ERROR", st.title)

    def test_status_yellow_when_problem_domains_exist(self):
        from app.zapret_manager.core.commands import CommandResult
        from app.zapret_manager.tray.tray_status import status_from_command_result

        res = CommandResult(
            ok=True,
            message="ok",
            details={
                "zapret": {"running": False, "active_strategy": "v7", "pid": 0},
                "singbox": {"running": False, "pid": 0, "nodes": 0, "recommended_action": ""},
                "problem_domains": {"count": 3},
                "runtime_assets": {"ok": True, "missing_binaries": []},
            },
        )
        st = status_from_command_result(res)
        self.assertEqual(st.level, "yellow")
        self.assertIn("Проблемные домены", st.tooltip)


if __name__ == "__main__":
    unittest.main()
