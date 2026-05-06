from __future__ import annotations

"""Unified commands layer.

Goal
----
Provide a thin orchestration API for future frontends (tray/GUI/autostart/watcher)
without refactoring the whole app. Commands must:
- keep existing feature modules as source of business logic;
- return structured results (no raw exceptions);
- avoid leaking secrets in messages/text;
- remain lightweight by default (no heavy network operations unless explicitly
  invoked by a command like update_subscriptions).

This module intentionally does NOT implement any UI.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CommandResult:
    ok: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        # Keep json-friendly primitives only.
        def _coerce(v: Any) -> Any:
            if isinstance(v, Path):
                # Use stable forward-slash representation for logs/telemetry.
                return v.as_posix()
            if isinstance(v, (list, tuple)):
                return [_coerce(x) for x in v]
            if isinstance(v, dict):
                return {str(k): _coerce(val) for k, val in v.items()}
            return v

        return {
            "ok": bool(self.ok),
            "message": str(self.message),
            "details": _coerce(dict(self.details)),
            "warnings": [str(x) for x in self.warnings],
            "errors": [str(x) for x in self.errors],
        }


def success(
    message: str,
    details: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
) -> CommandResult:
    return CommandResult(ok=True, message=message, details=details or {}, warnings=warnings or [], errors=[])


def failure(
    message: str,
    errors: list[str] | None = None,
    details: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
) -> CommandResult:
    return CommandResult(ok=False, message=message, details=details or {}, warnings=warnings or [], errors=errors or [])


def from_exception(exc: BaseException, message: str = "Ошибка выполнения команды") -> CommandResult:
    # Never propagate raw exception upstream; keep minimal data.
    err = f"{type(exc).__name__}: {exc}"
    try:
        from app.zapret_manager.core.mask import mask_secrets_text

        err = mask_secrets_text(err)
        message = mask_secrets_text(message)
    except Exception:
        pass
    return failure(message, errors=[err])


# ---------------------------- commands ----------------------------


def get_status_summary(ctx) -> CommandResult:
    """Lightweight status summary for tray/GUI.

    No heavy network operations.
    """
    try:
        from app.zapret_manager.core.mask import mask_secrets_text
        from app.zapret_manager.features.diagnostics_artifacts import build_runtime_asset_report
        from app.zapret_manager.features.singbox_health import build_singbox_health_report
        from app.zapret_manager.features.problem_domains import load_problem_domains

        # zapret state
        zap = getattr(getattr(ctx, "state", None), "zapret", None)
        active_strategy = ""
        engine_mode = "auto"
        if zap:
            # selected_strategy is preferred, fallback to base_strategy
            active_strategy = str(getattr(zap, "selected_strategy", "") or getattr(zap, "base_strategy", "") or "").strip()
            engine_mode = str(getattr(zap, "engine_mode", "auto") or "auto").strip().lower() or "auto"

        running = bool(getattr(zap, "running", False)) if zap else False
        pid = getattr(zap, "pid", None) if zap else None
        pid_int = int(pid) if pid else 0
        pid_alive: bool | None = None
        try:
            from app.zapret_manager.utils.platform import is_windows

            if is_windows() and pid_int:
                from app.zapret_manager.features.zapret_runtime import is_pid_alive

                pid_alive = bool(is_pid_alive(pid_int))
        except Exception:
            pid_alive = None

        # sing-box short health (cheap)
        sb = build_singbox_health_report(data_dir=ctx.paths.data_dir, root_dir=ctx.paths.root)

        # problem domains count
        pd = load_problem_domains(ctx)
        pd_count = len(getattr(pd, "domains", []) or [])

        # latest ranking recommended strategy (cheap local file read)
        recommended = ""
        try:
            p = (ctx.paths.data_dir / "telemetry" / "latest_strategy_ranking.json").resolve()
            if p.exists():
                import json

                obj = json.loads(p.read_text(encoding="utf-8", errors="replace"))
                if isinstance(obj, dict):
                    rows = obj.get("rows")
                    if isinstance(rows, list):
                        # pick best ok row by rank (file is rank-sorted)
                        ok_rows = [r for r in rows if isinstance(r, dict) and str(r.get("status") or "ok") == "ok"]
                        if ok_rows:
                            best = ok_rows[0]
                            recommended = str(best.get("strategy") or best.get("name") or "")
        except Exception:
            recommended = ""

        # runtime asset status (cheap: file existence checks)
        runtime_rep = build_runtime_asset_report(ctx)
        runtime_ok = bool(runtime_rep.get("ok"))
        missing_bins = list((runtime_rep.get("missing") or {}).get("binaries") or []) if isinstance(runtime_rep.get("missing"), dict) else []

        details = {
            "zapret": {
                "active_strategy": active_strategy,
                "running": running,
                "pid": pid_int,
                "pid_alive": pid_alive,
                "engine_mode": engine_mode,
            },
            "profile": {"active": "unknown"},
            "singbox": {
                "running": bool(sb.process_running),
                "pid": int(sb.pid or 0),
                "nodes": int(sb.nodes_count),
                "recommended_action": mask_secrets_text(sb.recommended_action),
            },
            "problem_domains": {"count": int(pd_count)},
            "latest_ranking": {"recommended": recommended},
            "runtime_assets": {"ok": runtime_ok, "missing_binaries": [str(x) for x in missing_bins]},
        }
        return success("Статус получен.", details=details)
    except Exception as e:
        return from_exception(e, "Не удалось получить статус.")


def set_engine_mode(ctx, mode: str) -> CommandResult:
    """Set runtime engine override mode for zapret start.

    mode: auto|winws|winws2
    """
    try:
        m = (mode or "").strip().lower()
        if m not in {"auto", "winws", "winws2"}:
            return failure("Неверный engine mode.", errors=[f"mode={mode!r}"])
        ctx.state.zapret.engine_mode = m
        try:
            from app.zapret_manager.core.state import save_state

            save_state(ctx.paths.state_file, ctx.state)
        except Exception:
            pass
        running = bool(getattr(getattr(ctx, "state", None), "zapret", None) and ctx.state.zapret.running)
        msg = f"Runtime engine mode: {m}."
        if running:
            msg += " Применится после перезапуска."
        return success(msg, details={"engine_mode": m, "running": running})
    except Exception as e:
        return from_exception(e, "Не удалось обновить engine mode.")


def apply_recommended_strategy(ctx, *, restart_if_running: bool = True) -> CommandResult:
    """Apply strategy recommended by the latest ranking json (if present)."""
    try:
        from app.zapret_manager.features.selection import find_strategy
        from app.zapret_manager.core.state import save_state

        p = (ctx.paths.data_dir / "telemetry" / "latest_strategy_ranking.json").resolve()
        if not p.exists():
            return failure("Рейтинг ещё не создан. Запустите 'Тест всех стратегий'.", errors=["latest_strategy_ranking.json missing"])

        import json

        obj = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        if not isinstance(obj, dict):
            return failure("Файл рейтинга повреждён.", errors=["ranking json is not a dict"])
        rows = obj.get("rows")
        if not isinstance(rows, list) or not rows:
            return failure("Рейтинг пуст.", errors=["rows empty"])

        ok_rows = [r for r in rows if isinstance(r, dict) and str(r.get("status") or "ok") == "ok"]
        best = ok_rows[0] if ok_rows else next((r for r in rows if isinstance(r, dict)), None)
        if not isinstance(best, dict):
            return failure("Не удалось выбрать стратегию из рейтинга.", errors=["no usable rows"])
        name = str(best.get("strategy") or best.get("name") or "").strip()
        if not name:
            return failure("Не удалось выбрать стратегию из рейтинга.", errors=["strategy name missing"])

        st = find_strategy(ctx, name, kind="base") or find_strategy(ctx, name)
        if not st:
            return failure("Рекомендованная стратегия не найдена локально.", errors=[f"strategy '{name}' not found"])

        ctx.state.zapret.base_strategy = st.name
        ctx.state.zapret.selected_strategy = st.name
        save_state(ctx.paths.state_file, ctx.state)

        if restart_if_running and bool(ctx.state.zapret.running):
            r = restart_current(ctx)
            if not r.ok:
                return failure(
                    "Стратегия выбрана, но перезапуск не удался.",
                    errors=r.errors,
                    warnings=r.warnings,
                    details={"strategy": st.name, "restart_current": r.to_dict()},
                )
            return success("Рекомендованная стратегия применена и перезапущена.", details={"strategy": st.name, "restart_current": r.to_dict()})

        return success("Рекомендованная стратегия применена.", details={"strategy": st.name, "restart_needed": bool(ctx.state.zapret.running)})
    except Exception as e:
        return from_exception(e, "Не удалось применить рекомендованную стратегию.")


def singbox_start_local_proxy(ctx) -> CommandResult:
    """Start sing-box local proxy without touching system proxy."""
    try:
        from app.zapret_manager.core.process_supervisor import ProcessSupervisor
        from app.zapret_manager.core.current_state import load_current_state
        from app.zapret_manager.core.singbox.binary import detect_singbox_binary
        from app.zapret_manager.core.singbox.process import SingBoxProcess

        cur_path = (ctx.paths.data_dir / "state" / "current.json").resolve()
        _ = load_current_state(cur_path)  # ensure file exists/shape
        sup = ProcessSupervisor(current_state_file=cur_path)
        bin = detect_singbox_binary(ctx.paths.root)
        if not bin:
            return failure("sing-box.exe не найден.", errors=["singbox binary missing"])
        proc = SingBoxProcess(
            supervisor=sup,
            bin_path=bin.path,
            config_path=(ctx.paths.data_dir / "singbox" / "generated_config.json").resolve(),
            log_file=(ctx.paths.logs_dir / "singbox.log").resolve(),
        )
        pid = proc.start()
        return success("sing-box запущен (local proxy).", details={"pid": int(pid or 0)})
    except Exception as e:
        return from_exception(e, "Не удалось запустить sing-box.")


def singbox_stop(ctx) -> CommandResult:
    try:
        from app.zapret_manager.core.process_supervisor import ProcessSupervisor
        from app.zapret_manager.core.current_state import load_current_state
        from app.zapret_manager.core.singbox.binary import detect_singbox_binary
        from app.zapret_manager.core.singbox.process import SingBoxProcess

        cur_path = (ctx.paths.data_dir / "state" / "current.json").resolve()
        cur = load_current_state(cur_path)
        pid = None
        if cur.processes.get("singbox"):
            pid = cur.processes["singbox"].pid
        sup = ProcessSupervisor(current_state_file=cur_path)
        bin = detect_singbox_binary(ctx.paths.root)
        if not bin:
            # clear state anyway
            sup.set_process("singbox", pid=None, running=False)
            return success("sing-box остановлен (state cleared).", details={"pid": int(pid or 0), "binary_missing": True})
        proc = SingBoxProcess(
            supervisor=sup,
            bin_path=bin.path,
            config_path=(ctx.paths.data_dir / "singbox" / "generated_config.json").resolve(),
            log_file=(ctx.paths.logs_dir / "singbox.log").resolve(),
        )
        proc.stop(pid)
        return success("sing-box остановлен.", details={"pid": int(pid or 0)})
    except Exception as e:
        return from_exception(e, "Не удалось остановить sing-box.")


def singbox_restart(ctx) -> CommandResult:
    try:
        st = singbox_stop(ctx)
        if not st.ok:
            return failure("Не удалось перезапустить sing-box: stop завершился с ошибкой.", errors=st.errors, warnings=st.warnings, details={"stop": st.to_dict()})
        started = singbox_start_local_proxy(ctx)
        if not started.ok:
            return failure("Не удалось перезапустить sing-box: start завершился с ошибкой.", errors=started.errors, warnings=st.warnings + started.warnings, details={"stop": st.to_dict(), "start": started.to_dict()})
        return success("sing-box перезапущен.", details={"stop": st.to_dict(), "start": started.to_dict()}, warnings=st.warnings + started.warnings)
    except Exception as e:
        return from_exception(e, "Не удалось перезапустить sing-box.")


def singbox_set_active_node(ctx, node_id: str, *, restart: bool = True) -> CommandResult:
    """Set active sing-box node id (masked in output)."""
    try:
        from app.zapret_manager.core.current_state import load_current_state, save_current_state
        from app.zapret_manager.core.singbox.nodes import load_nodes

        wanted = (node_id or "").strip()
        if not wanted:
            return failure("Пустой node_id.", errors=["node_id is empty"])

        nodes = load_nodes((ctx.paths.data_dir / "singbox" / "nodes.json").resolve())
        node = next((n for n in nodes if n.node_id == wanted), None)
        if not node:
            return failure("Нода не найдена.", errors=[f"node_id={wanted}"])

        cur_path = (ctx.paths.data_dir / "state" / "current.json").resolve()
        cur = load_current_state(cur_path)
        cur.active_singbox_node_id = wanted
        save_current_state(cur_path, cur)

        if restart:
            r = singbox_restart(ctx)
            if not r.ok:
                return failure(
                    "Нода выбрана, но перезапуск sing-box не удался.",
                    errors=r.errors,
                    warnings=r.warnings,
                    details={"active_node_id": wanted, "restart": r.to_dict()},
                )
            return success("Нода выбрана и sing-box перезапущен.", details={"active_node_id": wanted, "node": node.masked_summary(), "restart": r.to_dict()})

        return success("Нода выбрана.", details={"active_node_id": wanted, "node": node.masked_summary()})
    except Exception as e:
        return from_exception(e, "Не удалось выбрать ноду.")


def open_logs_dir(ctx) -> CommandResult:
    try:
        from app.zapret_manager.utils.platform import is_windows
        from subprocess import Popen

        p = ctx.paths.logs_dir.resolve()
        if is_windows():
            Popen(["explorer.exe", str(p)])  # noqa: S603,S607
            return success("Открыта папка логов.", details={"path": p})
        return failure("Открытие папки логов доступно только на Windows.", errors=["windows-only"], details={"path": p})
    except Exception as e:
        return from_exception(e, "Не удалось открыть папку логов.")


def generate_diagnostics_artifacts(ctx) -> CommandResult:
    try:
        from app.zapret_manager.features.diagnostics_artifacts import write_all_diagnostics_artifacts

        res = write_all_diagnostics_artifacts(ctx)
        created = [str(p) for p in (res.created or [])]
        warnings = list(res.errors or [])
        return success(
            "Диагностические артефакты сформированы.",
            details={"created_files": created},
            warnings=warnings,
        )
    except Exception as e:
        return from_exception(e, "Не удалось сформировать диагностические артефакты.")


def create_bug_report(ctx) -> CommandResult:
    """Create bug report zip with best-effort extras."""
    try:
        from app.zapret_manager.core.mask import mask_secrets_text
        from app.zapret_manager.core.report import generate_bug_report_zip
        from app.zapret_manager.features.diagnostics_artifacts import write_all_diagnostics_artifacts
        from app.zapret_manager.features.singbox_health import build_singbox_health_report, write_singbox_health_artifacts
        from app.zapret_manager.features.problem_domains import write_problem_domains_summary_artifacts

        warnings: list[str] = []
        extra: list[Path] = []

        # diagnostics artifacts
        try:
            ar = write_all_diagnostics_artifacts(ctx)
            extra.extend(ar.created)
            warnings.extend(ar.errors)
        except Exception as e:
            warnings.append(mask_secrets_text(f"diagnostics artifacts: {type(e).__name__}: {e}"))

        # sing-box health
        try:
            rep = build_singbox_health_report(data_dir=ctx.paths.data_dir, root_dir=ctx.paths.root)
            p_json, p_txt = write_singbox_health_artifacts(data_dir=ctx.paths.data_dir, report=rep)
            extra.extend([p_json, p_txt])
        except Exception as e:
            warnings.append(mask_secrets_text(f"singbox health: {type(e).__name__}: {e}"))

        # problem domains artifacts
        try:
            extra.extend(write_problem_domains_summary_artifacts(ctx))
        except Exception as e:
            warnings.append(mask_secrets_text(f"problem domains artifacts: {type(e).__name__}: {e}"))

        out = generate_bug_report_zip(
            out_dir=(ctx.paths.data_dir / "reports").resolve(),
            logs_dir=ctx.paths.logs_dir.resolve(),
            state_file=ctx.paths.state_file.resolve(),
            current_state_file=(ctx.paths.data_dir / "state" / "current.json").resolve(),
            config_file=ctx.paths.config_file.resolve(),
            extra_files=extra,
        )
        return success(
            "Bug report создан.",
            details={"zip_path": str(out), "extras": [str(p) for p in extra]},
            warnings=warnings,
        )
    except Exception as e:
        return from_exception(e, "Не удалось создать bug report.")


def singbox_health(ctx) -> CommandResult:
    try:
        from app.zapret_manager.features.singbox_health import build_singbox_health_report, format_singbox_health_text

        rep = build_singbox_health_report(data_dir=ctx.paths.data_dir, root_dir=ctx.paths.root)
        txt = format_singbox_health_text(rep)
        return success(
            "sing-box health сформирован.",
            details={
                "report": rep.to_json(),
                "text": txt,
                "recommended_action": rep.recommended_action,
            },
        )
    except Exception as e:
        return from_exception(e, "Не удалось получить sing-box health.")


def update_subscriptions(ctx) -> CommandResult:
    """Best-effort wrapper around sing-box subscriptions update.

    NOTE: Current implementation lives in UI-oriented module; we re-use lower-level
    functions directly here to avoid requiring interactive menu.
    """
    try:
        from app.zapret_manager.core.current_state import load_current_state, save_current_state
        from app.zapret_manager.core.singbox.subscriptions import (
            download_subscription_text,
            load_subscriptions,
            parse_subscription_payload_detailed,
            masked_subscription_label,
            merge_subscription_nodes,
            save_subscriptions,
        )
        from app.zapret_manager.core.singbox.nodes import load_nodes, save_nodes
        from app.zapret_manager.core.mask import mask_secrets_text

        subs_path = (ctx.paths.data_dir / "singbox" / "subscriptions.json").resolve()
        nodes_path = (ctx.paths.data_dir / "singbox" / "nodes.json").resolve()
        cur_path = (ctx.paths.data_dir / "state" / "current.json").resolve()

        subs = load_subscriptions(subs_path)
        if not subs:
            return failure("Нет подписок.", errors=["subscriptions.json пуст"], details={"imported": 0, "skipped": 0, "errors": 0})

        nodes = load_nodes(nodes_path)
        total_imported = 0
        total_skipped = 0
        total_errors = 0
        total_unsupported = 0
        updated = []

        cur = load_current_state(cur_path)
        auto_selected = False

        for s in subs:
            if not s.enabled:
                updated.append(s)
                continue
            try:
                txt = download_subscription_text(s.url)
                links, counters, last_err = parse_subscription_payload_detailed(txt)
                nodes, stats = merge_subscription_nodes(current_nodes=nodes, links=links)
                total_imported += int(stats.get("imported", 0) or 0)
                total_skipped += int(stats.get("skipped", 0) or 0)
                total_errors += int(stats.get("errors", 0) or 0)
                total_unsupported += int(counters.get("unsupported_lines", 0) or 0)
                if stats.get("imported", 0) == 0 and not links:
                    raise RuntimeError(last_err or "unsupported subscription payload")
                updated.append(
                    type(s)(
                        subscription_id=s.subscription_id,
                        name=s.name,
                        url=s.url,
                        enabled=s.enabled,
                        last_update_at="ok",
                        last_error="",
                        node_count=len(links),
                    )
                )
            except Exception as e:
                total_errors += 1
                updated.append(
                    type(s)(
                        subscription_id=s.subscription_id,
                        name=s.name,
                        url=s.url,
                        enabled=s.enabled,
                        last_update_at=s.last_update_at,
                        last_error=mask_secrets_text(str(e)),
                        node_count=s.node_count,
                    )
                )

        save_nodes(nodes_path, nodes)
        save_subscriptions(subs_path, updated)

        if total_imported > 0 and not (cur.active_singbox_node_id or "").strip() and nodes:
            cur.active_singbox_node_id = nodes[0].node_id
            save_current_state(cur_path, cur)
            auto_selected = True

        return success(
            "Подписки обновлены.",
            details={
                "imported": total_imported,
                "skipped": total_skipped,
                "errors": total_errors,
                "unsupported_lines": total_unsupported,
                "active_node_auto_selected": auto_selected,
                "subscriptions": [masked_subscription_label(s) for s in updated],
            },
        )
    except Exception as e:
        return from_exception(e, "Не удалось обновить подписки.")


def run_test_all(ctx, *, domain_set: str = "default", mode: str = "quick") -> CommandResult:
    try:
        from app.zapret_manager.features.test_sets import read_domain_set_file, DOMAIN_SETS, combine_domain_sets
        from app.zapret_manager.features.strategy_test import test_all_strategies_with_progress

        # resolve domains
        key = (domain_set or "default").strip().lower()
        if key == "all":
            domains = combine_domain_sets(ctx, [d.key for d in DOMAIN_SETS if d.key != "all"])
        else:
            ds = next((d for d in DOMAIN_SETS if d.key == key), None)
            if not ds:
                return failure("Неизвестный набор доменов.", errors=[f"domain_set={domain_set}"], details={"domain_set": domain_set})
            domains = read_domain_set_file(ds.file_path(ctx))

        if not [d for d in domains if d.strip()]:
            return failure("Набор доменов пуст.", errors=["domains list is empty"], details={"domain_set": key})

        summary, rows, ranking_json = test_all_strategies_with_progress(ctx, domains=domains, domain_set=key, mode=mode)
        recommended = ""
        if rows:
            best = next((r for r in rows if r.status == "ok" and (r.ok + r.fail) > 0), rows[0])
            recommended = best.strategy

        failed_domains = 0
        try:
            for r in summary.results:
                for c in r.checks:
                    if not c.ok:
                        failed_domains += 1
        except Exception:
            failed_domains = 0

        return success(
            "Тест всех стратегий завершён.",
            details={
                "ranking_path": str(ranking_json),
                "results_path": str(summary.results_file),
                "recommended_strategy": recommended,
                "total_strategies": len(summary.results),
                "failed_domains": failed_domains,
            },
        )
    except Exception as e:
        return from_exception(e, "Не удалось выполнить тест всех стратегий.")


def repair_runtime(ctx) -> CommandResult:
    try:
        from app.zapret_manager.features.runtime_assets import repair_runtime_assets
        from app.zapret_manager.features.diagnostics_artifacts import build_runtime_asset_report

        repair_runtime_assets(ctx)
        rep = build_runtime_asset_report(ctx)
        return success("Runtime восстановлен (best-effort).", details={"runtime_asset_report": rep})
    except Exception as e:
        return from_exception(e, "Не удалось восстановить runtime.")


def stop_all(ctx) -> CommandResult:
    """Best-effort stop of managed processes.

    Must not crash if nothing is running.
    """
    stopped: list[str] = []
    skipped: list[str] = []
    warnings: list[str] = []
    try:
        # zapret/winws
        try:
            from app.zapret_manager.features.zapret_runtime import stop_zapret

            stop_zapret(ctx)
            stopped.append("zapret")
        except Exception as e:
            warnings.append(f"zapret stop: {type(e).__name__}: {e}")
            skipped.append("zapret")

        # sing-box
        try:
            from app.zapret_manager.core.singbox.binary import detect_singbox_binary
            from app.zapret_manager.core.singbox.process import SingBoxProcess
            from app.zapret_manager.core.process_supervisor import ProcessSupervisor
            from app.zapret_manager.core.current_state import load_current_state
            from app.zapret_manager.core.mask import mask_secrets_text

            cur_path = (ctx.paths.data_dir / "state" / "current.json").resolve()
            cur = load_current_state(cur_path)
            pid = None
            if cur.processes.get("singbox"):
                pid = cur.processes["singbox"].pid
            bin = detect_singbox_binary(ctx.paths.root)
            sup = ProcessSupervisor(current_state_file=cur_path)
            if not bin:
                # Even if binary missing, clear state.
                sup.set_process("singbox", pid=None, running=False)
                skipped.append("singbox(binary missing)")
            else:
                proc = SingBoxProcess(
                    supervisor=sup,
                    bin_path=bin.path,
                    config_path=(ctx.paths.data_dir / "singbox" / "generated_config.json").resolve(),
                    log_file=(ctx.paths.logs_dir / "singbox.log").resolve(),
                )
                proc.stop(pid)
                stopped.append("singbox")
        except Exception as e:
            try:
                from app.zapret_manager.core.mask import mask_secrets_text

                warnings.append(mask_secrets_text(f"singbox stop: {type(e).__name__}: {e}"))
            except Exception:
                warnings.append(f"singbox stop: {type(e).__name__}: {e}")
            skipped.append("singbox")

        # TG proxy
        try:
            from app.zapret_manager.features.tg_proxy import stop_go, stop_rust

            stop_go(ctx)
            stop_rust(ctx)
            stopped.append("tg_proxy")
        except Exception as e:
            warnings.append(f"tg proxy stop: {type(e).__name__}: {e}")
            skipped.append("tg_proxy")

        return success("Остановка выполнена.", details={"stopped": stopped, "skipped": skipped}, warnings=warnings)
    except Exception as e:
        return from_exception(e, "Не удалось остановить процессы.")


def start_current_strategy(ctx) -> CommandResult:
    try:
        from app.zapret_manager.features.selection import find_strategy
        from app.zapret_manager.features.zapret_runtime import start_zapret_interactive

        zap = getattr(getattr(ctx, "state", None), "zapret", None)
        name = str(getattr(zap, "selected_strategy", "") or getattr(zap, "base_strategy", "") or "").strip() if zap else ""
        if not name:
            return failure("Не выбрана активная стратегия.", errors=["selected_strategy/base_strategy is empty"])
        st = find_strategy(ctx, name, kind="base") or find_strategy(ctx, name)
        if not st:
            return failure("Активная стратегия не найдена.", errors=[f"strategy '{name}' not found"], details={"strategy": name})
        start_zapret_interactive(ctx, st)
        return success("Стратегия запущена.", details={"strategy": name})
    except Exception as e:
        return from_exception(e, "Не удалось запустить стратегию.")


def restart_current(ctx) -> CommandResult:
    try:
        st = stop_all(ctx)
        if not st.ok:
            return failure(
                "Не удалось перезапустить: stop_all завершился с ошибкой.",
                errors=st.errors,
                warnings=st.warnings,
                details={"stop_all": st.to_dict()},
            )
        started = start_current_strategy(ctx)
        if not started.ok:
            return failure(
                "Не удалось перезапустить: не удалось запустить активную стратегию.",
                errors=started.errors,
                warnings=st.warnings + started.warnings,
                details={"stop_all": st.to_dict(), "start_current_strategy": started.to_dict()},
            )
        return success(
            "Перезапуск выполнен.",
            details={"stop_all": st.to_dict(), "start_current_strategy": started.to_dict()},
            warnings=st.warnings + started.warnings,
        )
    except Exception as e:
        return from_exception(e, "Не удалось перезапустить.")
