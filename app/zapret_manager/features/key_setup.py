from __future__ import annotations

import logging
from copy import deepcopy

from zapret_manager.core.app_context import AppContext
from zapret_manager.core.state import save_state
from zapret_manager.features.hosts import HostsManager
from zapret_manager.features.lists import update_exclude
from zapret_manager.features.selection import find_strategy
from zapret_manager.features.upstreams import sync_flowseal, sync_stressozz_strategies
from zapret_manager.features.zapret_runtime import require_runtime_ok, start_zapret_interactive, stop_zapret
from zapret_manager.features.hosts import load_blocks_from_file, set_block_enabled


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

