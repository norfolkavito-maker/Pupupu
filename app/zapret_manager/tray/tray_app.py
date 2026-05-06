from __future__ import annotations

"""Tray application (optional).

This module uses lazy imports for pystray/Pillow.
It should not be imported unless user explicitly enables tray.
"""

import logging
import threading
import time

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.commands import get_status_summary
from app.zapret_manager.tray.tray_menu import build_tray_menu_spec, handle_menu_action
from app.zapret_manager.tray.tray_icons import get_icon
from app.zapret_manager.tray.tray_status import status_from_command_result
from app.zapret_manager.tray.tray_worker import TrayWorker


log = logging.getLogger(__name__)


def _lazy_import_pil_image():
    from PIL import Image  # type: ignore

    return Image


def _lazy_import_pystray():
    import pystray  # type: ignore

    return pystray


class TrayApp:
    def __init__(self, ctx: AppContext, *, refresh_interval_ms: int = 1500, show_notifications: bool = True) -> None:
        self.ctx = ctx
        self.refresh_interval_ms = max(300, int(refresh_interval_ms))
        self.show_notifications = bool(show_notifications)
        self.worker = TrayWorker()
        self._stop_ev = threading.Event()
        self._thread: threading.Thread | None = None
        self._icon = None
        self._last_job_state = "idle"

    def _create_placeholder_icon(self):
        Image = _lazy_import_pil_image()
        return Image.new("RGB", (64, 64), color=(70, 70, 70))

    def _notify_best_effort(self, title: str, message: str) -> None:
        if not (self.show_notifications and self._icon is not None):
            return
        try:
            # pystray supports notify on some backends; ignore if unavailable.
            self._icon.notify(str(message or title), str(title or "DedZapret"))
        except Exception:
            pass

    def _rebuild_menu(self):
        pystray = _lazy_import_pystray()
        spec = build_tray_menu_spec(self.ctx, self.worker)

        def _mk_action(action_id: str):
            def _handler(icon, item):
                if action_id == "exit":
                    try:
                        self.stop()
                    finally:
                        icon.stop()
                    return
                res = handle_menu_action(ctx=self.ctx, worker=self.worker, action_id=action_id)
                if res is not None and not res.ok:
                    log.warning("Tray action failed: %s", res.message)
                    self._notify_best_effort("DedZapret", res.message)
            return _handler

        def _convert(it):
            if getattr(it, "children", None):
                submenu = pystray.Menu(*[_convert(ch) for ch in it.children])
                return pystray.MenuItem(it.title, submenu, enabled=it.enabled)

            checked = None
            if getattr(it, "checked", None) is not None:
                want = bool(it.checked)

                def _checked(_item=None, _want=want):
                    return _want

                checked = _checked
            return pystray.MenuItem(
                it.title,
                _mk_action(it.action_id),
                enabled=it.enabled,
                checked=checked,
                radio=bool(getattr(it, "radio", False)),
            )

        return pystray.Menu(*[_convert(it) for it in spec.items])

    def _refresh_loop(self):
        while not self._stop_ev.is_set():
            try:
                # status
                res = get_status_summary(self.ctx)
                job = self.worker.snapshot()
                st = status_from_command_result(res, job=job)
                if self._icon is not None:
                    self._icon.title = st.tooltip
                    try:
                        self._icon.icon = get_icon(st.level)
                    except Exception:
                        pass
                    # rebuild menu to reflect running job state
                    self._icon.menu = self._rebuild_menu()

                # notify on job completion
                if job.state != self._last_job_state:
                    if self._last_job_state in {"running", "cancel_requested"} and job.state in {"done", "error"}:
                        msg = job.message or ("Готово" if job.state == "done" else "Ошибка")
                        self._notify_best_effort("DedZapret", msg)
                    self._last_job_state = job.state
            except Exception as e:
                log.debug("Tray refresh failed: %s", e)
            time.sleep(self.refresh_interval_ms / 1000.0)

    def run(self) -> None:
        try:
            pystray = _lazy_import_pystray()
            _ = _lazy_import_pil_image()
        except Exception as e:
            log.warning("Tray deps are missing or failed to import: %s", e)
            return
        icon = pystray.Icon(
            "DedZapret",
            self._create_placeholder_icon(),
            "DedZapret",
            menu=self._rebuild_menu(),
        )
        self._icon = icon

        self._thread = threading.Thread(target=self._refresh_loop, daemon=True, name="TrayRefresh")
        self._thread.start()
        icon.run()

    def stop(self) -> None:
        self._stop_ev.set()
