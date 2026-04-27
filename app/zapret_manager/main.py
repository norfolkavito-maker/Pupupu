from __future__ import annotations

import sys

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.diagnostics import github_issue_url, open_url
from app.zapret_manager.ui.main_menu import run_main_menu


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    ctx = AppContext.bootstrap(argv=argv)
    exit_code = 0
    try:
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

