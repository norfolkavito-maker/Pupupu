import unittest


from app.zapret_manager.utils.subprocessx import decode_bytes_best_effort


class TestWindowsDecodeCp866(unittest.TestCase):
    def test_decode_cp866_fallback(self):
        # "Привет" in cp866
        raw = bytes([0x8f, 0xe0, 0xa8, 0xa2, 0xa5, 0xe2])
        text, enc = decode_bytes_best_effort(raw, preferred="utf-8")
        self.assertEqual(text, "Привет")
        self.assertEqual(enc, "cp866")


if __name__ == "__main__":
    unittest.main()
