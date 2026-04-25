from __future__ import annotations

import logging
import shutil
import tempfile
from dataclasses import dataclass
from typing import Iterable
from pathlib import Path

import requests

from zapret_manager.core.app_context import AppContext
from zapret_manager.features.selection import find_strategy
from zapret_manager.features.upstreams import (
    sync_flowseal,
    sync_stressozz_strategies,
    sync_zapret_runtime,
)
from zapret_manager.features.zapret_runtime import start_zapret_interactive, stop_zapret
from zapret_manager.strategies.model import Strategy
from zapret_manager.strategies.store import list_strategies, save_strategy
from zapret_manager.utils.timex import now_utc_iso


log = logging.getLogger(__name__)


DEFAULT_TEST_DOMAINS = [
    # Best-effort "youtube/googlevideo" probes (из Zapret-Manager.sh).
    "rr1---sn-gvnuxaxjvh-jx3z.googlevideo.com",
    "rr1---sn-gvnuxaxjvh-jx3l.googlevideo.com",
    "rr1---sn-gvnuxaxjvh-jx3s.googlevideo.com",
]


@dataclass(frozen=True)
class TestResult:
    strategy: str
    ok: int
    total: int


@dataclass(frozen=True)
class TestSessionSummary:
    results: list[TestResult]
    pinned: list[Path]
    results_file: Path


def check_domains(domains: list[str], *, timeout_s: float = 3.0) -> tuple[int, int]:
    ok = 0
    total = 0
    for d in domains:
        d = d.strip()
        if not d:
            continue
        total += 1
        url = d if d.startswith("http://") or d.startswith("https://") else f"https://{d}"
        try:
            r = requests.get(url, timeout=timeout_s)
            if 200 <= r.status_code < 500:
                ok += 1
        except Exception:
            pass
    return ok, total


def control_test(domains: list[str], *, parallel: int | None = None) -> TestResult:
    """Legacy helper used by UI: baseline check without any strategy running."""
    ok, total = check_domains(domains)
    return TestResult(strategy="control", ok=ok, total=total)


def _runtime_ready(ctx: AppContext) -> bool:
    """Best-effort check that runtime is installed and winws.exe is discoverable."""
    try:
        from zapret_manager.features.zapret_runtime import detect_runtime_files

        detect_runtime_files(ctx)
        return bool(ctx.state.runtime.installed and ctx.state.runtime.winws_path)
    except Exception:
        return False


def _ensure_runtime(ctx: AppContext) -> None:
    if _runtime_ready(ctx):
        return
    log.info("runtime missing for tests -> syncing zapret runtime")
    sync_zapret_runtime(ctx)
    from zapret_manager.features.zapret_runtime import detect_runtime_files

    detect_runtime_files(ctx)
    if not _runtime_ready(ctx):
        raise RuntimeError("Runtime is still missing after sync. Check sources.yaml/runtime layout.")


def _ensure_pack_strategies(ctx: AppContext, *, need_flowseal: bool, need_stressozz: bool) -> None:
    """Sync optional packs if strategies are missing."""
    if need_flowseal:
        log.info("flowseal strategies missing -> syncing Flowseal")
        sync_flowseal(ctx, generated_dir=_tmp_pack_dir(ctx, "flowseal"))
    if need_stressozz:
        log.info("stressozz strategies missing -> syncing StressOzz")
        sync_stressozz_strategies(ctx, generated_dir=_tmp_pack_dir(ctx, "stressozz"))


def _tmp_pack_dir(ctx: AppContext, pack: str) -> Path:
    d = ctx.paths.strategies_generated_dir / "_tmp" / "packs" / pack
    d.mkdir(parents=True, exist_ok=True)
    return d


def _tmp_dir(ctx: AppContext, name: str) -> Path:
    d = ctx.paths.strategies_generated_dir / "_tmp" / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def _list_tmp_strategies(ctx: AppContext, tmp_dir: Path, *, kind: str | None = None) -> list[Strategy]:
    # by construction temp dir stores json/yaml strategies
    return list_strategies(tmp_dir, kind=kind)


