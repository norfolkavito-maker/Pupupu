from __future__ import annotations

import json
import logging
from pathlib import Path

import yaml

from app.zapret_manager.strategies.model import Strategy


log = logging.getLogger(__name__)


def list_strategies(dir_path: Path, kind: str | None = None) -> list[Strategy]:
    if not dir_path.exists():
        return []
    out: list[Strategy] = []
    files = sorted(list(dir_path.glob("*.json")) + list(dir_path.glob("*.yaml")) + list(dir_path.glob("*.yml")))
    for p in files:
        try:
            if p.suffix.lower() == ".json":
                data = json.loads(p.read_text(encoding="utf-8"))
            else:
                data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            st = Strategy.from_json(data)
            if kind is None or st.kind == kind:
                out.append(st)
        except Exception as e:
            log.warning("failed to load strategy file %s: %s", p, e)
            continue
    return out


def save_strategy(dir_path: Path, strategy: Strategy) -> Path:
    dir_path.mkdir(parents=True, exist_ok=True)
    p = dir_path / f"{strategy.name}.json"
    p.write_text(json.dumps(strategy.to_json(), ensure_ascii=False, indent=2), encoding="utf-8")
    return p

