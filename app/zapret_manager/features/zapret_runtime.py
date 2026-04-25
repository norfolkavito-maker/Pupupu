from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from zapret_manager.core.app_context import AppContext
from zapret_manager.core.state import save_state
from zapret_manager.strategies.composer import compose
from zapret_manager.strategies.model import Strategy
from zapret_manager.strategies.overlays import apply_overlays
from zapret_manager.utils.platform import is_admin, is_windows
from zapret_manager.utils.subprocessx import popen_detached, run


log = logging.getLogger(__name__)


class WinwsRunner:
    """Класс для управления winws.exe процессом."""
    
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.process: Optional[subprocess.Popen] = None
        
    def check_bundle(self) -> dict:
        """Проверяет наличие zapret-win-bundle и его компонентов."""
        bundle_path = Path(self.ctx.config.zapret.bundle_path)
        winws_path = Path(self.ctx.config.zapret.winws_path)
        blockcheck_path = Path(self.ctx.config.zapret.blockcheck_path)
        
        windivert_dll = bundle_path / "WinDivert.dll"
        windivert_sys = bundle_path / "WinDivert64.sys"
        
        result = {
            "bundle_exists": bundle_path.exists(),
            "winws_exists": winws_path.exists(),
            "windivert_dll_exists": windivert_dll.exists(),
            "windivert_sys_exists": windivert_sys.exists(),
            "blockcheck_exists": blockcheck_path.exists(),
            "fake_files_dir_exists": Path(self.ctx.config.paths.fake_files_dir).exists(),
            "lists_dir_exists": Path(self.ctx.config.paths.lists_dir).exists(),
        }
        
        return result
        
    def check_admin_rights(self) -> bool:
        """Проверяет права администратора."""
        if not is_windows():
            return False
        return is_admin()
        
    def start(self, strategy: Strategy, wait_time: int = 2) -> bool:
        """Запускает winws.exe с указанной стратегией."""
        if not is_windows():
            raise RuntimeError("This action is Windows-only")
        
        if not self.check_admin_rights():
            raise RuntimeError("Нужны права администратора (запусти от имени администратора).")
            
        if not self.check_bundle()["winws_exists"]:
            raise RuntimeError("winws.exe не найден. Сначала установи zapret-win-bundle.")
            
        cmd = self._build_command(strategy)
        
        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=Path(self.ctx.config.zapret.bundle_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
                
            # Обновляем состояние
            self.ctx.state.zapret.running = True
            self.ctx.state.zapret.mode = "interactive"
            self.ctx.state.zapret.pid = self.process.pid
            self.ctx.state.zapret.selected_strategy = strategy.name
            save_state(self.ctx.paths.state_file, self.ctx.state)
            
            log.info(f"winws запущен с PID {self.process.pid}")
            time.sleep(wait_time)  # Даем время на инициализацию
            return True
            
        except Exception as e:
            log.error(f"Ошибка запуска winws: {e}")
            return False
            
    def stop(self) -> bool:
        """Останавливает winws.exe."""
        if not is_windows():
            raise RuntimeError("This action is Windows-only")
            
        pid = self.ctx.state.zapret.pid
        if not pid:
            log.info("winws не запущен")
            return True
            
        try:
            # Останавливаем процесс
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], 
                          check=False, capture_output=True)
            
            # Закрываем процесс, если он еще жив
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=5)
                
            # Обновляем состояние
            self.ctx.state.zapret.running = False
            self.ctx.state.zapret.pid = None
            save_state(self.ctx.paths.state_file, self.ctx.state)
            
            log.info("winws остановлен")
            return True
            
        except Exception as e:
            log.error(f"Ошибка остановки winws: {e}")
            return False
            
    def restart(self, strategy: Strategy) -> bool:
        """Перезапускает winws.exe."""
        log.info("Перезапуск winws...")
        self.stop()
        time.sleep(1)
        return self.start(strategy)
        
    def get_status(self) -> dict:
        """Получает текущий статус winws."""
        pid = self.ctx.state.zapret.pid
        running = False
        
        if pid:
            try:
                # Проверяем, существует ли процесс
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV"],
                    capture_output=True, text=True
                )
                running = "winws.exe" in result.stdout
            except Exception:
                running = False
                
        return {
            "running": running,
            "pid": pid,
            "active_strategy": self.ctx.state.zapret.selected_strategy,
            "admin": self.check_admin_rights()
        }
        
    def _build_command(self, strategy: Strategy) -> list[str]:
        """Строит команду запуска для winws с учётом compose/оверлеев."""
        winws_path = self.ctx.config.zapret.winws_path
        lists_dir = self.ctx.config.paths.lists_dir
        fake_files_dir = self.ctx.config.paths.fake_files_dir
        
        state = self.ctx.state.zapret
        # Если есть активные слои/оверлеи — используем compose
        if (
            state.youtube_layer
            or state.discord_layer
            or state.discord_script
            or state.games_profile
            or state.rkn_enabled
            or state.wssize_enabled
        ):
            from zapret_manager.features.selection import find_strategy
            from zapret_manager.strategies.composer import compose
            
            youtube = find_strategy(self.ctx, state.youtube_layer, kind="youtube") if state.youtube_layer else None
            discord = find_strategy(self.ctx, state.discord_layer, kind="discord") if state.discord_layer else None
            
            composed = compose(
                base=strategy,
                youtube=youtube,
                discord=discord,
                discord_script=state.discord_script,
                games_profile=state.games_profile,
                rkn_enabled=state.rkn_enabled,
                wssize_enabled=state.wssize_enabled,
            )
            args = composed.args
        else:
            args = apply_overlays(
                strategy.args,
                discord_profile=state.discord_profile,
                games_profile=state.games_profile,
            )
        
        # Заменяем пути
        resolved_args = []
        for arg in args:
            arg = arg.replace("{BIN}", os.path.dirname(winws_path) + "\\")
            arg = arg.replace("{LISTS}", lists_dir + "\\")
            arg = arg.replace("{FAKE}", fake_files_dir + "\\")
            resolved_args.append(arg)
            
        return [winws_path] + resolved_args
        
    def get_start_command(self, strategy: Strategy) -> str:
        """Возвращает строку команды запуска для отображения."""
        cmd = self._build_command(strategy)
        return " ".join(cmd)


