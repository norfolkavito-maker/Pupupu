from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import requests

from zapret_manager.core.app_context import AppContext
from zapret_manager.features.selection import find_strategy
from zapret_manager.features.zapret_runtime import start_zapret_interactive, stop_zapret
from zapret_manager.strategies.model import Strategy
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


def test_strategy(
    ctx: AppContext, strategy: Strategy, domains: list[str], *, settle_s: float = 1.5
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


def write_results(ctx: AppContext, results: list[TestResult], file_name: str) -> Path:
    out = ctx.paths.results_dir / file_name
    lines = [f"# {now_utc_iso()}"]
    for r in sorted(results, key=lambda x: x.ok, reverse=True):
        lines.append(f"{r.strategy} -> {r.ok}/{r.total}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out

