from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.zapret_manager.core.config import AppConfig, load_config
from app.zapret_manager.core.diagnostics import SessionRecorder, set_global_recorder
from app.zapret_manager.core.log import setup_logging
from app.zapret_manager.core.paths import Paths
from app.zapret_manager.core.state import AppState, load_state


@dataclass(frozen=True)
class AppContext:
    root: Path
    paths: Paths
    config: AppConfig
    state: AppState
    diagnostics: SessionRecorder

    @staticmethod
    def bootstrap(argv: list[str]) -> "AppContext":
        root = Paths.detect_root()
        paths = Paths.from_root(root)
        paths.ensure_dirs()

        setup_logging(paths.logs_dir / "zapret_manager.log")

        config = load_config(paths.config_file)
        state = load_state(paths.state_file)

        # Diagnostics session recorder (opt-in). Always create an instance so
        # other modules can call diag_log() safely.
        rec = SessionRecorder(
            logs_dir=paths.logs_dir,
            enabled=bool(getattr(config, "diagnostics", None) and config.diagnostics.enabled),
            record_console_io=bool(getattr(config.diagnostics, "record_console_io", True))
            if getattr(config, "diagnostics", None)
            else True,
            record_subprocess=bool(getattr(config.diagnostics, "record_subprocess", True))
            if getattr(config, "diagnostics", None)
            else True,
            max_text_len=int(getattr(config.diagnostics, "max_text_len", 8000))
            if getattr(config, "diagnostics", None)
            else 8000,
            redact_paths=bool(getattr(config.diagnostics, "redact_paths", False))
            if getattr(config, "diagnostics", None)
            else False,
        )
        set_global_recorder(rec)

        ctx = AppContext(root=root, paths=paths, config=config, state=state, diagnostics=rec)
        # Ensure bundled runtime exists. (Portable app should ship with runtime.)
        try:
            from app.zapret_manager.features.zapret_runtime import require_runtime_ok

            require_runtime_ok(ctx)
        except Exception:
            # Do not crash bootstrap; UI will show status/error on start actions.
            pass
        return ctx

