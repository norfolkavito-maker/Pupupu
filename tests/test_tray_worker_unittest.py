import time
import unittest


class TestTrayWorker(unittest.TestCase):
    def test_single_job_lock_and_cancel(self):
        from app.zapret_manager.tray.tray_worker import TrayWorker

        w = TrayWorker()
        self.assertTrue(w.can_start())

        def _job(cancel):
            # spin a bit
            for _ in range(50):
                if cancel.is_set():
                    return "cancelled"
                time.sleep(0.001)
            return "done"

        self.assertTrue(w.start(name="t1", fn=_job))
        self.assertFalse(w.can_start())
        self.assertTrue(w.request_cancel())

        # wait for completion
        for _ in range(1000):
            if w.snapshot().state in {"done", "error"}:
                break
            time.sleep(0.001)
        self.assertIn(w.snapshot().state, {"done", "error"})

        # now should allow start
        self.assertTrue(w.can_start())


if __name__ == "__main__":
    unittest.main()
