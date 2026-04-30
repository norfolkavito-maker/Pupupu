from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from app.zapret_manager.core.config import AppConfig, load_config
from app.zapret_manager.core.diagnostics import SessionRecorder, set_global_recorder
from app.zapret_manager.core.log import setup_logging
from app.zapret_manager.core.paths import Paths
from app.zapret_manager.core.state import AppState, load_state
from app.zapret_manager.strategies.manager import StrategyManager


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class AppContext:
    root: Path
    paths: Paths
    config: AppConfig
    state: AppState
    diagnostics: SessionRecorder
    
    # Strategy Managers
    strategies_builtin: StrategyManager
    strategies_generated: StrategyManager
    strategies_custom: StrategyManager

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

        ctx = AppContext(
            root=root,
            paths=paths,
            config=config,
            state=state,
            diagnostics=rec,
            strategies_builtin=StrategyManager(paths.strategies_builtin_dir),
            strategies_generated=StrategyManager(paths.strategies_generated_dir),
            strategies_custom=StrategyManager(paths.strategies_custom_dir)
        )
        
        # Авто-синхронизация при запуске (не блокирует старт)
        try:
            ctx.auto_sync()
        except Exception as e:
            log.warning("Auto-sync failed during bootstrap: %s", e)

        try:
            from app.zapret_manager.features.test_sets import ensure_domain_sets
            ensure_domain_sets(ctx)
        except Exception:
            # Do not crash bootstrap; UI will show status/error on start actions.
            pass
        return ctx

    def auto_sync(self) -> None:
        """Автоматически обновляет стратегии и списки из апстримов."""
        from app.zapret_manager.features.upstreams import sync_flowseal, sync_stressozz_strategies
        from app.zapret_manager.features.lists import update_exclude, update_rkn
        
        log.info("Starting background auto-sync...")
        # Обновляем стратегии
        try:
            sync_flowseal(self)
            sync_stressozz_strategies(self)
            # Перестраиваем индексы после загрузки новых файлов
            self.strategies_generated.rebuild_index()
        except Exception as e:
            log.error("Failed to sync upstreams: %s", e)
            
        # Обновляем списки
        try:
            update_exclude(self)
            if self.state.zapret.rkn_enabled:
                update_rkn(self)
        except Exception as e:
            log.error("Failed to update lists: %s", e)

