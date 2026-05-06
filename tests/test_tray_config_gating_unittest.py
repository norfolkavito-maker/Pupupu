import unittest
from types import SimpleNamespace
from unittest import mock


class TestTrayConfigGating(unittest.TestCase):
    def test_tray_disabled_does_not_import_tray_package(self):
        from app.zapret_manager.main import maybe_start_tray

        ctx = SimpleNamespace(config=SimpleNamespace(tray=SimpleNamespace(enabled=False)))

        real_import = __import__

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.startswith("app.zapret_manager.tray"):
                raise AssertionError("tray package must not be imported when tray.enabled=false")
            return real_import(name, globals, locals, fromlist, level)

        with mock.patch("builtins.__import__", side_effect=guarded_import):
            maybe_start_tray(ctx)  # must be a no-op

    def test_tray_enabled_but_non_windows_does_not_import_tray_package(self):
        from app.zapret_manager.main import maybe_start_tray

        ctx = SimpleNamespace(config=SimpleNamespace(tray=SimpleNamespace(enabled=True)))

        real_import = __import__

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.startswith("app.zapret_manager.tray"):
                raise AssertionError("tray package must not be imported on non-Windows")
            return real_import(name, globals, locals, fromlist, level)

        with mock.patch("builtins.__import__", side_effect=guarded_import):
            maybe_start_tray(ctx)  # on non-Windows should print a warning and return


if __name__ == "__main__":
    unittest.main()

