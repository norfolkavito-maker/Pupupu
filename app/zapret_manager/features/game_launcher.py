from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.config import GameLauncherProfile
from app.zapret_manager.features.selection import find_strategy
from app.zapret_manager.features.zapret_runtime import start_zapret_interactive, stop_zapret


log = logging.getLogger(__name__)


def list_profiles(ctx: AppContext) -> list[GameLauncherProfile]:
    return list(ctx.config.game_launcher.program_profiles)


def add_profile(ctx: AppContext, name: str, exe_path: str, strategy_name: str) -> None:
    profiles = list(ctx.config.game_launcher.program_profiles)
    profiles.append(
        GameLauncherProfile(
            name=name,
            exe_path=exe_path,
            strategy_name=strategy_name,
        )
    )
    _save_profiles(ctx, profiles)


def remove_profile(ctx: AppContext, name: str) -> None:
    profiles = [p for p in ctx.config.game_launcher.program_profiles if p.name != name]
    _save_profiles(ctx, profiles)


def _save_profiles(ctx: AppContext, profiles: list[GameLauncherProfile]) -> None:
    import yaml

    config_path = ctx.paths.config_file
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    data.setdefault("game_launcher", {})
    data["game_launcher"]["program_profiles"] = [
        {"name": p.name, "exe_path": p.exe_path, "strategy_name": p.strategy_name}
        for p in profiles
    ]
    config_path.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def run_profile(ctx: AppContext, profile: GameLauncherProfile) -> None:
    if not Path(profile.exe_path).exists():
        raise RuntimeError(f"Исполняемый файл не найден: {profile.exe_path}")

    strategy = find_strategy(ctx, profile.strategy_name, kind="base")
    if not strategy:
        strategy = find_strategy(ctx, profile.strategy_name)
    if not strategy:
        raise RuntimeError(f"Стратегия не найдена: {profile.strategy_name}")

    # Старт winws
    stop_zapret(ctx)
    time.sleep(0.5)
    warnings = start_zapret_interactive(ctx, strategy)
    for w in warnings:
        log.warning(w)

    # Запуск игры
    log.info("Запуск %s (strategy=%s)", profile.exe_path, profile.strategy_name)
    proc = subprocess.Popen([profile.exe_path])

    # Мониторинг и автоостановка
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
    finally:
        if ctx.config.game_launcher.auto_stop_zapret_on_game_exit:
            stop_zapret(ctx)
            log.info("winws остановлен после выхода из игры")


def generate_bat(ctx: AppContext, profile: GameLauncherProfile, output_path: Path) -> Path:
    """Генерирует .bat лаунчер для запуска игры с winws (с полными аргументами)."""
    strategy = find_strategy(ctx, profile.strategy_name, kind="base")
    if not strategy:
        strategy = find_strategy(ctx, profile.strategy_name)
    if not strategy:
        raise RuntimeError(f"Стратегия не найдена: {profile.strategy_name}")

    # Prefer using the same command builder as interactive mode.
    # But allow a minimal context (used by unit tests) where runtime paths/state
    # may be absent.
    from app.zapret_manager.features.zapret_runtime import build_command

    try:
        cmd_list = build_command(ctx, strategy)
    except Exception as e:  # pragma: no cover (fallback path for minimal ctx)
        log.debug("generate_bat: build_command failed, using fallback: %s", e)

        exe = "winws.exe"
        # Try to discover executable path from ctx if present.
        if hasattr(ctx, "state") and getattr(ctx, "state", None):
            rt = getattr(ctx.state, "runtime", None)
            if rt and getattr(rt, "winws_path", None):
                exe = str(rt.winws_path)
        if exe == "winws.exe" and hasattr(ctx, "config") and getattr(ctx, "config", None):
            zap = getattr(ctx.config, "zapret", None)
            if zap and getattr(zap, "winws_path", None):
                exe = str(zap.winws_path)

        args = strategy.get_full_args() if hasattr(strategy, "get_full_args") else list(strategy.args)
        cmd_list = [exe] + args
    cmd = " ".join(f'"{x}"' if " " in x else x for x in cmd_list)

    bat_lines = [
        "@echo off",
        "chcp 65001 > nul",
        f'cd /d "{ctx.root}"',
        "",
        f"{cmd}",
        f'start "" "{profile.exe_path}"',
        "",
        "REM Ожидание завершения игры и остановка winws",
        f':loop',
        f'timeout /t 2 /nobreak >nul',
        f'tasklist /fi "imagename eq {Path(profile.exe_path).name}" 2>nul | find /i "{Path(profile.exe_path).name}" >nul',
        f'if errorlevel 1 goto endloop',
        f'goto loop',
        f':endloop',
        f'taskkill /f /im winws.exe >nul 2>&1',
        "exit",
    ]
    output_path.write_text("\n".join(bat_lines), encoding="utf-8")
    return output_path


def generate_shortcut(ctx: AppContext, profile: GameLauncherProfile, shortcut_path: Path) -> None:
    """Генерирует .lnk ярлык через PowerShell."""
    bat_path = shortcut_path.with_suffix(".bat")
    generate_bat(ctx, profile, bat_path)
    ps = (
        f'$WshShell = New-Object -comObject WScript.Shell; '
        f'$Shortcut = $WshShell.CreateShortcut("{shortcut_path}"); '
        f'$Shortcut.TargetPath = "{bat_path}"; '
        f'$Shortcut.WorkingDirectory = "{ctx.root}"; '
        f'$Shortcut.Save()'
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=False, capture_output=True)
