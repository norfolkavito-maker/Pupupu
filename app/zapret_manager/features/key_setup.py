from __future__ import annotations

import logging
from copy import deepcopy

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.state import save_state
from app.zapret_manager.features.hosts import HostsManager
from app.zapret_manager.features.lists import update_exclude
from app.zapret_manager.features.selection import find_strategy
from app.zapret_manager.features.upstreams import sync_flowseal, sync_stressozz_strategies
from app.zapret_manager.features.strategy_test import control_test, test_session
from app.zapret_manager.features.test_sets import combine_domain_sets
from app.zapret_manager.features.test_urls import prepare_urls
from app.zapret_manager.features.zapret_runtime import require_runtime_ok, start_zapret_interactive, stop_zapret
from app.zapret_manager.utils.console import C, ask, safe_print
from app.zapret_manager.features.hosts import load_blocks_from_file, set_block_enabled


log = logging.getLogger(__name__)


def key_setup(ctx: AppContext) -> list[str]:
    """
    StressOzz-like "под ключ":
    sync strategies -> v7 -> hosts all -> 50-stun4all -> Gv1 -> start.
    """
    lines: list[str] = []
    state_backup = deepcopy(ctx.state)
    hosts_backup = HostsManager(ctx).backup()
    try:
        require_runtime_ok(ctx)
        stop_zapret(ctx)

        sync_flowseal(ctx)
        sync_stressozz_strategies(ctx)
        lines.append("strategies: synced")

        update_exclude(ctx)
        lines.append("exclude: updated")

        base = find_strategy(ctx, "v7", kind="base")
        if not base:
            raise RuntimeError("Не найдена стратегия v7. Сначала sync StressOzz.")

        ctx.state.zapret.base_strategy = base.name
        ctx.state.zapret.selected_strategy = base.name
        ctx.state.zapret.youtube_layer = ""
        ctx.state.zapret.discord_layer = ""
        ctx.state.zapret.discord_script = "50-stun4all"
        ctx.state.zapret.games_profile = "Gv1"
        ctx.state.zapret.rkn_enabled = False
        ctx.state.zapret.wssize_enabled = False
        save_state(ctx.paths.state_file, ctx.state)
        lines.append("state: v7 + 50-stun4all + Gv1")

        blocks_file = (ctx.paths.data_dir / "hosts" / "blocks.json").resolve()
        for b in load_blocks_from_file(blocks_file):
            set_block_enabled(b.key, True)
        lines.append("hosts: all enabled")

        warnings = start_zapret_interactive(ctx, base)
        lines.append("zapret: started")
        lines.extend([f"warn: {w}" for w in warnings])
        return lines
    except Exception:
        ctx.state = state_backup
        save_state(ctx.paths.state_file, ctx.state)
        if hosts_backup:
            HostsManager(ctx).restore(hosts_backup)
        raise


def key_setup_full_check(ctx: AppContext) -> list[str]:
    """Interactive wizard:

    1) baseline (control) test without zapret
    2) select services (youtube/discord/instagram/games)
    3) run candidate strategy session on selected domain set
    4) print top-3 and offer to apply best

    NOTE: This is best-effort and should not modify user setup unless confirmed.
    """

    state_backup = deepcopy(ctx.state)
    hosts_backup = HostsManager(ctx).backup()
    lines: list[str] = []
    try:
        require_runtime_ok(ctx)
        stop_zapret(ctx)

        sync_flowseal(ctx)
        sync_stressozz_strategies(ctx)
        update_exclude(ctx)
        lines.append("strategies: synced")
        lines.append("exclude: updated")

        # Step A: baseline control test
        safe_print(f"\n{C.MAGENTA}Под ключ (full-check): контрольная проверка без zapret{C.RESET}\n")
        base_domains = combine_domain_sets(ctx, ["default", "youtube", "cdn", "amazon", "discord", "instagram", "games"])
        domains = [u.url for u in prepare_urls(base_urls=base_domains, include_default=True, include_suite=True)]
        # control_test signature: control_test(ctx, domains, ...)
        r0 = control_test(ctx, domains, parallel=8)
        safe_print(f"{C.YELLOW}Baseline:{C.RESET} {r0.summary_text()}\n")
        lines.append(f"baseline: {r0.summary_text()}")

        # Step B: choose services
        services = {
            "youtube": True,
            "discord": True,
            "instagram": False,
            "games": False,
        }

        while True:
            safe_print(f"{C.MAGENTA}Выбор сервисов (toggle 1-4, Enter=далее){C.RESET}")
            safe_print(f"1) YouTube      : {'ON' if services['youtube'] else 'OFF'}")
            safe_print(f"2) Discord      : {'ON' if services['discord'] else 'OFF'}")
            safe_print(f"3) Instagram    : {'ON' if services['instagram'] else 'OFF'}")
            safe_print(f"4) Games        : {'ON' if services['games'] else 'OFF'}")
            c = ask("Выбор: ").strip()
            if not c:
                break
            if c == "1":
                services["youtube"] = not services["youtube"]
            elif c == "2":
                services["discord"] = not services["discord"]
            elif c == "3":
                services["instagram"] = not services["instagram"]
            elif c == "4":
                services["games"] = not services["games"]

        keys = ["default", "cdn", "amazon"]
        if services["youtube"]:
            keys.append("youtube")
        if services["discord"]:
            keys.append("discord")
        if services["instagram"]:
            keys.append("instagram")
        if services["games"]:
            keys.append("games")

        domains = combine_domain_sets(ctx, keys)
        urls = [u.url for u in prepare_urls(base_urls=domains, include_default=True, include_suite=True)]
        lines.append(f"domain_set: {','.join(keys)}")

        # Step C: run test session
        safe_print(f"\n{C.MAGENTA}Запускаю подбор стратегий (base: v + flowseal){C.RESET}\n")
        summary = test_session(
            ctx,
            group="all",
            domains=urls,
            out_name="results_key_setup_full.txt",
            top_n=3,
            parallel=8,
            ensure_runtime=True,
            ensure_flowseal=True,
            ensure_stressozz=True,
        )
        ranked = sorted(summary.results, key=lambda x: (x.ok, x.total, x.strategy), reverse=True)
        top = [r for r in ranked if r.total > 0][:3]
        safe_print(f"\n{C.GREEN}Top-3 стратегии:{C.RESET}")
        for r in top:
            safe_print(f"- {r.strategy}: {r.summary_text()}")
        lines.append("top3: " + ", ".join(f"{r.strategy}({r.ok}/{r.total})" for r in top))

        if top:
            ans = ask("\nПрименить лучшую стратегию как base? (Y/n): ").strip().lower()
            if ans in {"", "y", "yes"}:
                best = top[0].strategy
                base = find_strategy(ctx, best, kind="base") or find_strategy(ctx, best)
                if not base:
                    raise RuntimeError(f"strategy not found: {best}")
                ctx.state.zapret.base_strategy = base.name
                ctx.state.zapret.selected_strategy = base.name
                save_state(ctx.paths.state_file, ctx.state)
                start_zapret_interactive(ctx, base)
                lines.append(f"applied: {base.name}")

        return lines
    except Exception:
        ctx.state = state_backup
        save_state(ctx.paths.state_file, ctx.state)
        if hosts_backup:
            HostsManager(ctx).restore(hosts_backup)
        raise