def _pin_top_results(ctx: AppContext, results: list[TestResult], tmp_dir: Path, *, top_n: int = 5) -> list[Path]:
    """Pin top strategies into custom dir (user won't lose them on updates)."""
    if top_n == 5:
        best = _select_top5_wide(results)
    else:
        ranked = sorted(results, key=lambda r: (r.ok, r.total, r.strategy), reverse=True)
        best = [r for r in ranked if r.total > 0][:top_n]

    pinned: list[Path] = []
    for r in best:
        st = find_strategy(ctx, r.strategy) or next(
            (s for s in _list_tmp_strategies(ctx, tmp_dir) if s.name == r.strategy), None
        )
        if not st:
            continue
        # save as JSON into custom
        p = save_strategy(ctx.paths.strategies_custom_dir, st)
        pinned.append(p)
    return pinned


def _cleanup_tmp(tmp_dir: Path) -> None:
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_strategy(
    ctx: AppContext,
    strategy: Strategy,
    domains: list[str],
    *,
    settle_s: float = 1.5,
    parallel: int | None = None,
) -> TestResult:
    import time

    was_running = ctx.state.zapret.running
    prev_base = ctx.state.zapret.base_strategy
    prev_selected = ctx.state.zapret.selected_strategy
    prev_youtube = ctx.state.zapret.youtube_layer
    prev_discord = ctx.state.zapret.discord_layer
    try:
        stop_zapret(ctx)
        start_zapret_interactive(ctx, strategy)
        time.sleep(settle_s)
        ok, total = check_domains(domains)
        return TestResult(strategy=strategy.name, ok=ok, total=total)
    finally:
        stop_zapret(ctx)
        ctx.state.zapret.base_strategy = prev_base
        ctx.state.zapret.selected_strategy = prev_selected
        ctx.state.zapret.youtube_layer = prev_youtube
        ctx.state.zapret.discord_layer = prev_discord
        if was_running and prev_selected:
            prev_strategy = find_strategy(ctx, prev_selected, kind="base") or find_strategy(ctx, prev_selected)
            if prev_strategy:
                youtube = find_strategy(ctx, prev_youtube, kind="youtube") if prev_youtube else None
                discord = find_strategy(ctx, prev_discord, kind="discord") if prev_discord else None
                try:
                    start_zapret_interactive(ctx, prev_strategy, youtube=youtube, discord=discord)
                except Exception:
                    log.exception("failed to restore previous zapret state after strategy test")


def _select_candidates(ctx: AppContext, group: str) -> list[Strategy]:
    from zapret_manager.features.selection import list_bases, list_layers

    # include temp pack dirs in selection (if they exist)
    tmp_flowseal = ctx.paths.strategies_generated_dir / "_tmp" / "packs" / "flowseal"
    tmp_stressozz = ctx.paths.strategies_generated_dir / "_tmp" / "packs" / "stressozz"
    tmp_bases = list_strategies(tmp_flowseal, kind="base") + list_strategies(tmp_stressozz, kind="base")
    tmp_yv = list_strategies(tmp_flowseal, kind="youtube") + list_strategies(tmp_stressozz, kind="youtube")
    tmp_dv = list_strategies(tmp_flowseal, kind="discord") + list_strategies(tmp_stressozz, kind="discord")

    if group == "v":
        bases = list_bases(ctx)
        out = [b for b in bases if b.name.lower().startswith("v") and b.name[1:].isdigit()]
        # also include temp stressozz v-strategies (same naming)
        for st in tmp_bases:
            if st.name.lower().startswith("v") and st.name[1:].isdigit():
                out.append(st)
        # de-dup by name
        seen: set[str] = set()
        uniq: list[Strategy] = []
        for st in out:
            if st.name in seen:
                continue
            seen.add(st.name)
            uniq.append(st)
        return uniq
    if group == "flowseal":
        out = [b for b in list_bases(ctx) if (b.upstream or "").lower() == "flowseal"]
        out.extend([b for b in tmp_bases if (b.upstream or "").lower() == "flowseal"])
        return out
    if group == "all":
        # v + flowseal bases
        out: list[Strategy] = []
        seen: set[str] = set()
        for st in _select_candidates(ctx, "v") + _select_candidates(ctx, "flowseal"):
            if st.name in seen:
                continue
            seen.add(st.name)
            out.append(st)
        return out
    if group == "youtube":
        out = [s for s in list_layers(ctx, "youtube") if s.name.lower().startswith("yv")]
        out.extend([s for s in tmp_yv if s.name.lower().startswith("yv")])
        # de-dup
        seen: set[str] = set()
        uniq: list[Strategy] = []
        for st in out:
            if st.name in seen:
                continue
            seen.add(st.name)
            uniq.append(st)
        return uniq
    if group == "discord":
        out = [s for s in list_layers(ctx, "discord") if s.name.lower().startswith("dv")]
        out.extend([s for s in tmp_dv if s.name.lower().startswith("dv")])
        # de-dup
        seen: set[str] = set()
        uniq: list[Strategy] = []
        for st in out:
            if st.name in seen:
                continue
            seen.add(st.name)
            uniq.append(st)
        return uniq
    raise ValueError(f"Unknown candidates group: {group}")


