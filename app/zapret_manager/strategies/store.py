from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from app.zapret_manager.strategies.model import Strategy
from app.zapret_manager.strategies.validation import StrategyValidator

if TYPE_CHECKING:
    from app.zapret_manager.core.app_context import AppContext


log = logging.getLogger(__name__)


def _is_strategy_file(p: Path) -> bool:
    # generated/index.json is an internal cache/index, not a Strategy.
    # Also skip hidden files.
    if p.name.startswith("."):
        return False
    if p.name.lower() == "index.json":
        return False
    return True


def list_strategies(ctx: "AppContext", dir_path: Path, kind: str | None = None) -> list[Strategy]:
    if not dir_path.exists():
        return []

    validator = StrategyValidator(ctx)
    out: list[Strategy] = []
    files = sorted(list(dir_path.glob("*.json")) + list(dir_path.glob("*.yaml")) + list(dir_path.glob("*.yml")))
    for p in files:
        if not _is_strategy_file(p):
            continue
        try:
            if p.suffix.lower() == ".json":
                data = json.loads(p.read_text(encoding="utf-8"))
            else:
                data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}

            # --- Basic structural validation for raw dict before Pydantic model parsing ---
            if not isinstance(data, dict):
                log.warning("invalid strategy file %s: expected dict, got %s", p, type(data).__name__)
                continue
            if not data.get("id") and p.stem:
                data["id"] = p.stem  # Derive ID from filename if missing
            if not data.get("name"):
                log.warning("invalid strategy file %s: missing required field 'name'", p)
                continue
            if "commands" not in data:
                log.warning("invalid strategy file %s: missing required field 'commands'", p)
                continue
            if not isinstance(data.get("commands"), list):
                log.warning("invalid strategy file %s: field 'commands' must be a list", p)
                continue

            st = Strategy.from_json(data)
            st.source_file = str(p)

            # --- Advanced content validation with StrategyValidator ---
            validation_result = validator.validate(st)
            st.is_valid = validation_result.is_valid
            st.validation_errors = validation_result.errors
            st.missing_assets = validation_result.missing_assets
            st.unresolved_placeholders = validation_result.unresolved_placeholders

            if kind is None or st.kind == kind:
                out.append(st)

        except Exception as e:
            log.warning("failed to load strategy file %s: %s", p, e)
            # Create an invalid strategy to represent the parsing failure
            invalid_strategy_id = p.stem or "unknown"
            invalid_strategy_name = p.stem or "Unknown Strategy"
            invalid_st = Strategy(
                id=invalid_strategy_id,
                name=invalid_strategy_name,
                commands=[],
                source_file=str(p),
                is_valid=False,
                validation_errors=[f"Failed to parse/load: {e}"],
            )
            out.append(invalid_st)
            continue
    return out


def save_strategy(ctx: "AppContext", dir_path: Path, strategy: Strategy) -> Path:
    dir_path.mkdir(parents=True, exist_ok=True)
    p = dir_path / f"{strategy.id}.json"
    p.write_text(json.dumps(strategy.to_json(), ensure_ascii=False, indent=2), encoding="utf-8")
    return p
