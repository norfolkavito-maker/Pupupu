import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace


class TestTrayMenuSpec(unittest.TestCase):
    def test_build_tray_menu_spec_from_fake_status(self):
        from app.zapret_manager.core.commands import CommandResult
        from app.zapret_manager.tray.tray_menu import build_tray_menu_spec
        from app.zapret_manager.tray.tray_worker import TrayWorker

        with TemporaryDirectory() as td:
            data_dir = Path(td)
            (data_dir / "singbox").mkdir(parents=True, exist_ok=True)
            (data_dir / "singbox" / "nodes.json").write_text("[]", encoding="utf-8")

            ctx = SimpleNamespace(paths=SimpleNamespace(data_dir=data_dir))

            status = CommandResult(
                ok=True,
                message="ok",
                details={
                    "zapret": {"running": False, "active_strategy": "v7", "pid": 0, "engine_mode": "auto"},
                    "singbox": {"running": False, "pid": 0, "nodes": 0, "recommended_action": ""},
                    "problem_domains": {"count": 0},
                    "latest_ranking": {"recommended": "v7"},
                    "runtime_assets": {"ok": True, "missing_binaries": []},
                },
            )

            w = TrayWorker()
            spec = build_tray_menu_spec(ctx, w, status=status)

            titles = [it.title for it in spec.items]
            self.assertIn("Основное", titles)
            self.assertIn("VPN", titles)
            self.assertIn("Стратегии", titles)
            self.assertIn("Диагностика", titles)
            self.assertIn("Настройки", titles)

            # Check a few nested items exist.
            groups = {it.title: it for it in spec.items if it.children}
            self.assertTrue(any("Включить Recommended" == c.title for c in groups["Основное"].children))
            self.assertTrue(any("Активировать VPN" in c.title for c in groups["VPN"].children))
            self.assertTrue(any("Тест всех стратегий" in c.title for c in groups["Стратегии"].children))
            self.assertTrue(any("Открыть логи" == c.title for c in groups["Диагностика"].children))


if __name__ == "__main__":
    unittest.main()
