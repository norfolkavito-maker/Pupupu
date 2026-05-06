import unittest
from types import SimpleNamespace
from unittest import mock


class TestTrayActions(unittest.TestCase):
    def test_apply_recommended_routes_through_commands(self):
        from app.zapret_manager.core.commands import CommandResult
        from app.zapret_manager.tray.tray_menu import handle_menu_action
        from app.zapret_manager.tray.tray_worker import TrayWorker

        ctx = SimpleNamespace()
        worker = TrayWorker()

        with mock.patch(
            "app.zapret_manager.tray.tray_menu.apply_recommended_strategy",
            return_value=CommandResult(ok=True, message="ok"),
        ) as fn:
            res = handle_menu_action(ctx=ctx, worker=worker, action_id="apply_recommended")
            self.assertIsNotNone(res)
            self.assertTrue(res.ok)
            fn.assert_called_once()

    def test_engine_mode_routes_through_commands(self):
        from app.zapret_manager.core.commands import CommandResult
        from app.zapret_manager.tray.tray_menu import handle_menu_action
        from app.zapret_manager.tray.tray_worker import TrayWorker

        ctx = SimpleNamespace()
        worker = TrayWorker()

        with mock.patch(
            "app.zapret_manager.tray.tray_menu.set_engine_mode",
            return_value=CommandResult(ok=True, message="ok"),
        ) as fn:
            res = handle_menu_action(ctx=ctx, worker=worker, action_id="engine.winws2")
            self.assertIsNotNone(res)
            self.assertTrue(res.ok)
            fn.assert_called_once()


if __name__ == "__main__":
    unittest.main()

