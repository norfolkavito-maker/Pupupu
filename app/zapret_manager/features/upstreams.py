from __future__ import annotations

import logging
from pathlib import Path

from zapret_manager.core.app_context import AppContext
from zapret_manager.core.state import save_state
from zapret_manager.strategies.flowseal_import import import_flowseal_strategies
from zapret_manager.strategies.stressozz_import import (
    import_dv_strategies_from_script,
    import_liststryou,
    import_v_strategies_from_script,
)
from zapret_manager.upstreams.http import download
from zapret_manager.upstreams.sources import RawUrlSource, RepoZipSource, load_sources
from zapret_manager.upstreams.sync import check_update, sync_repo_zip
from zapret_manager.utils.timex import now_utc_iso


log = logging.getLogger(__name__)


def get_sources(ctx: AppContext) -> dict[str, object]:
    return load_sources(ctx.paths.sources_file)


def check_updates(ctx: AppContext) -> dict[str, tuple[bool, str]]:
    sources = load_sources(ctx.paths.sources_file)
    results: dict[str, tuple[bool, str]] = {}
    for name, src in sources.items():
        try:
            changed, msg = check_update(src, ctx.state)
            results[name] = (changed, msg)
        except Exception as e:
            results[name] = (False, f"error: {e}")
    return results


def sync_zapret_runtime(ctx: AppContext) -> None:
    """Disabled in portable mode.

    Runtime must be shipped bundled inside the release. We do not download it
    for the user.
    """
    raise RuntimeError("Runtime sync is disabled (portable bundle ships runtime).")


def sync_flowseal(ctx: AppContext, *, generated_dir: Path | None = None) -> int:
    sources = load_sources(ctx.paths.sources_file)
    src = sources.get("flowseal")
    if not isinstance(src, RepoZipSource):
        raise RuntimeError("sources.yaml: flowseal must be repo_zip")

    dest = (ctx.paths.upstreams_dir / "flowseal").resolve()
    sync_repo_zip(src, dest_dir=dest, cache_dir=ctx.paths.cache_dir, app_state=ctx.state)

    # regenerate strategies
    out_dir = generated_dir or ctx.paths.strategies_generated_dir
    count = import_flowseal_strategies(flowseal_root=dest, generated_dir=out_dir)
    save_state(ctx.paths.state_file, ctx.state)
    return count


def sync_stressozz_strategies(ctx: AppContext, *, generated_dir: Path | None = None) -> int:
    sources = load_sources(ctx.paths.sources_file)
    src = sources.get("stress_ozz_manager")
    if not isinstance(src, RawUrlSource):
        raise RuntimeError("sources.yaml: stress_ozz_manager must be raw_url")

    dest = (ctx.paths.upstreams_dir / "stressozz").resolve()
    dest.mkdir(parents=True, exist_ok=True)
    script_path = dest / "Zapret-Manager.sh"
    download(src.url, script_path)
    script_text = script_path.read_text(encoding="utf-8", errors="replace")

    count = 0
    out_dir = generated_dir or ctx.paths.strategies_generated_dir

    count += import_v_strategies_from_script(
        script_text=script_text,
        generated_dir=out_dir,
        upstream_name="stressozz",
    )
    count += import_liststryou(
        list_text=script_text,
        generated_dir=out_dir,
        upstream_name="stressozz",
    )
    count += import_dv_strategies_from_script(
        script_text=script_text,
        generated_dir=out_dir,
        upstream_name="stressozz",
    )

    save_state(ctx.paths.state_file, ctx.state)
    log.info("imported %s strategies from StressOzz", count)
    return count

