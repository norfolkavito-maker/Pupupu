from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

import yaml

from app.zapret_manager.strategies.model import Strategy, CommandType
from app.zapret_manager.strategies.store import list_strategies

if TYPE_CHECKING:
    from app.zapret_manager.core.app_context import AppContext


log = logging.getLogger(__name__)


@dataclass
class StrategyIndex:
    id: str
    name: str
    kind: str
    upstream: str
    source_file: str
    is_valid: bool
    validation_errors: list[str]
    missing_assets: list[str]
    unresolved_placeholders: list[str]
    # engine is now part of Command, so it's not directly in StrategyIndex

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "upstream": self.upstream,
            "source_file": self.source_file,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
            "missing_assets": self.missing_assets,
            "unresolved_placeholders": self.unresolved_placeholders,
        }

    @staticmethod
    def from_dict(data: dict) -> StrategyIndex:
        return StrategyIndex(
            id=data["id"],
            name=data["name"],
            kind=data.get("kind", "base"),
            upstream=data.get("upstream", ""),
            source_file=data.get("source_file", ""),
            is_valid=data.get("is_valid", True),
            validation_errors=data.get("validation_errors", []),
            missing_assets=data.get("missing_assets", []),
            unresolved_placeholders=data.get("unresolved_placeholders", []),
        )


class StrategyManager:
    def __init__(self, ctx: AppContext, strategies_dir: Path):
        self.ctx = ctx
        self.strategies_dir = strategies_dir
        self.index_file = strategies_dir / "index.json"
        self._cache: Dict[str, Strategy] = {}
        self._index: List[StrategyIndex] = []
        self._loaded = False

    def load_all(self, force_refresh: bool = False) -> List[StrategyIndex]:
        """Загружает индекс стратегий. Если индекса нет или force_refresh=True, перестраивает его."""
        if self._loaded and not force_refresh:
            return self._index

        if self.index_file.exists() and not force_refresh:
            try:
                data = json.loads(self.index_file.read_text(encoding="utf-8"))
                self._index = [StrategyIndex.from_dict(d) for d in data]
                self._loaded = True
                # After loading from index, populate cache from full strategy files if possible for valid strategies
                for idx in self._index:
                    if idx.is_valid:
                        # Attempt to load full strategy for valid entries into cache
                        try:
                            # Need to read the actual strategy file to get the full Strategy object
                            p = Path(idx.source_file)
                            if p.exists():
                                if p.suffix.lower() == ".json":
                                    strategy_data = json.loads(p.read_text(encoding="utf-8"))
                                else:
                                    strategy_data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                                self._cache[idx.id] = Strategy.from_json(strategy_data)
                        except Exception as e:
                            log.warning("Failed to load full strategy %s from %s for cache: %s", idx.id, idx.source_file, e)

                return self._index
            except Exception as e:
                log.warning("Failed to load strategy index: %s. Rebuilding...", e)

        # Перестройка индекса
        self.rebuild_index()
        return self._index

    def rebuild_index(self):
        """Сканирует директорию и создает новый индекс."""
        log.info("Rebuilding strategy index in %s", self.strategies_dir)
        strategies = list_strategies(self.ctx, self.strategies_dir) # Pass ctx here
        self._index = []
        self._cache = {}
        for s in strategies:
            idx = StrategyIndex(
                id=s.id,
                name=s.name,
                kind=s.kind,
                upstream=s.upstream,
                source_file=s.source_file,
                is_valid=s.is_valid,
                validation_errors=s.validation_errors,
                missing_assets=s.missing_assets,
                unresolved_placeholders=s.unresolved_placeholders,
            )
            self._index.append(idx)
            self._cache[s.id] = s  # Cache by ID now

        try:
            self.strategies_dir.mkdir(parents=True, exist_ok=True)
            self.index_file.write_text(
                json.dumps([idx.to_dict() for idx in self._index], ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            log.error("Failed to save strategy index: %s", e)
        
        self._loaded = True

    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """Возвращает полную стратегию по ID, используя кэш."""
        if strategy_id in self._cache:
            return self._cache[strategy_id]
        
        # If not in cache, try to load it from disk using list_strategies to ensure validation
        # This might be less efficient if called often, but ensures consistency.
        # A better approach would be to always populate the cache fully on load_all/rebuild_index.
        # For now, we will rely on rebuild_index populating the cache with validated strategies.
        self.load_all() # Ensure index and cache are loaded
        return self._cache.get(strategy_id) # Try to get from updated cache

    def list_by_kind(self, kind: str) -> List[StrategyIndex]:
        """Возвращает список стратегий определенного типа из индекса."""
        if not self._loaded:
            self.load_all()
        return [idx for idx in self._index if idx.kind == kind]
