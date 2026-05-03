import unittest


class TestStrategyMetricsNA(unittest.TestCase):
    def test_summary_shows_na_for_unmeasured_metrics(self):
        from app.zapret_manager.features.strategy_test import TestResult

        r = TestResult(strategy="v1", ok=1, total=2)
        self.assertIn("HTTP: 1/2", r.summary_text())
        self.assertIn("TCP: N/A", r.summary_text())
        self.assertIn("DNS: N/A", r.summary_text())
        self.assertIn("PING: N/A", r.summary_text())
        self.assertIn("UDP443: N/A", r.summary_text())

    def test_summary_shows_ratio_when_measured(self):
        from app.zapret_manager.features.strategy_test import TestResult

        r = TestResult(
            strategy="v1",
            ok=1,
            total=2,
            tcp_ok=2,
            dns_ok=1,
            ping_ok=0,
            udp_ok=2,
            measured_tcp=True,
            measured_dns=True,
            measured_ping=True,
            measured_udp=True,
        )
        s = r.summary_text()
        self.assertIn("TCP: 2/2", s)
        self.assertIn("DNS: 1/2", s)
        self.assertIn("PING: 0/2", s)
        self.assertIn("UDP443: 2/2", s)


if __name__ == "__main__":
    unittest.main()
