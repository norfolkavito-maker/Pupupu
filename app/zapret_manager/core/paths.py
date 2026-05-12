"""Canonical portable path resolver.

Phase 2 goal: a single, deterministic, portable layout resolver.

Target layout:

DedZapret.exe
DedZapretData/
  config.yaml
  sources.yaml
  runtime/
    zapret/
      winws.exe
      winws2.exe
      WinDivert.dll
      WinDivert64.sys
      files/fake/
      files/lists/
      blockcheck/
    sing-box/
      sing-box.exe
  data/
    strategies/{builtin,generated,custom}
    lists/
    nodes/
    profiles/
    state/
    logs/
    backups/
    reports/
    upstreams/{flowseal,stressozz}

Compatibility notes:
- Older code/tests referenced AppPaths/create_app_paths; we keep thin aliases.
- Callers should prefer Paths.detect_root/from_root + attributes like
  config_file, sources_file, data_dir, runtime_dir, lists_dir, upstreams_dir.
"""

from __future__ import annotations
from dataclasses import dataclass
import os
from pathlib import Path
import sys
from typing import Optional


@dataclass(frozen=True)
class Paths:
    """Portable paths resolved from a detected root directory."""

    root: Path

    # Top-level portable data root
    data_root: Path  # DedZapretData

    # Config files
    config_file: Path  # DedZapretData/config.yaml
    sources_file: Path  # DedZapretData/sources.yaml

    # Runtime roots
    runtime_dir: Path  # DedZapretData/runtime
    zapret_runtime_dir: Path  # DedZapretData/runtime/zapret
    singbox_runtime_dir: Path  # DedZapretData/runtime/sing-box
    singbox_bin: Path  # bin/sing-box/sing-box.exe

    # Working data roots
    data_dir: Path  # DedZapretData/data
    lists_dir: Path  # DedZapretData/data/lists
    strategies_dir: Path  # DedZapretData/data/strategies
    strategies_builtin_dir: Path
    strategies_generated_dir: Path
    strategies_custom_dir: Path

    state_dir: Path  # DedZapretData/data/state
    state_file: Path  # state.json
    current_state_file: Path  # current.json

    logs_dir: Path  # DedZapretData/data/logs
    reports_dir: Path  # DedZapretData/data/reports
    backups_dir: Path  # DedZapretData/data/backups
    cache_dir: Path  # DedZapretData/data/cache
    results_dir: Path  # DedZapretData/data/results
    telemetry_dir: Path  # DedZapretData/data/telemetry

    upstreams_dir: Path  # DedZapretData/data/upstreams
    flowseal_dir: Path
    flowseal_bin_dir: Path
    flowseal_lists_dir: Path
    stressozz_dir: Path

    nodes_dir: Path  # DedZapretData/data/nodes
    profiles_dir: Path  # DedZapretData/data/profiles

    @staticmethod
    def detect_root() -> Path:
        """Detect portable root.

        - In PyInstaller/packed mode: directory of sys.executable.
        - In source/dev mode: repository root (marker: README.md).
        """
        try:
            if getattr(sys, "frozen", False):
                return Path(sys.executable).resolve().parent
        except Exception:
            pass

        # Source mode: find README.md upwards from this file.
        start = Path(__file__).resolve()
        for p in [start] + list(start.parents):
            if (p / "README.md").exists():
                return p
        return Path.cwd().resolve()

    @staticmethod
    def from_root(root: Path) -> "Paths":
        root = Path(root).resolve()
        data_root = (root / "DedZapretData").resolve()

        # Canonical roots
        runtime_dir = (data_root / "runtime").resolve()
        zapret_runtime_dir = (runtime_dir / "zapret").resolve()
        singbox_runtime_dir = (runtime_dir / "sing-box").resolve()

        data_dir = (data_root / "data").resolve()
        lists_dir = (data_dir / "lists").resolve()
        strategies_dir = (data_dir / "strategies").resolve()

        state_dir = (data_dir / "state").resolve()
        logs_dir = (data_dir / "logs").resolve()
        reports_dir = (data_dir / "reports").resolve()
        backups_dir = (data_dir / "backups").resolve()
        cache_dir = (data_dir / "cache").resolve()
        results_dir = (data_dir / "results").resolve()
        telemetry_dir = (data_dir / "telemetry").resolve()

        upstreams_dir = (data_dir / "upstreams").resolve()
        flowseal_dir = (upstreams_dir / "flowseal").resolve()
        flowseal_bin_dir = (flowseal_dir / "bin").resolve()
        flowseal_lists_dir = (flowseal_dir / "lists").resolve()
        stressozz_dir = (upstreams_dir / "stressozz").resolve()

        nodes_dir = (data_dir / "nodes").resolve()
        profiles_dir = (data_dir / "profiles").resolve()

        return Paths(
            root=root,
            data_root=data_root,
            config_file=(data_root / "config.yaml").resolve(),
            sources_file=(data_root / "sources.yaml").resolve(),
            runtime_dir=runtime_dir,
            zapret_runtime_dir=zapret_runtime_dir,
            singbox_runtime_dir=singbox_runtime_dir,
            singbox_bin=(root / "bin" / "sing-box" / "sing-box.exe").resolve(),
            data_dir=data_dir,
            lists_dir=lists_dir,
            strategies_dir=strategies_dir,
            strategies_builtin_dir=(strategies_dir / "builtin").resolve(),
            strategies_generated_dir=(strategies_dir / "generated").resolve(),
            strategies_custom_dir=(strategies_dir / "custom").resolve(),
            state_dir=state_dir,
            state_file=(state_dir / "state.json").resolve(),
            current_state_file=(state_dir / "current.json").resolve(),
            logs_dir=logs_dir,
            reports_dir=reports_dir,
            backups_dir=backups_dir,
            cache_dir=cache_dir,
            results_dir=results_dir,
            telemetry_dir=telemetry_dir,
            upstreams_dir=upstreams_dir,
            flowseal_dir=flowseal_dir,
            flowseal_bin_dir=flowseal_bin_dir,
            flowseal_lists_dir=flowseal_lists_dir,
            stressozz_dir=stressozz_dir,
            nodes_dir=nodes_dir,
            profiles_dir=profiles_dir,
        )

    def ensure_dirs(self) -> None:
        """Create known directories.

        Must be safe in unit tests: no network, no admin, no destructive actions.
        """
        dirs = [
            self.data_root,
            self.runtime_dir,
            self.zapret_runtime_dir,
            self.singbox_runtime_dir,
            self.data_dir,
            self.lists_dir,
            self.strategies_dir,
            self.strategies_builtin_dir,
            self.strategies_generated_dir,
            self.strategies_custom_dir,
            self.state_dir,
            self.logs_dir,
            self.reports_dir,
            self.backups_dir,
            self.cache_dir,
            self.results_dir,
            self.telemetry_dir,
            self.upstreams_dir,
            self.flowseal_dir,
            self.stressozz_dir,
            self.nodes_dir,
            self.profiles_dir,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    # ---- Backward-compatible aliases (do not use for new code) ----
    @property
    def root_dir(self) -> Path:  # legacy name
        return self.root

    # Legacy attribute aliases used by old tests. Keep them mapped to the new
    # canonical layout.
    @property
    def config_path(self) -> Path:
        # old tests expected root/config.yaml
        return (self.root / "config.yaml").resolve()

    @property
    def state_path(self) -> Path:
        # old tests expected DedZapretData/state.json
        return (self.data_root / "state.json").resolve()

    @property
    def current_state_path(self) -> Path:
        return (self.data_root / "current.json").resolve()

    @property
    def problem_domains_path(self) -> Path:
        return (self.data_root / "problem_domains.json").resolve()

    @property
    def nodes_path(self) -> Path:
        return (self.data_root / "nodes.json").resolve()

    # NOTE: more legacy aliases removed; tests were updated to assert canonical
    # directories under DedZapretData/data/*.


# Legacy names still referenced by a few tests/modules.
AppPaths = Paths


def get_project_root(start_path: Optional[Path] = None) -> Path:
    # Legacy helper (used only by older tests). Prefer Paths.detect_root().
    if start_path is None:
        start_path = Path(__file__).resolve().parent
    for p in [start_path] + list(start_path.parents):
        if (p / "README.md").exists():
            return p
    return Path.cwd().resolve()


def create_app_paths() -> AppPaths:
    # Legacy helper (tests expect it). Prefer Paths.from_root(Paths.detect_root()).
    return Paths.from_root(get_project_root())


def ensure_directories(paths: AppPaths) -> None:
    # Legacy helper name. Prefer Paths.ensure_dirs().
    paths.ensure_dirs()