def _runtime_root(ctx: AppContext) -> Path:
    # runtime_dir from config is relative to root
    return (ctx.root / ctx.config.zapret.runtime_dir).resolve()


def detect_runtime_files(ctx: AppContext) -> None:
    rt = _runtime_root(ctx)
    winws = _find_first(rt, ["winws.exe"])
    winws2 = _find_first(rt, ["winws2.exe"])
    ctx.state.runtime.installed = bool(winws)
    ctx.state.runtime.runtime_path = str(rt)
    ctx.state.runtime.winws_path = str(winws or "")
    ctx.state.runtime.winws2_path = str(winws2 or "")
    save_state(ctx.paths.state_file, ctx.state)


def uninstall_runtime(ctx: AppContext) -> None:
    rt = _runtime_root(ctx)
    if rt.exists():
        shutil.rmtree(rt)
    ctx.state.runtime.installed = False
    ctx.state.runtime.runtime_path = str(rt)
    ctx.state.runtime.winws_path = ""
    ctx.state.runtime.winws2_path = ""
    save_state(ctx.paths.state_file, ctx.state)


def build_command(
    ctx: AppContext,
    strategy: Strategy,
    *,
    args_override: list[str] | None = None,
    engine_override: str | None = None,
) -> list[str]:
    rt = _runtime_root(ctx)
    winws = Path(ctx.state.runtime.winws_path) if ctx.state.runtime.winws_path else None
    winws2 = Path(ctx.state.runtime.winws2_path) if ctx.state.runtime.winws2_path else None

    engine = engine_override or strategy.engine

    if engine == "winws2":
        exe = winws2 or _find_first(rt, ["winws2.exe"])
        if not exe:
            raise RuntimeError("winws2.exe not found in runtime")
    else:
        exe = winws or _find_first(rt, ["winws.exe"])
        if not exe:
            raise RuntimeError("winws.exe not found in runtime")

    args = list(args_override) if args_override is not None else apply_overlays(
        strategy.args,
        discord_profile=ctx.state.zapret.discord_profile,
        games_profile=ctx.state.zapret.games_profile,
    )

    resolved: list[str] = []
    for a in args:
        a = a.replace("{BIN}", str(exe.parent) + "\\")
        # {LISTS} -> runtime-provided lists (usually runtime/zapret/lists)
        a = a.replace("{LISTS}", str(Path(ctx.config.paths.lists_dir).resolve()) + "\\")
        # {MGR_LISTS} -> manager-owned lists (data/lists)
        a = a.replace("{MGR_LISTS}", str(ctx.paths.lists_dir.resolve()) + "\\")
        # Support both {FAKE:filename.bin} and legacy {FAKE} prefix.
        a = a.replace("{FAKE}", str(Path(ctx.config.paths.fake_files_dir).resolve()) + "\\")
        a = _resolve_fake(ctx, a)
        resolved.append(a)
    return [str(exe)] + resolved


