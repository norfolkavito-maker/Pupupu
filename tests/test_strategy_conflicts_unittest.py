import unittest


class TestStrategyConflicts(unittest.TestCase):
    def test_detects_udp443_fake_quic_conflict_when_multiple_blocks(self):
        from app.zapret_manager.features.strategy_conflicts import detect_conflicts

        args = [
            "--new",
            "--filter-udp=443",
            "--dpi-desync=fake",
            "--dpi-desync-fake-unknown-udp={FAKE:quic_initial_www_google_com.bin}",
            "--new",
            "--filter-udp=1-65535",
            "--dpi-desync=fake",
        ]
        conflicts = detect_conflicts(composed_args=args)
        self.assertTrue(conflicts)
        self.assertEqual(conflicts[0].code, "udp443_fake_quic_multi")

    def test_no_conflict_when_single_fake_quic_udp443_block(self):
        from app.zapret_manager.features.strategy_conflicts import detect_conflicts

        args = [
            "--new",
            "--filter-udp=443",
            "--dpi-desync=fake",
            "--dpi-desync-fake-unknown-udp={FAKE:quic_initial_www_google_com.bin}",
        ]
        conflicts = detect_conflicts(composed_args=args)
        self.assertEqual(conflicts, [])


if __name__ == "__main__":
    unittest.main()

