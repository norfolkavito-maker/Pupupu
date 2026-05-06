import unittest


class TestTrayOptionalImports(unittest.TestCase):
    def test_import_tray_modules_without_pystray_or_pillow(self):
        # These modules must not import optional deps at import time.
        import app.zapret_manager.tray.tray_menu  # noqa: F401
        import app.zapret_manager.tray.tray_worker  # noqa: F401
        import app.zapret_manager.tray.tray_status  # noqa: F401
        import app.zapret_manager.ui.tray  # noqa: F401


if __name__ == "__main__":
    unittest.main()
