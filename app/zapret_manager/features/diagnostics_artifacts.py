from __future__ import annotations

"""Diagnostics summary artifacts.

Goal: create small best-effort text/JSON artifacts that can be included into:
- bug report zip
- future GUI / tray
- support/debug menu

Constraints:
- must not crash if files/directories are missing;
- must not perform network-heavy operations;
- outputs are later masked by bug report generator, but we still avoid writing raw secrets.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.mask import mask_secrets_text
from app.zapret_manager.utils.jsonx import atomic_write_json


log = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def diagnostics_dir(ctx: AppContext) -> Path:
    out_dir = (ctx.paths.data_dir / "diagnostics").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _read_json(p: Path) -> Any:
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _write_text(p: Path, text: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    # defensive: avoid writing raw secrets (still masked again in bug report)
    p.write_text(mask_secrets_text(text), encoding="utf-8")
    return p


# ----------------------- latest_strategy_ranking -----------------------


def build_latest_strategy_ranking_text(*, ranking_json: dict[str, Any] | None) -> str:
    if not ranking_json:
        return "Рейтинг стратегий ещё не создан. Запустите Тест всех стратегий.\n"

    domain_set = str(ranking_json.get("domain_set") or "")
    mode = str(ranking_json.get("mode") or "")
    created_at = str(ranking_json.get("created_at") or ranking_json.get("ts") or "")
    recommended = str(ranking_json.get("recommended") or "")
    rows = ranking_json.get("rows")
    if not isinstance(rows, list):
        rows = []

    invalid = [r for r in rows if isinstance(r, dict) and str(r.get("status") or "") != "ok"]
    ok_rows = [r for r in rows if isinstance(r, dict) and str(r.get("status") or "ok") == "ok"]

    lines: list[str] = []
    lines.append("Рейтинг стратегий (latest_strategy_ranking)")
    lines.append("=")
    lines.append(f"created_at: {created_at or '-'}")
    lines.append(f"domain_set: {domain_set or '-'}")
    lines.append(f"mode: {mode or '-'}")
    lines.append(f"total strategies: {len(rows)}")
    lines.append(f"invalid/crashed: {len(invalid)}")
    lines.append("")
    lines.append(f"Рекомендовано: {recommended or '-'}")
    lines.append("")

    def _row_line(idx: int, r: dict[str, Any]) -> str:
        name = str(r.get("strategy") or r.get("name") or "-")
        ok = r.get("ok")
        fail = r.get("fail")
        avg_ms = r.get("avg_ms")
        score = r.get("score")
        missing_assets = r.get("missing_assets")
        miss = "-" if not missing_assets else str(missing_assets)
        return f"{idx:02d}. {name} | ok={ok} fail={fail} avg_ms={avg_ms} score={score} missing_assets={miss}"

    lines.append("TOP-5:")
    for i, r in enumerate(ok_rows[:5], start=1):
        lines.append(_row_line(i, r))
    if not ok_rows:
        lines.append("(нет валидных результатов)")
    lines.append("")

    if invalid:
        lines.append("INVALID/CRASHED (первые 10):")
        for r in invalid[:10]:
            name = str(r.get("strategy") or r.get("name") or "-")
            err = str(r.get("error") or "")
            lines.append(f"- {name}: {err}".rstrip())
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def write_latest_strategy_ranking_artifact(ctx: AppContext) -> Path:
    src = (ctx.paths.data_dir / "telemetry" / "latest_strategy_ranking.json").resolve()
    data = _read_json(src) if src.exists() else None
    txt = build_latest_strategy_ranking_text(ranking_json=data if isinstance(data, dict) else None)
    out = diagnostics_dir(ctx) / "latest_strategy_ranking.txt"
    return _write_text(out, txt)


# ----------------------- runtime assets report -----------------------


_EXPECTED_FAKE = [
    "quic_initial_www_google_com.bin",
    "tls_clienthello_max_ru.bin",
    "tls_clienthello_www_google_com.bin",
    "tls_clienthello_vk_com.bin",
    "tls_clienthello_gosuslugi_ru.bin",
    "4pda.bin",
    "t2.bin",
    "stun.bin",
]


def _safe_exists(p: Path) -> bool:
    try:
        return p.exists()
    except Exception:
        return False


def build_runtime_asset_report(ctx: AppContext) -> dict[str, Any]:
    from app.zapret_manager.features.zapret_runtime import zapret_root

    rep: dict[str, Any] = {
        "schema_version": 1,
        "created_at": _utc_now_iso(),
        "runtime_dir": str(ctx.paths.runtime_dir.resolve()),
        "ok": True,
        "checks": {},
        "missing": {"fake": [], "lists": [], "binaries": [], "other": []},
        "suggested_actions": [],
    }

    runtime_dir = ctx.paths.runtime_dir.resolve()
    zapret_dir = zapret_root(ctx)

    rep["checks"]["runtime_dir"] = {"path": str(runtime_dir), "exists": _safe_exists(runtime_dir)}
    rep["checks"]["zapret_root"] = {"path": str(zapret_dir), "exists": _safe_exists(zapret_dir)}

    # binaries
    winws = (zapret_dir / "winws.exe").resolve()
    winws2 = (zapret_dir / "winws2.exe").resolve()
    wd_dll = (zapret_dir / "WinDivert.dll").resolve()
    wd_sys = (zapret_dir / "WinDivert64.sys").resolve()
    for key, p in [
        ("winws.exe", winws),
        ("winws2.exe", winws2),
        ("WinDivert.dll", wd_dll),
        ("WinDivert64.sys", wd_sys),
    ]:
        ok = _safe_exists(p)
        rep["checks"][key] = {"path": str(p), "exists": ok}
        if not ok:
            rep["missing"]["binaries"].append(str(p))

    fake_dir = (zapret_dir / "files" / "fake").resolve()
    rep["checks"]["fake_dir"] = {"path": str(fake_dir), "exists": _safe_exists(fake_dir)}

    for name in _EXPECTED_FAKE:
        p = (fake_dir / name).resolve()
        ok = _safe_exists(p)
        rep["checks"][f"fake/{name}"] = {"path": str(p), "exists": ok}
        if not ok:
            rep["missing"]["fake"].append(name)

    lists_dir = ctx.paths.lists_dir.resolve()
    rep["checks"]["lists_dir"] = {"path": str(lists_dir), "exists": _safe_exists(lists_dir)}
    # minimal known lists
    for name in ["google.txt", "exclude.txt", "rkn.txt", "list-general.txt", "general.txt"]:
        p = (lists_dir / name).resolve()
        ok = _safe_exists(p)
        rep["checks"][f"lists/{name}"] = {"path": str(p), "exists": ok}
        if not ok:
            rep["missing"]["lists"].append(name)

    # requested engine (best-effort; doesn't crash if state fields are absent)
    requested_engine = "auto"
    try:
        zap = getattr(getattr(ctx, "state", None), "zapret", None)
        base = getattr(zap, "base_strategy", "") if zap else ""
        selected = getattr(zap, "selected_strategy", "") if zap else ""
        # prefer the selected strategy if present
        st_name = (selected or base or "").strip()
        if st_name:
            try:
                from app.zapret_manager.features.selection import find_strategy

                st = find_strategy(ctx, st_name)
                if st and (st.engine or "").strip().lower() == "winws2":
                    requested_engine = "winws2"
            except Exception:
                pass
    except Exception:
        pass
    rep["requested_engine"] = requested_engine

    # suggested actions (simple heuristic)
    if rep["missing"]["fake"] or rep["missing"]["lists"]:
        rep["suggested_actions"].append("Repair runtime assets")
    if rep["missing"]["binaries"]:
        rep["suggested_actions"].append("Reinstall runtime")
    # If current/selected strategy explicitly requires winws2, missing winws2 is actionable.
    if requested_engine == "winws2" and not _safe_exists(winws2):
        rep["suggested_actions"].append(
            "Runtime неполный: отсутствует winws2.exe. Выполните Repair runtime assets или переустановите runtime."
        )

    rep["ok"] = not (rep["missing"]["fake"] or rep["missing"]["lists"] or rep["missing"]["binaries"])
    return rep


def runtime_asset_report_text(rep: dict[str, Any]) -> str:
    ok = bool(rep.get("ok"))
    lines: list[str] = []
    lines.append("Runtime asset report")
    lines.append("=")
    lines.append(f"created_at: {rep.get('created_at')}")
    lines.append(f"runtime_dir: {rep.get('runtime_dir')}")
    lines.append(f"status: {'OK' if ok else 'MISSING/BROKEN'}")
    lines.append("")

    missing = rep.get("missing") if isinstance(rep.get("missing"), dict) else {}
    fake = missing.get("fake") if isinstance(missing, dict) else []
    lists = missing.get("lists") if isinstance(missing, dict) else []
    bins = missing.get("binaries") if isinstance(missing, dict) else []

    if bins:
        lines.append("Missing runtime binaries:")
        for p in bins:
            lines.append(f"- {p}")
        lines.append("")

    req = str(rep.get("requested_engine") or "")
    if req:
        lines.append(f"requested_engine: {req}")
        lines.append("")
    if lists:
        lines.append("Missing lists:")
        for n in lists:
            lines.append(f"- {n}")
        lines.append("")
    if fake:
        lines.append("Missing fake files:")
        for n in fake:
            lines.append(f"- {n}")
        lines.append("")

    actions = rep.get("suggested_actions")
    if isinstance(actions, list) and actions:
        lines.append("Suggested action:")
        for a in actions:
            lines.append(f"- {a}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def write_runtime_asset_reports(ctx: AppContext) -> tuple[Path, Path]:
    rep = build_runtime_asset_report(ctx)
    out_dir = diagnostics_dir(ctx)
    p_json = (out_dir / "runtime_asset_report.json").resolve()
    atomic_write_json(p_json, rep)
    p_txt = (out_dir / "runtime_asset_report.txt").resolve()
    _write_text(p_txt, runtime_asset_report_text(rep))
    return p_json, p_txt


# ----------------------- flowseal assets report -----------------------


def build_flowseal_asset_report(ctx: AppContext) -> dict[str, Any]:
    flowseal_root = (ctx.paths.upstreams_dir / "flowseal").resolve()
    rep: dict[str, Any] = {
        "schema_version": 1,
        "created_at": _utc_now_iso(),
        "flowseal_root": str(flowseal_root),
        "ok": True,
        "checks": {},
        "missing": {"dirs": [], "files": []},
        "suggested_actions": [],
        "strategy_counts": {},
    }

    rep["checks"]["flowseal_root"] = {"path": str(flowseal_root), "exists": _safe_exists(flowseal_root)}
    bin_dir = (flowseal_root / "bin").resolve()
    lists_dir = (flowseal_root / "lists").resolve()
    rep["checks"]["bin_dir"] = {"path": str(bin_dir), "exists": _safe_exists(bin_dir)}
    rep["checks"]["lists_dir"] = {"path": str(lists_dir), "exists": _safe_exists(lists_dir)}
    if not _safe_exists(flowseal_root):
        rep["missing"]["dirs"].append(str(flowseal_root))
    if not _safe_exists(bin_dir):
        rep["missing"]["dirs"].append(str(bin_dir))
    if not _safe_exists(lists_dir):
        rep["missing"]["dirs"].append(str(lists_dir))

    # Common Flowseal lists
    for name in ["list-general.txt", "general.txt"]:
        p = (lists_dir / name).resolve()
        ok = _safe_exists(p)
        rep["checks"][f"lists/{name}"] = {"path": str(p), "exists": ok}
        if not ok:
            rep["missing"]["files"].append(name)

    # Known fake files are checked in runtime report (canonical place). Here only basic checks.
    # Strategy counts (best-effort)
    try:
        from app.zapret_manager.strategies.store import list_strategies

        generated = ctx.paths.strategies_generated_dir.resolve()
        bases = list_strategies(generated, kind="base")
        flowseal_bases = [b for b in bases if (b.upstream or "").lower() == "flowseal"]
        rep["strategy_counts"]["generated_base_total"] = len(bases)
        rep["strategy_counts"]["generated_flowseal_base"] = len(flowseal_bases)
    except Exception:
        pass

    if rep["missing"]["dirs"] or rep["missing"]["files"]:
        rep["suggested_actions"].append("Sync Flowseal")
        rep["suggested_actions"].append("Repair runtime assets")
    rep["ok"] = not (rep["missing"]["dirs"] or rep["missing"]["files"])
    return rep


def flowseal_asset_report_text(rep: dict[str, Any]) -> str:
    ok = bool(rep.get("ok"))
    lines: list[str] = []
    lines.append("Flowseal asset report")
    lines.append("=")
    lines.append(f"created_at: {rep.get('created_at')}")
    lines.append(f"flowseal_root: {rep.get('flowseal_root')}")
    lines.append(f"status: {'OK' if ok else 'MISSING/BROKEN'}")
    lines.append("")

    missing = rep.get("missing") if isinstance(rep.get("missing"), dict) else {}
    dirs = missing.get("dirs") if isinstance(missing, dict) else []
    files = missing.get("files") if isinstance(missing, dict) else []
    if dirs:
        lines.append("Missing dirs:")
        for d in dirs:
            lines.append(f"- {d}")
        lines.append("")
    if files:
        lines.append("Missing files:")
        for f in files:
            lines.append(f"- {f}")
        lines.append("")

    sc = rep.get("strategy_counts")
    if isinstance(sc, dict) and sc:
        lines.append("Strategy counts:")
        for k, v in sc.items():
            lines.append(f"- {k}: {v}")
        lines.append("")

    actions = rep.get("suggested_actions")
    if isinstance(actions, list) and actions:
        lines.append("Suggested action:")
        for a in actions:
            lines.append(f"- {a}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def write_flowseal_asset_reports(ctx: AppContext) -> tuple[Path, Path]:
    rep = build_flowseal_asset_report(ctx)
    out_dir = diagnostics_dir(ctx)
    p_json = (out_dir / "flowseal_asset_report.json").resolve()
    atomic_write_json(p_json, rep)
    p_txt = (out_dir / "flowseal_asset_report.txt").resolve()
    _write_text(p_txt, flowseal_asset_report_text(rep))
    return p_json, p_txt


# ----------------------- public orchestration -----------------------


@dataclass(frozen=True)
class ArtifactsResult:
    created: list[Path]
    errors: list[str]


def write_all_diagnostics_artifacts(ctx: AppContext) -> ArtifactsResult:
    created: list[Path] = []
    errors: list[str] = []

    def _try(fn, label: str):
        try:
            res = fn()
            if isinstance(res, (list, tuple)):
                for p in res:
                    if isinstance(p, Path):
                        created.append(p)
            elif isinstance(res, Path):
                created.append(res)
        except Exception as e:
            log.warning("diagnostics artifacts: %s failed: %s", label, e)
            errors.append(f"{label}: {type(e).__name__}: {e}")

    _try(lambda: [write_latest_strategy_ranking_artifact(ctx)], "latest_strategy_ranking")
    _try(lambda: list(write_runtime_asset_reports(ctx)), "runtime_asset_report")
    _try(lambda: list(write_flowseal_asset_reports(ctx)), "flowseal_asset_report")

    # Dedup preserve order
    uniq: list[Path] = []
    seen: set[str] = set()
    for p in created:
        key = str(p.resolve())
        if key in seen:
            continue
        seen.add(key)
        uniq.append(p)

    return ArtifactsResult(created=uniq, errors=errors)
