from __future__ import annotations

os_import = __import__('os')
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from app.zapret_manager.strategies.model import Strategy
from app.zapret_manager.strategies.store import list_strategies as load_strategies_from_dir


log = logging.getLogger(__name__)


@dataclass
class StrategyIndex:
    name: str
    kind: str
    upstream: str
    source_file: str
    engine: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "upstream": self.upstream,
            "source_file": self.source_file,
            "engine": self.engine,
        }

    @staticmethod
    def from_dict(data: dict) -> StrategyIndex:
        return StrategyIndex(
            name=data["name"],
            kind=data.get("kind", "base"),
            upstream=data.get("upstream", ""),
            source_file=data.get("source_file", ""),
            engine=data.get("engine", "winws"),
        )


class StrategyManager:
    def __init__(self, strategies_dir: Path):
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
                return self._index
            except Exception as e:
                log.warning("Failed to load strategy index: %s. Rebuilding...", e)

        # Перестройка индекса
        self.rebuild_index()
        return self._index

    def rebuild_index(self):
        """Сканирует директорию и создает новый индекс."""
        log.info("Rebuilding strategy index in %s", self.strategies_dir)
        strategies = load_strategies_from_dir(self.strategies_dir)
        self._index = []
        for s in strategies:
            idx = StrategyIndex(
                name=s.name,
                kind=s.kind,
                upstream=s.upstream,
                source_file=s.source_file,
                engine=s.engine
            )
            self._index.append(idx)
            self._cache[s.name] = s

        try:
            self.strategies_dir.mkdir(parents=True, exist_ok=True)
            self.index_file.write_text(
                json.dumps([idx.to_dict() for idx in self._index], ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            log.error("Failed to save strategy index: %s", e)
        
        self._loaded = True

    def get_strategy(self, name: str) -> Optional[Strategy]:
        """Возвращает полную стратегию по имени, используя кэш."""
        if name in self._cache:
            return self._cache[name]

        # Пытаемся найти файл напрямую
        for ext in [".json", ".yaml", ".yml"]:
            p = self.strategies_dir / f"{name}{ext}"
            if p.exists():
                try:
                    if ext == ".json":
                        data = json.loads(p.read_text(encoding="utf-8"))
                    else:
                        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                    s = Strategy.from_json(data)
                    self._cache[name] = s
                    return s
                except Exception as e:
                    log.error("Failed to load strategy %s: %s", name, e)
        
        return None

    def list_by_kind(self, kind: str) -> List[StrategyIndex]:
        """Возвращает список стратегий определенного типа из индекса."""
        if not self._loaded:
            self.load_all()
        return [idx for idx in self._index if idx.kind == kind]
