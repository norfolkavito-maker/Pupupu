import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from zapret_manager.features.hosts import clear_all_manager_blocks, has_block, set_block_enabled


class HostsBlockTests(unittest.TestCase):
    def test_hosts_block_roundtrip(self):
        with TemporaryDirectory() as td:
            hosts = Path(td) / "hosts"
            hosts.write_text("127.0.0.1 localhost\n", encoding="utf-8")

            self.assertFalse(has_block("RUTOR", path=hosts))
            set_block_enabled("RUTOR", True, path=hosts, require_admin=False)
            self.assertTrue(has_block("RUTOR", path=hosts))
            set_block_enabled("RUTOR", False, path=hosts, require_admin=False)
            self.assertFalse(has_block("RUTOR", path=hosts))

    def test_clear_all_blocks(self):
        with TemporaryDirectory() as td:
            hosts = Path(td) / "hosts"
            hosts.write_text("127.0.0.1 localhost\n", encoding="utf-8")
            set_block_enabled("RUTOR", True, path=hosts, require_admin=False)
            set_block_enabled("NTC", True, path=hosts, require_admin=False)
            self.assertTrue(has_block("RUTOR", path=hosts))
            self.assertTrue(has_block("NTC", path=hosts))
            clear_all_manager_blocks(path=hosts, require_admin=False)
            self.assertFalse(has_block("RUTOR", path=hosts))
            self.assertFalse(has_block("NTC", path=hosts))


if __name__ == "__main__":
    unittest.main()

