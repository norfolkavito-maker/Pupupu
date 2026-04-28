from __future__ import annotations

import os
import subprocess
from pathlib import Path

from app.zapret_manager.core.process_supervisor import ProcessSupervisor


class SingBoxProcess:
    def __init__(
        self,
        *,
        supervisor: ProcessSupervisor,
        bin_path: Path,
        config_path: Path,
        log_file: Path,
    ) -> None:
        self.supervisor = supervisor
        self.bin_path = bin_path
        self.config_path = config_path
        self.log_file = log_file

    def start(self) -> int:
        """Start sing-box as a detached child process.

        We intentionally do NOT touch system proxy, firewall, or TUN.
        """
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        creationflags = 0
        try:
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
        except Exception:
            creationflags = 0

        # Keep file handle open in parent process; this is acceptable for long running.
        # For a future refactor we can add a rotated logger.
        f = self.log_file.open("ab")
        try:
            p = subprocess.Popen(
                [str(self.bin_path), "run", "-c", str(self.config_path)],
                stdout=f,
                stderr=f,
                stdin=subprocess.DEVNULL,
                creationflags=creationflags,
            )
        except Exception as e:
            try:
                f.close()
            except Exception:
                pass
            self.supervisor.set_process("singbox", pid=None, running=False, error=str(e))
            raise

        self.supervisor.set_process("singbox", pid=int(p.pid), running=True, error="")
        return int(p.pid)

    def stop(self, pid: int | None) -> None:
        if not pid:
            return
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False, capture_output=True)
            else:
                # Best-effort for tests/non-windows.
                os.kill(pid, 15)
        except Exception:
            pass
        self.supervisor.set_process("singbox", pid=None, running=False, error="")
