from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from zapret_manager.core.config import AppConfig, load_config
from zapret_manager.core.log import setup_logging
from zapret_manager.core.paths import Paths
from zapret_manager.core.state import AppState, load_state
from zapret_manager.features.zapret_runtime import require_runtime_ok


@dataclass(frozen=True)
class AppContext:
    root: Path
    paths: Paths
    config: AppConfig
    state: AppState

    @staticmethod
    def bootstrap(argv: list[str]) -> "AppContext":
        root = Paths.detect_root()
        paths = Paths.from_root(root)
        paths.ensure_dirs()

        setup_logging(paths.logs_dir / "zapret_manager.log")

        config = load_config(paths.config_file)
        state = load_state(paths.state_file)
        ctx = AppContext(root=root, paths=paths, config=config, state=state)
        # Ensure bundled runtime exists. (Portable app should ship with runtime.)
        try:
            require_runtime_ok(ctx)
        except Exception:
            # Do not crash bootstrap; UI will show status/error on start actions.
            pass
        return ctx

