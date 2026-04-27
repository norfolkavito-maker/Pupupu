import unittest
import tempfile
import subprocess
import time
from pathlib import Path

from app.zapret_manager.utils.subprocessx import popen_detached


class TestPopenDetachedHandles(unittest.TestCase):
    def test_stdout_stderr_handles_leak(self):
        """Test that parent closes handles but child continues writing to files."""
        
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            stdout_path = td_path / "stdout.log"
            stderr_path = td_path / "stderr.log"
            
            # Start a detached process that writes to files
            echo_script = []
            echo_script.append("import sys")
            echo_script.append("import time")
            echo_script.append("with open(sys.argv[1], 'a', encoding='utf-8') as f:")
            echo_script.append("    f.write('stdout\\n')")
            echo_script.append("with open(sys.argv[2], 'a', encoding='utf-8') as f:")
            echo_script.append("    f.write('stderr\\n')")
            echo_script.append("time.sleep(0.1)")
            echo_script.append("with open(sys.argv[1], 'a', encoding='utf-8') as f:")
            echo_script.append("    f.write('stdout again\\n')")
            echo_script.append("with open(sys.argv[2], 'a', encoding='utf-8') as f:")
            echo_script.append("    f.write('stderr again\\n')")
            
            py_script = td_path / "echo_script.py"
            py_script.write_text("\n".join(echo_script), encoding="utf-8")
            
            # Start the detached process
            p = popen_detached(
                ["python3", str(py_script), str(stdout_path), str(stderr_path)],
                cwd=td_path,
                stdout_path=stdout_path,
                stderr_path=stderr_path
            )
            
            # Wait for process to complete
            p.wait(timeout=5.0)
            
            # Check that files contain the expected content
            stdout_content = stdout_path.read_text(encoding="utf-8")
            stderr_content = stderr_path.read_text(encoding="utf-8")
            
            self.assertIn("stdout", stdout_content)
            self.assertIn("stdout again", stdout_content)
            self.assertIn("stderr", stderr_content)
            self.assertIn("stderr again", stderr_content)
            
            # Verify process is terminated
            self.assertFalse(p.poll() is None, "Process should be terminated")


if __name__ == "__main__":
    unittest.main()