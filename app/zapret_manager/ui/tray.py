from __future__ import annotations

"""Tray icon compatibility wrapper.

New implementation lives in `app.zapret_manager.tray.*`.
This module stays as a thin wrapper to avoid breaking older imports.
"""

from app.zapret_manager.core.app_context import AppContext


class TrayIcon:
    """Backward-compatible name.

    NOTE: This wrapper does not provide thread-based run() anymore.
    Use TrayApp from `app.zapret_manager.tray.tray_app`.
    """

    def __init__(self, ctx: AppContext):
        self.ctx = ctx

    def run(self) -> None:
        from app.zapret_manager.tray.tray_app import TrayApp

        TrayApp(self.ctx).run()

    def update_status(self) -> None:
        # Status is auto-refreshed by TrayApp.
        return None