def _select_top5_wide(results: list[TestResult]) -> list[TestResult]:
    """Select up to 5 results with preference for high coverage.

    Heuristic:
    - sort by ok desc, then total desc
    - take top 5
    """
    ranked = sorted(results, key=lambda r: (r.ok, r.total, r.strategy), reverse=True)
    return [r for r in ranked if r.total > 0][:5]


def test_session(
    ctx: AppContext,
    *,
    group: str | None = None,
    candidates: list[Strategy] | None = None,
    domains: list[str],
    out_name: str,
    settle_s: float = 1.5,
    top_n: int = 5,
    ensure_runtime: bool = True,
    ensure_flowseal: bool = False,
    ensure_stressozz: bool = False,
) -> TestSessionSummary:
    """Runs a test session.

    - Can auto-sync runtime/packs.
    - Can work with a temporary pool of strategies.
    - Pins top-N to custom strategies.
    """
    if ensure_runtime:
        _ensure_runtime(ctx)
    _ensure_pack_strategies(ctx, need_flowseal=ensure_flowseal, need_stressozz=ensure_stressozz)

    if candidates is None:
        if not group:
            raise ValueError("either candidates or group must be provided")
        candidates = _select_candidates(ctx, group)

    if not candidates:
        raise RuntimeError("No strategies found for test session (after ensure).")

    # Build a temp pool from current builtin/generated/custom after sync.
    tmp_name = f"session_{now_utc_iso().replace(':','-').replace('T','_')}_{next(tempfile._get_candidate_names())}"
    tmp_dir = _tmp_dir(ctx, tmp_name)
    try:
        # copy candidates by name only to keep session stable
        # If a candidate is from builtin/generated/custom, we store it into tmp.
        for st in candidates:
            save_strategy(tmp_dir, st)

        session_strategies = _list_tmp_strategies(ctx, tmp_dir)
        if not session_strategies:
            raise RuntimeError("No strategies to test.")

        results: list[TestResult] = []
        for st in session_strategies:
            log.info("testing strategy %s", st.name)
            results.append(test_strategy(ctx, st, domains, settle_s=settle_s))

        results_file = write_results(ctx, results, out_name)
        pinned = _pin_top_results(ctx, results, tmp_dir, top_n=top_n)
        return TestSessionSummary(results=results, pinned=pinned, results_file=results_file)
    finally:
        _cleanup_tmp(tmp_dir)
        # cleanup temp packs as well
        if ensure_flowseal:
            _cleanup_tmp(_tmp_pack_dir(ctx, "flowseal"))
        if ensure_stressozz:
            _cleanup_tmp(_tmp_pack_dir(ctx, "stressozz"))


def write_results(ctx: AppContext, results: list[TestResult], file_name: str) -> Path:
    out = ctx.paths.results_dir / file_name
    lines = [f"# {now_utc_iso()}"]
    for r in sorted(results, key=lambda x: x.ok, reverse=True):
        lines.append(f"{r.strategy} -> {r.ok}/{r.total}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out

