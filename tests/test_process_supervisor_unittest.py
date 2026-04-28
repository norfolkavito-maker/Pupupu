import unittest
from pathlib import Path
import tempfile


from app.zapret_manager.core.process_supervisor import ProcessSupervisor
from app.zapret_manager.core.current_state import load_current_state


class TestProcessSupervisor(unittest.TestCase):
    def test_set_process_persists(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "current.json"
            sup = ProcessSupervisor(current_state_file=p)
            sup.set_process("singbox", pid=123, running=True)
            st = load_current_state(p)
            self.assertEqual(st.processes["singbox"].pid, 123)
            self.assertTrue(st.processes["singbox"].running)


if __name__ == "__main__":
    unittest.main()
