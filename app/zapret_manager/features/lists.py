from __future__ import annotations

import logging
from pathlib import Path

from zapret_manager.core.app_context import AppContext
from zapret_manager.upstreams.http import download
from zapret_manager.utils.timex import now_utc_iso


log = logging.getLogger(__name__)


EXCLUDE_URL = "https://raw.githubusercontent.com/StressOzz/Zapret-Manager/refs/heads/main/zapret-hosts-user-exclude.txt"
RKN_URL = "https://raw.githubusercontent.com/IndeecFOX/zapret4rocket/refs/heads/master/extra_strats/TCP/RKN/List.txt"


def exclude_file(ctx: AppContext) -> Path:
    return (ctx.paths.lists_dir / "exclude.txt").resolve()


def rkn_file(ctx: AppContext) -> Path:
    return (ctx.paths.lists_dir / "rkn.txt").resolve()


def update_exclude(ctx: AppContext) -> Path:
    dest = exclude_file(ctx)
    download(EXCLUDE_URL, dest)
    meta = ctx.paths.lists_dir / "exclude.meta.txt"
    meta.write_text(f"updated_at_utc={now_utc_iso()}\nurl={EXCLUDE_URL}\n", encoding="utf-8")
    return dest


def update_rkn(ctx: AppContext) -> Path:
    dest = rkn_file(ctx)
    download(RKN_URL, dest)
    meta = ctx.paths.lists_dir / "rkn.meta.txt"
    meta.write_text(f"updated_at_utc={now_utc_iso()}\nurl={RKN_URL}\n", encoding="utf-8")
    return dest

