from __future__ import annotations

import logging
from pathlib import Path

from app.zapret_manager.strategies.flowseal_parser import extract_winws_command
from app.zapret_manager.strategies.model import Strategy
from app.zapret_manager.strategies.store import save_strategy


log = logging.getLogger(__name__)


_SKIP_BAT_NAMES = {
    # Not a strategy (service/installer/helpers)
    "service.bat",
    "install.bat",
    "update.bat",
    "uninstall.bat",
    "start.bat",
    "stop.bat",
}


def _is_probably_strategy_bat(path: Path, text: str) -> bool:
    """Best-effort filter to avoid importing helper .bat files as winws strategies."""
    name = path.name.lower()
    if name in _SKIP_BAT_NAMES:
        return False
    # Skip common helper patterns.
    helper_prefixes = (
        "service",
        "install",
        "update",
        "uninstall",
        "start",
        "stop",
        "helper",
        "setup",
        "readme",
    )
    if any(name.startswith(p + "_") or name.startswith(p + "-") or name.startswith(p) and name.endswith(".bat") for p in helper_prefixes):
        # allow real strategies like yvNN/dvNN/vNN even if they contain these tokens
        stem = path.stem.lower()
        if stem.startswith("yv") or stem.startswith("dv") or (stem.startswith("v") and stem[1:].isdigit()):
            return True
        return False

    low = (text or "").lower()
    # Heuristic: a strategy bat should actually invoke winws.exe with DPI args.
    if "winws.exe" not in low and "winws2.exe" not in low:
        return False
    # Many helper scripts also mention winws; require at least one known option.
    interesting = ("--filter-", "--dpi-desync", "--wf-", "--hostlist", "--ipset")
    if not any(tok in low for tok in interesting):
        return False
    return True


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
        if not _is_probably_strategy_bat(bat, text):
            continue
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

