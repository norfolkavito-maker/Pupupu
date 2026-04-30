import tempfile
import unittest
from pathlib import Path

from app.zapret_manager.core.singbox.binary import detect_singbox_binary


class TestSingBoxBinary(unittest.TestCase):
    def test_detect_singbox_binary_missing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertIsNone(detect_singbox_binary(root))

    def test_detect_singbox_binary_found(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / "bin" / "sing-box" / "sing-box.exe"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"MZ")
            b = detect_singbox_binary(root)
            self.assertIsNotNone(b)
            self.assertEqual(b.path, p.resolve())


if __name__ == "__main__":
    unittest.main()
