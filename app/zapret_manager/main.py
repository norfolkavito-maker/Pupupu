from __future__ import annotations

import sys

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.diagnostics import github_issue_url, open_url
from app.zapret_manager.ui.main_menu import run_main_menu


def maybe_start_tray(ctx: AppContext) -> None:
    """Start optional tray icon in background (Windows-only, lazy deps).

    Must not import tray deps unless enabled in config.
    """
    tray_cfg = getattr(getattr(ctx, "config", None), "tray", None)
    if not (tray_cfg and bool(getattr(tray_cfg, "enabled", False))):
        return

    from app.zapret_manager.utils.console import C, safe_print
    from app.zapret_manager.utils.platform import is_windows

    if not is_windows():
        safe_print(f"{C.YELLOW}Tray включён в config, но доступен только на Windows.{C.RESET}")
        return

    # Lazy import: tray package itself is optional.
    from app.zapret_manager.tray.tray_app import TrayApp

    refresh_ms = int(getattr(tray_cfg, "refresh_interval_ms", 1500) or 1500)
    show_notifications = bool(getattr(tray_cfg, "show_notifications", True))

    # Best-effort: minimize console window if requested (do not hide).
    if bool(getattr(tray_cfg, "start_minimized", False)):
        try:
            import ctypes

            SW_MINIMIZE = 6
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, SW_MINIMIZE)
        except Exception:
            pass

    import threading

    t = threading.Thread(
        target=lambda: TrayApp(ctx, refresh_interval_ms=refresh_ms, show_notifications=show_notifications).run(),
        daemon=True,
        name="TrayApp",
    )
    t.start()


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    ctx = AppContext.bootstrap(argv=argv)
    exit_code = 0
    try:
        maybe_start_tray(ctx)
        exit_code = int(run_main_menu(ctx))
    finally:
        try:
            # Close session and optionally ask user to prepare a report.
            ctx.diagnostics.close(exit_code=exit_code)

            if not (getattr(ctx.config, "diagnostics", None) and ctx.config.diagnostics.enabled):
                pass
            else:
                from app.zapret_manager.utils.console import C, ask, pause

                print(
                    f"\n{C.YELLOW}Диагностика включена.{C.RESET} "
                    "Сформировать отчёт и открыть GitHub Issues?"
                )
                ans = ask("Y=да / Enter=нет: ").strip().lower()
                if ans != "y":
                    pass
                else:
                    crash_log = ctx.paths.logs_dir / "crash.log"
                    app_log = ctx.paths.logs_dir / "zapret_manager.log"
                    zip_path = ctx.diagnostics.bundle_report_zip(
                        crash_log=crash_log if crash_log.exists() else None,
                        app_log=app_log if app_log.exists() else None,
                    )

                    title = f"DedZapret report: {ctx.diagnostics.meta.session_id}"
                    body = "\n".join(
                        [
                            "Автоматический отчёт DedZapret (диагностическая сессия)",
                            "",
                            f"- session_id: {ctx.diagnostics.meta.session_id}",
                            f"- version: {ctx.diagnostics.meta.app_version}",
                            f"- git_commit: {ctx.diagnostics.meta.git_commit}",
                            f"- started_utc: {ctx.diagnostics.meta.started_utc}",
                            f"- os: {ctx.diagnostics.meta.os}",
                            f"- python: {ctx.diagnostics.meta.python}",
                            "",
                            f"ZIP (attach this file): {zip_path}",
                            "",
                            "Опиши коротко: что нажимал, что ожидал, что пошло не так.",
                        ]
                    )
                    repo = getattr(ctx.config.diagnostics.reporting, "github_repo", "norfolkavito-maker/Pupupu")
                    url = github_issue_url(repo=repo, title=title, body=body)
                    open_url(url)
                    print(f"\n{C.GREEN}Готово.{C.RESET} ZIP лежит здесь: {zip_path}")
                    pause("\nНажми Enter чтобы закрыть... ")
        except Exception:
            # Never crash on shutdown diagnostics.
            pass

    return exit_code
