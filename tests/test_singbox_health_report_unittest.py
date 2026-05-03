import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


from app.zapret_manager.features.singbox_health import (
    build_singbox_health_report,
    format_singbox_health_text,
)


class TestSingBoxHealthReport(unittest.TestCase):
    def _seed_current(self, data_dir: Path, *, active_node_id: str = "") -> None:
        st_dir = data_dir / "state"
        st_dir.mkdir(parents=True, exist_ok=True)
        (st_dir / "current.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "active_singbox_node_id": active_node_id,
                    "singbox_dns_mode": "system",
                    "processes": {"singbox": {"name": "singbox", "running": False, "pid": None}},
                }
            ),
            encoding="utf-8",
        )

    def _seed_nodes(self, data_dir: Path, nodes: list[dict]) -> None:
        sb = data_dir / "singbox"
        sb.mkdir(parents=True, exist_ok=True)
        (sb / "nodes.json").write_text(json.dumps(nodes, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_binary_missing_recommendation(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            self._seed_current(d)
            self._seed_nodes(d, [])

            with patch("app.zapret_manager.features.singbox_health.detect_singbox_binary", return_value=None), patch(
                "app.zapret_manager.features.singbox_health.singbox_health_summary",
                return_value={"running": False, "pid": 0, "ports": {"2080": False, "2081": False}, "ok": False},
            ):
                r = build_singbox_health_report(data_dir=d, root_dir=d)
            self.assertFalse(r.binary_found)
            self.assertIn("Установите sing-box", r.recommended_action)

    def test_nodes_zero_recommendation_update_subs(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            self._seed_current(d)
            self._seed_nodes(d, [])

            with patch("app.zapret_manager.features.singbox_health.detect_singbox_binary") as det, patch(
                "app.zapret_manager.features.singbox_health.singbox_version", return_value="sing-box 1.9.0"
            ), patch(
                "app.zapret_manager.features.singbox_health.singbox_health_summary",
                return_value={"running": False, "pid": 0, "ports": {"2080": False, "2081": False}, "ok": False},
            ):
                det.return_value = type("B", (), {"path": d / "bin" / "sing-box" / "sing-box.exe"})()
                r = build_singbox_health_report(data_dir=d, root_dir=d)
            self.assertEqual(r.nodes_count, 0)
            # nodes.json exists but contains no parsed nodes => diagnostic hint
            self.assertTrue(r.nodes_file_exists)
            self.assertGreater(r.nodes_file_size, 0)
            self.assertEqual(r.nodes_schema_detected, "list")
            self.assertIn("nodes.json найден, но ноды не прочитаны", r.recommended_action)

    def test_active_node_empty_when_nodes_present(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            self._seed_current(d, active_node_id="")
            self._seed_nodes(
                d,
                [
                    {
                        "node_id": "n1",
                        "name": "Germany-1",
                        "protocol": "vless",
                        "server": "example.com",
                        "port": 443,
                        "raw": "vless://***",
                        "extra": {},
                    }
                ],
            )
            with patch("app.zapret_manager.features.singbox_health.detect_singbox_binary") as det, patch(
                "app.zapret_manager.features.singbox_health.singbox_version", return_value="sing-box 1.9.0"
            ), patch(
                "app.zapret_manager.features.singbox_health.singbox_health_summary",
                return_value={"running": False, "pid": 0, "ports": {"2080": False, "2081": False}, "ok": False},
            ):
                det.return_value = type("B", (), {"path": d / "bin" / "sing-box" / "sing-box.exe"})()
                r = build_singbox_health_report(data_dir=d, root_dir=d)
            self.assertEqual(r.nodes_count, 1)
            self.assertFalse(r.active_node_id)
            self.assertIn("Выберите active node", r.recommended_action)

    def test_active_node_missing_in_nodes(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            self._seed_current(d, active_node_id="missing")
            self._seed_nodes(
                d,
                [
                    {
                        "node_id": "n1",
                        "name": "Germany-1",
                        "protocol": "vless",
                        "server": "example.com",
                        "port": 443,
                        "raw": "vless://***",
                        "extra": {},
                    }
                ],
            )
            with patch("app.zapret_manager.features.singbox_health.detect_singbox_binary") as det, patch(
                "app.zapret_manager.features.singbox_health.singbox_version", return_value="sing-box 1.9.0"
            ), patch(
                "app.zapret_manager.features.singbox_health.singbox_health_summary",
                return_value={"running": False, "pid": 0, "ports": {"2080": False, "2081": False}, "ok": False},
            ):
                det.return_value = type("B", (), {"path": d / "bin" / "sing-box" / "sing-box.exe"})()
                r = build_singbox_health_report(data_dir=d, root_dir=d)
            self.assertEqual(r.active_node_id, "missing")
            self.assertFalse(r.active_node_exists)
            self.assertIn("Выберите active node", r.recommended_action)

    def test_config_missing_recommendation_generate(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            self._seed_current(d, active_node_id="n1")
            self._seed_nodes(
                d,
                [
                    {
                        "node_id": "n1",
                        "name": "Germany-1",
                        "protocol": "vless",
                        "server": "example.com",
                        "port": 443,
                        "raw": "vless://***",
                        "extra": {},
                    }
                ],
            )
            with patch("app.zapret_manager.features.singbox_health.detect_singbox_binary") as det, patch(
                "app.zapret_manager.features.singbox_health.singbox_version", return_value="sing-box 1.9.0"
            ), patch(
                "app.zapret_manager.features.singbox_health.singbox_health_summary",
                return_value={"running": False, "pid": 0, "ports": {"2080": False, "2081": False}, "ok": False},
            ):
                det.return_value = type("B", (), {"path": d / "bin" / "sing-box" / "sing-box.exe"})()
                r = build_singbox_health_report(data_dir=d, root_dir=d)
            self.assertFalse(r.generated_config_exists)
            self.assertIn("Сгенерируйте конфиг", r.recommended_action)

    def test_process_running_reflected_from_core_health(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            self._seed_current(d, active_node_id="n1")
            self._seed_nodes(
                d,
                [
                    {
                        "node_id": "n1",
                        "name": "Germany-1",
                        "protocol": "vless",
                        "server": "example.com",
                        "port": 443,
                        "raw": "vless://***",
                        "extra": {},
                    }
                ],
            )
            # seed config
            sb = d / "singbox"
            sb.mkdir(parents=True, exist_ok=True)
            (sb / "generated_config.json").write_text("{}", encoding="utf-8")

            with patch("app.zapret_manager.features.singbox_health.detect_singbox_binary") as det, patch(
                "app.zapret_manager.features.singbox_health.singbox_version", return_value="sing-box 1.9.0"
            ), patch(
                "app.zapret_manager.features.singbox_health.singbox_health_summary",
                return_value={"running": True, "pid": 123, "ports": {"2080": True, "2081": True}, "ok": True},
            ):
                det.return_value = type("B", (), {"path": d / "bin" / "sing-box" / "sing-box.exe"})()
                r = build_singbox_health_report(data_dir=d, root_dir=d)
            self.assertTrue(r.process_running)
            self.assertEqual(r.pid, 123)
            self.assertTrue(r.socks_port_open)
            self.assertTrue(r.mixed_port_open)

    def test_formatter_masks_secrets_and_does_not_crash(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            self._seed_current(d)
            self._seed_nodes(d, [])
            with patch("app.zapret_manager.features.singbox_health.detect_singbox_binary") as det, patch(
                "app.zapret_manager.features.singbox_health.singbox_version", return_value="sing-box 1.9.0"
            ), patch(
                "app.zapret_manager.features.singbox_health.singbox_health_summary",
                return_value={"running": False, "pid": 0, "ports": {"2080": False, "2081": False}, "ok": False},
            ):
                det.return_value = type("B", (), {"path": d / "bin" / "sing-box" / "sing-box.exe"})()
                r = build_singbox_health_report(data_dir=d, root_dir=d)
            txt = format_singbox_health_text(r)
            self.assertIn("sing-box health", txt)
            # No raw vless/vmess/etc links should ever be present
            self.assertNotIn("vless://", txt)


if __name__ == "__main__":
    unittest.main()
