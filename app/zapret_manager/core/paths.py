from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Paths:
    root: Path
    config_file: Path
    sources_file: Path
    data_dir: Path
    state_file: Path
    logs_dir: Path
    cache_dir: Path
    lists_dir: Path
    upstreams_dir: Path
    runtime_dir: Path
    strategies_generated_dir: Path
    strategies_builtin_dir: Path
    strategies_custom_dir: Path
    results_dir: Path

    @staticmethod
    def detect_root() -> Path:
        # Prefer CWD (run.bat does cd into project root).
        cwd = Path.cwd()
        if (cwd / "config.yaml").exists() and (cwd / "sources.yaml").exists():
            return cwd

        # Fallback: directory of executable / script.
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent

        return Path(__file__).resolve().parents[3]

    @staticmethod
    def from_root(root: Path) -> "Paths":
        data_dir = root / "data"
        return Paths(
            root=root,
            config_file=root / "config.yaml",
            sources_file=root / "sources.yaml",
            data_dir=data_dir,
            state_file=data_dir / "state.json",
            logs_dir=data_dir / "logs",
            cache_dir=data_dir / "cache",
            lists_dir=data_dir / "lists",
            upstreams_dir=data_dir / "upstreams",
            runtime_dir=data_dir / "runtime",
            strategies_generated_dir=data_dir / "strategies" / "generated",
            strategies_builtin_dir=data_dir / "strategies" / "builtin",
            strategies_custom_dir=data_dir / "strategies" / "custom",
            results_dir=data_dir / "results",
        )

    def ensure_dirs(self) -> None:
        for d in [
            self.data_dir,
            self.logs_dir,
            self.cache_dir,
            self.lists_dir,
            self.upstreams_dir,
            self.runtime_dir,
            self.strategies_generated_dir,
            self.strategies_builtin_dir,
            self.strategies_custom_dir,
            self.results_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

