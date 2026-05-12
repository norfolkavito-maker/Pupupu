from __future__ import annotations

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.strategies.model import Strategy
from app.zapret_manager.strategies.store import list_strategies


def find_strategy(ctx: AppContext, name: str, *, kind: str | None = None) -> Strategy | None:
    name = (name or "").strip()
    if not name:
        return None
    for st in (
        list_strategies(ctx, ctx.paths.strategies_builtin_dir)
        + list_strategies(ctx, ctx.paths.strategies_generated_dir)
        + list_strategies(ctx, ctx.paths.strategies_custom_dir)
    ):
        if st.name == name and (kind is None or st.kind == kind):
            return st
    return None


def list_bases(ctx: AppContext) -> list[Strategy]:
    return (
        list_strategies(ctx, ctx.paths.strategies_builtin_dir, kind="base")
        + list_strategies(ctx, ctx.paths.strategies_generated_dir, kind="base")
        + list_strategies(ctx, ctx.paths.strategies_custom_dir, kind="base")
    )


def list_layers(ctx: AppContext, kind: str) -> list[Strategy]:
    return list_strategies(ctx, ctx.paths.strategies_generated_dir, kind=kind) + list_strategies(
        ctx, ctx.paths.strategies_custom_dir, kind=kind
    )

