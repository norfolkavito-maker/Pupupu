from __future__ import annotations

import logging
from pathlib import Path

from zapret_manager.strategies.flowseal_parser import extract_winws_command
from zapret_manager.strategies.model import Strategy
from zapret_manager.strategies.store import save_strategy


log = logging.getLogger(__name__)


def import_flowseal_strategies(
    *,
    flowseal_root: Path,
    generated_dir: Path,
    upstream_name: str = "flowseal",
) -> int:
    """
    Сканирует .bat в корне Flowseal и генерирует Strategy json.
    """
    count = 0
    for bat in sorted(flowseal_root.glob("*.bat")):
        text = bat.read_text(encoding="utf-8", errors="replace")
        cmd = extract_winws_command(text)
        if not cmd:
            continue
        name = bat.stem
        kind = "base"
        low = name.lower()
        if low.startswith("yv"):
            kind = "youtube"
        elif low.startswith("dv"):
            kind = "discord"
        st = Strategy(
            name=name,
            engine=cmd.engine,
            args=cmd.args,
            source_file=str(bat),
            upstream=upstream_name,
            kind=kind,
        )
        save_strategy(generated_dir, st)
        count += 1

    log.info("imported %s strategies from %s", count, flowseal_root)
    return count

