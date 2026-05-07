
from pathlib import Path
from dataclasses import dataclass


@dataclass
class AppPaths:
    root_dir: Path
    data_dir: Path

    config_path: Path
    state_path: Path
    current_state_path: Path
    problem_domains_path: Path
    nodes_path: Path

    logs_dir: Path
    reports_dir: Path
    backups_dir: Path
    snapshots_dir: Path
    telemetry_dir: Path

    runtime_dir: Path
    zapret_runtime_dir: Path
    singbox_runtime_dir: Path

    strategies_dir: Path
    builtin_strategies_dir: Path
    generated_strategies_dir: Path
    custom_strategies_dir: Path

    upstreams_dir: Path


def get_project_root(start_path: Optional[Path] = None) -> Path:
    # Find the project root by looking for a unique marker file, e.g., 'README.md'
    if start_path is None:
        start_path = Path(__file__).parent

    current_dir = start_path
    for parent in current_dir.parents:
        if (parent / "README.md").exists():
            return parent
    return Path.cwd() # Fallback if no marker found


def create_app_paths() -> AppPaths:
    root = get_project_root()
    data = root / "DedZapretData"

    paths = AppPaths(
        root_dir=root,
        data_dir=data,

        config_path=root / "config.yaml",
        state_path=data / "state.json",
        current_state_path=data / "current.json",
        problem_domains_path=data / "problem_domains.json",
        nodes_path=data / "nodes.json",

        logs_dir=data / "logs",
        reports_dir=data / "reports",
        backups_dir=data / "backups",
        snapshots_dir=data / "snapshots",
        telemetry_dir=data / "data" / "telemetry",

        runtime_dir=data / "runtime",
        zapret_runtime_dir=data / "runtime" / "zapret",
        singbox_runtime_dir=data / "runtime" / "sing-box",

        strategies_dir=data / "strategies",
        builtin_strategies_dir=data / "strategies" / "builtin",
        generated_strategies_dir=data / "strategies" / "generated",
        custom_strategies_dir=data / "strategies" / "custom",

        upstreams_dir=data / "data" / "upstreams",
    )
    return paths


def ensure_directories(paths: AppPaths) -> None:
    dirs_to_create = [
        paths.data_dir,
        paths.logs_dir,
        paths.reports_dir,
        paths.backups_dir,
        paths.snapshots_dir,
        paths.telemetry_dir,
        paths.runtime_dir,
        paths.zapret_runtime_dir,
        paths.singbox_runtime_dir,
        paths.strategies_dir,
        paths.builtin_strategies_dir,
        paths.generated_strategies_dir,
        paths.custom_strategies_dir,
        paths.upstreams_dir,
    ]
    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)
