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


class FlowsealImportStats(dict):
    """Small dict-like stats container."""


def _stats_inc(stats: dict[str, int], key: str) -> None:
    stats[key] = int(stats.get(key, 0)) + 1


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
    if any(name.startswith(p + "_") or name.startswith(p + "-") or (name.startswith(p) and name.endswith(".bat")) for p in helper_prefixes):
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
    stats: dict[str, int] = {
        "imported": 0,
        "skipped_helpers": 0,
        "skipped_no_winws": 0,
        "skipped_no_interesting_args": 0,
        "skipped_no_cmd": 0,
    }
    for bat in sorted(flowseal_root.glob("*.bat")):
        text = bat.read_text(encoding="utf-8", errors="replace")
        low = (text or "").lower()
        if bat.name.lower() in _SKIP_BAT_NAMES:
            _stats_inc(stats, "skipped_helpers")
            log.debug("flowseal import: skipped helper %s", bat)
            continue
        if ("winws.exe" not in low and "winws2.exe" not in low):
            _stats_inc(stats, "skipped_no_winws")
            log.debug("flowseal import: skipped no-winws %s", bat)
            continue
        interesting = ("--filter-", "--dpi-desync", "--wf-", "--hostlist", "--ipset")
        if not any(tok in low for tok in interesting):
            _stats_inc(stats, "skipped_no_interesting_args")
            log.debug("flowseal import: skipped no-interesting-args %s", bat)
            continue
        if not _is_probably_strategy_bat(bat, text):
            _stats_inc(stats, "skipped_helpers")
            log.debug("flowseal import: skipped helper-like %s", bat)
            continue
        cmd = extract_winws_command(text)
        if not cmd:
            _stats_inc(stats, "skipped_no_cmd")
            log.debug("flowseal import: skipped no-command %s", bat)
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
        _stats_inc(stats, "imported")

    log.info(
        "flowseal import summary: imported=%s skipped_helpers=%s skipped_no_winws=%s skipped_no_interesting_args=%s skipped_no_cmd=%s root=%s",
        stats.get("imported", 0),
        stats.get("skipped_helpers", 0),
        stats.get("skipped_no_winws", 0),
        stats.get("skipped_no_interesting_args", 0),
        stats.get("skipped_no_cmd", 0),
        flowseal_root,
    )
    return count

