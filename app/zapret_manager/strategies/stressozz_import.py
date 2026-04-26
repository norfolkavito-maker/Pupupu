from __future__ import annotations

import re
from pathlib import Path

from app.zapret_manager.strategies.model import Strategy
from app.zapret_manager.strategies.store import save_strategy


def _map_linux_paths(args: list[str]) -> list[str]:
    """Заменяет Linux-пути из Zapret-Manager.sh на плейсхолдеры."""
    out = []
    for a in args:
        a = a.replace("/opt/zapret/files/fake/", "{FAKE:")
        a = re.sub(r"\{FAKE:([^ ]+)\.bin", r"{FAKE:\1.bin}", a)
        a = a.replace("/opt/zapret/ipset/", "{LISTS}")
        out.append(a)
    return out


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
            args.append(ln)
        args = _map_linux_paths(args)
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
    for m in re.finditer(r"\bstrategy_(v\d+)\s*\(\)\s*\{", script_text):
        name = m.group(1)
        start = m.start()
        end = script_text.find("}", m.end())
        if end == -1:
            continue
        body = script_text[m.end() : end]
        args = re.findall(r"\"(--[^\"]+)\"", body)
        if not args:
            continue
        args = _map_linux_paths(args)
        st = Strategy(
            name=name,
            engine="winws",
            args=args,
            source_file="Zapret-Manager.sh",
            upstream=upstream_name,
            kind="base",
        )
        save_strategy(generated_dir, st)
        count += 1
    return count


def import_dv_strategies_from_script(
    *,
    script_text: str,
    generated_dir: Path,
    upstream_name: str = "stressozz",
) -> int:
    """
    Извлекает Dv1..Dv17 из Zapret-Manager.sh (формат DvN=$'...\n...').
    """
    count = 0
    # Pattern: Dv1=$'--filter-tcp=...\n--hostlist-domains=...'
    pattern = re.compile(r"^Dv(\d+)=[\$\']*'([\s\S]*?)'(?:\s*$)", re.MULTILINE)
    for m in pattern.finditer(script_text):
        num = m.group(1)
        body = m.group(2)
        name = f"Dv{num}"
        args = [ln.strip() for ln in body.splitlines() if ln.strip() and not ln.strip().startswith("#")]
        if not args:
            continue
        args = _map_linux_paths(args)
        st = Strategy(
            name=name,
            engine="winws",
            args=args,
            source_file="Zapret-Manager.sh",
            upstream=upstream_name,
            kind="discord",
        )
        save_strategy(generated_dir, st)
        count += 1
    return count

