from __future__ import annotations

"""Process watcher (optional).

This module is currently experimental and **must not** be imported by default
because it depends on optional third-party packages (psutil).

If you want to use it, install optional dependencies and import explicitly.
"""

import logging
import threading
import time
from typing import Set

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.features.zapret_runtime import start_zapret_interactive, stop_zapret


log = logging.getLogger(__name__)


class ProcessWatcher:
    """Следит за запущенными процессами и включает/выключает Zapret."""

    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self._running = False
        self._thread: threading.Thread | None = None
        self._targets: Set[str] = set()
        self._check_interval = 5  # секунд

    def start(self):
        """Запускает поток мониторинга."""
        if self._running:
            return
        
        # Загружаем цели из конфига или состояния
        self._targets = set(getattr(self.ctx.state.zapret, "watcher_targets", []))
        if not self._targets:
            log.info("ProcessWatcher: список целей пуст, мониторинг не имеет смысла.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="ProcessWatcher")
        self._thread.start()
        log.info("ProcessWatcher запущен. Цели: %s", self._targets)

    def stop(self):
        """Останавливает мониторинг."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        log.info("ProcessWatcher остановлен.")

    def _run(self):
        while self._running:
            try:
                target_found = self._check_processes()
                is_active = self.ctx.state.zapret.running
                
                if target_found and not is_active:
                    log.info("ProcessWatcher: Обнаружен целевой процесс. Запуск Zapret...")
                    self._start_bypass()
                elif not target_found and is_active:
                    # Опционально: выключать ли, если процесс закрыт? 
                    # Пользователь обычно хочет, чтобы выключалось.
                    log.info("ProcessWatcher: Целевые процессы не найдены. Остановка Zapret...")
                    stop_zapret(self.ctx)

            except Exception as e:
                log.error("Ошибка в ProcessWatcher: %s", e)
            
            time.sleep(self._check_interval)

    def _check_processes(self) -> bool:
        """Проверяет, запущен ли хоть один процесс из списка целей."""
        try:
            import psutil  # optional
        except Exception:
            log.warning("psutil is not installed; ProcessWatcher is disabled")
            return False
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name'].lower()
                if name in self._targets:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def _start_bypass(self):
        # We avoid importing UI modules here; watcher should be UI-independent.
        # Use selection logic from zapret_runtime (keeps behavior consistent).
        from app.zapret_manager.features.zapret_runtime import _load_selected_strategy

        st = _load_selected_strategy(self.ctx)
        if st:
            try:
                # В фоновом режиме используем неинтерактивный старт, если возможно,
                # или просто вызываем базовую функцию старта.
                start_zapret_interactive(self.ctx, st)
            except Exception as e:
                log.error("ProcessWatcher не смог запустить Zapret: %s", e)
        else:
            log.warning("ProcessWatcher: Стратегия не выбрана, запуск невозможен.")
