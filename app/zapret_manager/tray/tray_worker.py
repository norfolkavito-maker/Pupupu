from __future__ import annotations

"""Background job helper for tray actions.

Tray callbacks must return quickly; long operations should run in background.
This module provides a tiny single-job worker with cooperative cancellation.
"""

from dataclasses import dataclass
import threading
from typing import Callable


@dataclass(frozen=True)
class TrayJobSnapshot:
    name: str
    state: str  # idle|running|cancel_requested|done|error
    message: str = ""


class TrayWorker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._cancel = threading.Event()
        self._snap = TrayJobSnapshot(name="", state="idle", message="")

    def snapshot(self) -> TrayJobSnapshot:
        with self._lock:
            return self._snap

    def is_running(self) -> bool:
        with self._lock:
            return self._snap.state == "running"

    def can_start(self) -> bool:
        with self._lock:
            return self._snap.state in {"idle", "done", "error"}

    def request_cancel(self) -> bool:
        with self._lock:
            if self._snap.state != "running":
                return False
            self._cancel.set()
            self._snap = TrayJobSnapshot(name=self._snap.name, state="cancel_requested", message="Отмена...")
            return True

    def start(
        self,
        *,
        name: str,
        fn: Callable[[threading.Event], str | None],
    ) -> bool:
        """Start a new job.

        fn receives a cancel event. It should check `cancel.is_set()` periodically.
        Returned string becomes a final message.
        """
        with self._lock:
            if self._snap.state not in {"idle", "done", "error"}:
                return False
            self._cancel.clear()
            self._snap = TrayJobSnapshot(name=name, state="running", message="")

        def _run() -> None:
            try:
                msg = fn(self._cancel)
                with self._lock:
                    st = "done" if not self._cancel.is_set() else "done"
                    self._snap = TrayJobSnapshot(name=name, state=st, message=msg or "")
            except Exception as e:
                with self._lock:
                    self._snap = TrayJobSnapshot(name=name, state="error", message=f"{type(e).__name__}: {e}")

        self._thread = threading.Thread(target=_run, daemon=True, name=f"TrayJob:{name}")
        self._thread.start()
        return True
