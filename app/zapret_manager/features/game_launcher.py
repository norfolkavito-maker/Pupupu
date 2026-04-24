from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path

from zapret_manager.core.app_context import AppContext
from zapret_manager.core.config import GameLauncherProfile
from zapret_manager.core.state import save_state
from zapret_manager.features.selection import find_strategy
from zapret_manager.features.zapret_runtime import start_zapret_interactive, stop_zapret


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

    # Получаем полные аргументы
    args = strategy.get_full_args()

    # Заменяем плейсхолдеры путей (как в zapret_runtime._build_command)
    winws_path = ctx.config.zapret.winws_path
    lists_dir = ctx.config.paths.lists_dir
    fake_files_dir = ctx.config.paths.fake_files_dir
    resolved_args = []
    for arg in args:
        arg = arg.replace("{LISTS}", lists_dir)
        arg = arg.replace("{FAKE}", fake_files_dir)
        resolved_args.append(arg)

    cmd = f'"{winws_path}" ' + " ".join(f'"{a}"' if " " in a else a for a in resolved_args)

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
