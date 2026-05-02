from __future__ import annotations

"""Tray icon (optional).

This module is experimental and depends on optional packages: pystray + Pillow.
It must not be imported by default.

If you want to use it:
  pip install pystray pillow
"""

import logging
import threading
from pathlib import Path

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.features.zapret_runtime import stop_zapret, start_zapret_interactive


log = logging.getLogger(__name__)


# NOTE: pystray is an optional dependency.
# Use a forward reference for typing to avoid NameError at import time.
try:
    import pystray as _pystray  # type: ignore

    _PyStrayIcon = _pystray.Icon
except Exception:  # pragma: no cover
    _PyStrayIcon = object


class TrayIcon:
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.icon: _PyStrayIcon | None = None
        self._thread: threading.Thread | None = None

    def _create_image(self):
        # Lazy imports to keep dependencies optional.
        from PIL import Image

        # Пытаемся загрузить иконку из ресурсов, если нет - создаем заглушку
        icon_path = self.ctx.root / "data" / "icon.png"
        if icon_path.exists():
            return Image.open(icon_path)
        else:
            # Создаем простую иконку 64x64
            image = Image.new('RGB', (64, 64), color=(0, 120, 215))
            return image

    def _on_exit(self, icon, item):
        log.info("Tray: Выход через трей")
        stop_zapret(self.ctx)
        icon.stop()

    def _on_toggle(self, icon, item):
        zap = self.ctx.state.zapret
        if zap.running:
            stop_zapret(self.ctx)
            log.info("Tray: Zapret остановлен")
        else:
            # Avoid importing UI here.
            from app.zapret_manager.features.zapret_runtime import _load_selected_strategy

            st = _load_selected_strategy(self.ctx)
            if st:
                try:
                    start_zapret_interactive(self.ctx, st)
                    log.info("Tray: Zapret запущен")
                except Exception as e:
                    log.error("Tray: Ошибка запуска: %s", e)
            else:
                log.warning("Tray: Стратегия не выбрана")

    def run(self):
        """Запускает иконку в трее."""
        # Lazy import: optional dependency
        import pystray

        menu = pystray.Menu(
            pystray.MenuItem("Включить/Выключить", self._on_toggle),
            pystray.MenuItem("Выход", self._on_exit)
        )
        
        self.icon = pystray.Icon(
            "DedZapret",
            self._create_image(),
            "DedZapret Manager",
            menu=menu
        )
        
        # Запускаем в отдельном потоке, так как icon.run() блокирует выполнение
        self._thread = threading.Thread(target=self.icon.run, daemon=True, name="TrayThread")
        self._thread.start()
        log.info("Tray иконка запущена")

    def update_status(self):
        """Обновляет текст подсказки при наведении."""
        if self.icon:
            zap = self.ctx.state.zapret
            status = "РАБОТАЕТ" if zap.running else "ОСТАНОВЛЕН"
            st_name = zap.selected_strategy or "нет"
            self.icon.title = f"DedZapret: {status}\nСтратегия: {st_name}"
