from __future__ import annotations

import re
from pathlib import Path

from zapret_manager.strategies.model import Strategy
from zapret_manager.strategies.store import save_strategy


def import_liststryou(
    *,
    list_text: str,
    generated_dir: Path,
    upstream_name: str = "stressozz",
) -> int:
    """
    Парсит ListStrYou (YvNN блоки) в стратегии для winws.
    """
    current_name: str | None = None
    current_body: list[str] = []
    count = 0

    def flush() -> None:
        nonlocal count, current_name, current_body
        if not current_name:
            return
        args = []
        for ln in current_body:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            # map linux paths to placeholders
            ln = ln.replace("/opt/zapret/files/fake/", "{FAKE:").replace(".bin", ".bin}")
            ln = ln.replace("/opt/zapret/ipset/", "{LISTS}")
            args.append(ln)
        st = Strategy(
            name=current_name,
            engine="winws",
            args=args,
            source_file="ListStrYou",
            upstream=upstream_name,
            kind="youtube",
        )
        save_strategy(generated_dir, st)
        count += 1

    for raw in list_text.splitlines():
        line = raw.strip()
        if re.match(r"^Yv\d+\b", line):
            flush()
            current_name = line.split()[0]
            current_body = []
            continue
        if current_name:
            current_body.append(raw)
    flush()
    return count


def import_v_strategies_from_script(
    *,
    script_text: str,
    generated_dir: Path,
    upstream_name: str = "stressozz",
) -> int:
    """
    Извлекает strategy_vN() { printf "%s\\n" ... } из Zapret-Manager.sh
    и делает стратегии vN.
    """
    count = 0
    # best-effort: find function blocks starting with strategy_vN()
    for m in re.finditer(r"\bstrategy_(v\d+)\s*\(\)\s*\{", script_text):
        name = m.group(1)
        start = m.start()
        # take a window until next "}\n" after start
        end = script_text.find("}", m.end())
        if end == -1:
            continue
        body = script_text[m.end() : end]
        # collect quoted args that look like --something or --new
        args = re.findall(r"\"(--[^\"]+)\"", body)
        if not args:
            continue
        # map linux paths to placeholders
        args2 = []
        for a in args:
            a = a.replace("/opt/zapret/files/fake/", "{FAKE:")
            a = re.sub(r"\{FAKE:([^ ]+)\.bin", r"{FAKE:\1.bin}", a)
            a = a.replace("/opt/zapret/ipset/", "{LISTS}")
            args2.append(a)
        st = Strategy(
            name=name,
            engine="winws",
            args=args2,
            source_file="Zapret-Manager.sh",
            upstream=upstream_name,
            kind="base",
        )
        save_strategy(generated_dir, st)
        count += 1
    return count