def start_zapret_interactive(
    ctx: AppContext,
    strategy: Strategy,
    youtube: Strategy | None = None,
    discord: Strategy | None = None,
) -> list[str]:
    if not is_windows():
        raise RuntimeError("This action is Windows-only")
    if not is_admin():
        raise RuntimeError("Нужны права администратора (запусти от имени администратора).")

    detect_runtime_files(ctx)
    if not ctx.state.runtime.installed:
        raise RuntimeError("Runtime не установлен. Сначала установи Zapret (пункт 1).")

    warnings: list[str] = []
    args_override: list[str] | None = None
    engine_override: str | None = None
    if (
        youtube
        or discord
        or ctx.state.zapret.discord_script
        or ctx.state.zapret.games_profile
        or ctx.state.zapret.rkn_enabled
        or ctx.state.zapret.wssize_enabled
    ):
        composed = compose(
            base=strategy,
            youtube=youtube,
            discord=discord,
            discord_script=ctx.state.zapret.discord_script,
            games_profile=ctx.state.zapret.games_profile,
            rkn_enabled=ctx.state.zapret.rkn_enabled,
            wssize_enabled=ctx.state.zapret.wssize_enabled,
        )
        args_override = composed.args
        engine_override = composed.engine
        warnings = list(composed.warnings)

    cmd = build_command(ctx, strategy, args_override=args_override, engine_override=engine_override)
    p = popen_detached(cmd, cwd=str(_runtime_root(ctx)))
    ctx.state.zapret.running = True
    ctx.state.zapret.mode = "interactive"
    ctx.state.zapret.pid = int(p.pid)
    ctx.state.zapret.selected_strategy = strategy.name
    save_state(ctx.paths.state_file, ctx.state)
    return warnings


def stop_zapret(ctx: AppContext) -> None:
    if not is_windows():
        raise RuntimeError("This action is Windows-only")
    pid = ctx.state.zapret.pid
    if not pid:
        return
    run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False, capture=True)
    ctx.state.zapret.running = False
    ctx.state.zapret.pid = None
    save_state(ctx.paths.state_file, ctx.state)


def _find_first(root: Path, names: list[str]) -> Path | None:
    for name in names:
        for p in root.rglob(name):
            if p.is_file():
                return p
    return None


def _resolve_fake(ctx: AppContext, token: str) -> str:
    # token may include {FAKE:filename.bin}
    if "{FAKE:" not in token:
        return token
    rt = _runtime_root(ctx)
    import re

    def repl(m: re.Match[str]) -> str:
        fname = m.group(1)
        found = _find_first(rt, [fname])
        return str(found) if found else fname

    return re.sub(r"\{FAKE:([^}]+)\}", repl, token)