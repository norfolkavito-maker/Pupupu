import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile


from app.zapret_manager.features.singbox_menu import _sb_update_subscriptions


class TestSingBoxAutoSelectActiveNode(unittest.TestCase):
    def _make_ctx(self, data_dir: Path) -> MagicMock:
        ctx = MagicMock()
        ctx.paths = MagicMock()
        ctx.paths.data_dir = data_dir
        ctx.paths.logs_dir = data_dir / "logs"
        ctx.paths.root = data_dir
        return ctx

    def test_autoselect_first_node_when_empty(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)

            # seed current state with empty active node
            st_dir = d / "state"
            st_dir.mkdir(parents=True, exist_ok=True)
            (st_dir / "current.json").write_text(
                json.dumps({"version": 1, "active_singbox_node_id": "", "processes": {"singbox": {"name": "singbox"}}}),
                encoding="utf-8",
            )

            # seed subscriptions
            sb_dir = d / "singbox"
            sb_dir.mkdir(parents=True, exist_ok=True)
            (sb_dir / "subscriptions.json").write_text(
                json.dumps(
                    [
                        {
                            "subscription_id": "1",
                            "name": "s1",
                            "url": "https://example.com/sub",
                            "enabled": True,
                            "last_update_at": "",
                            "last_error": "",
                            "node_count": 0,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            ctx = self._make_ctx(d)
            with patch("app.zapret_manager.features.singbox_menu.download_subscription_text", return_value="vless://id@h1:443#n1\n"), patch(
                "app.zapret_manager.features.singbox_menu.pause", return_value=None
            ), patch(
                "app.zapret_manager.features.singbox_menu.safe_print", return_value=None
            ), patch(
                "app.zapret_manager.features.singbox_menu.clear", return_value=None
            ):
                _sb_update_subscriptions(ctx)

            # active node should be set
            cur = json.loads((st_dir / "current.json").read_text(encoding="utf-8"))
            self.assertTrue(cur.get("active_singbox_node_id"))


if __name__ == "__main__":
    unittest.main()
