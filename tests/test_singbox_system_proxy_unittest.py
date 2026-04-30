import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.zapret_manager.core.singbox import system_proxy_win as sp


class TestSingBoxSystemProxy(unittest.TestCase):
    @patch("app.zapret_manager.core.singbox.system_proxy_win.os.name", "nt")
    @patch("app.zapret_manager.core.singbox.system_proxy_win._run_reg")
    def test_read_system_proxy_parses_values(self, m_run):
        m_run.return_value = """
ProxyEnable    REG_DWORD    0x1
ProxyServer    REG_SZ       127.0.0.1:2081
ProxyOverride  REG_SZ       <local>
"""
        d = sp.read_system_proxy()
        self.assertEqual(d["ProxyEnable"], 1)
        self.assertEqual(d["ProxyServer"], "127.0.0.1:2081")

    @patch("app.zapret_manager.core.singbox.system_proxy_win.write_system_proxy")
    def test_backup_and_restore(self, m_write):
        data = {"ProxyEnable": 1, "ProxyServer": "127.0.0.1:2081", "ProxyOverride": "<local>"}
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "backup.json"
            sp.backup_system_proxy(p, current=data)
            self.assertTrue(p.exists())
            sp.restore_system_proxy(p)
            m_write.assert_called()


if __name__ == "__main__":
    unittest.main()
