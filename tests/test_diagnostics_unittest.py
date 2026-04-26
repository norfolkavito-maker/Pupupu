from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class DiagnosticsTests(unittest.TestCase):
    def test_recorder_writes_jsonl_and_bundles_zip(self):
        from app.zapret_manager.core.diagnostics import SessionRecorder

        with tempfile.TemporaryDirectory() as td:
            logs = Path(td)
            rec = SessionRecorder(logs_dir=logs, enabled=True)
            rec.log("ui.input", "console", {"answer": "1"})
            rec.close(exit_code=0)

            self.assertTrue(rec.session_file.exists())
            lines = rec.session_file.read_text(encoding="utf-8").splitlines()
            self.assertGreaterEqual(len(lines), 2)
            obj = json.loads(lines[0])
            self.assertEqual(obj["category"], "session.start")

            z = rec.bundle_report_zip()
            self.assertTrue(z.exists())
