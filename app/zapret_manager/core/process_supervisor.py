from __future__ import annotations

import logging
import time
from dataclasses import replace
from pathlib import Path

from app.zapret_manager.core.current_state import (
    ManagedProcessState,
    load_current_state,
    save_current_state,
)


log = logging.getLogger(__name__)


class ProcessSupervisor:
    """Supervisor for managed child processes.

    Phase 1-2 scope: manage ONLY sing-box.
    """

    def __init__(self, *, current_state_file: Path) -> None:
        self.current_state_file = current_state_file

    def _load(self):
        return load_current_state(self.current_state_file)

    def _save(self, st) -> None:
        save_current_state(self.current_state_file, st)

    def set_process(self, key: str, *, pid: int | None, running: bool, error: str = "", exit_code: int | None = None) -> None:
        st = self._load()
        p = st.processes.get(key) or ManagedProcessState(name=key)
        p.pid = pid
        p.running = bool(running)
        p.exit_code = exit_code
        p.last_error = error
        if running:
            p.started_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        st.processes[key] = p
        if error:
            st.last_error = error
        self._save(st)
