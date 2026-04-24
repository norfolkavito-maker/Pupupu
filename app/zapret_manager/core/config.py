from __future__ import annotations

from dataclasses import dataclass, field
import shutil
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class UpdatesConfig:
    check_on_start: bool = True
    apply_mode: str = "ask"  # ask|auto|manual


@dataclass(frozen=True)
class AppSection:
    language: str = "ru"
    updates: UpdatesConfig = field(default_factory=UpdatesConfig)


@dataclass(frozen=True)
class ZapretSection:
    mode: str = "interactive"  # interactive|task
    service_name: str = "ZapretManagerAutostart"
    runtime_dir: str = "data/runtime/zapret"
    selected_strategy: str = ""
    discord_profile: str = ""
    games_profile: str = ""
    bundle_path: str = ".\\zapret-win-bundle"
    winws_path: str = ".\\zapret-win-bundle\\winws.exe"
    blockcheck_path: str = ".\\zapret-win-bundle\\blockcheck\\blockcheck.cmd"
    active_strategy: str = "v7"
    run_mode: str = "process"
    autostart: bool = False
    require_admin: bool = True


@dataclass(frozen=True)
class PathsSection:
    hosts_file: str = r"C:\Windows\System32\drivers\etc\hosts"
    fake_files_dir: str = ".\\zapret-win-bundle\\files\\fake"
    lists_dir: str = ".\\data\\lists"
    strategies_dir: str = ".\\data\\strategies"
    logs_dir: str = ".\\data\\logs"
    backup_dir: str = ".\\data\\backup"


@dataclass(frozen=True)
class NetworkSection:
    adapter_name: str = ""
    flush_dns_after_hosts_change: bool = True
    enable_tcp_timestamps_if_needed: bool = False


@dataclass(frozen=True)
class GameLauncherSection:
    enabled: bool = True
    auto_stop_zapret_on_game_exit: bool = True


@dataclass(frozen=True)
class DoHSection:
    enabled: bool = False
    profile: str = "default"
    listen_addr: str = "127.0.0.1"
    listen_port: int = 5053


@dataclass(frozen=True)
class AppConfig:
    app: AppSection = field(default_factory=AppSection)
    zapret: ZapretSection = field(default_factory=ZapretSection)
    paths: PathsSection = field(default_factory=PathsSection)
    network: NetworkSection = field(default_factory=NetworkSection)
    game_launcher: GameLauncherSection = field(default_factory=GameLauncherSection)
    doh: DoHSection = field(default_factory=DoHSection)


def _get(d: dict[str, Any], path: list[str], default: Any) -> Any:
    cur: Any = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        return AppConfig()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        broken = path.with_suffix(path.suffix + ".broken")
        shutil.move(str(path), str(broken))
        return AppConfig()

    updates = UpdatesConfig(
        check_on_start=bool(_get(data, ["app", "updates", "check_on_start"], True)),
        apply_mode=str(_get(data, ["app", "updates", "apply_mode"], "ask")),
    )
    app = AppSection(
        language=str(_get(data, ["app", "language"], "ru")),
        updates=updates,
    )
    zapret = ZapretSection(
        mode=str(_get(data, ["zapret", "mode"], "interactive")),
        service_name=str(_get(data, ["zapret", "service_name"], "ZapretManagerAutostart")),
        runtime_dir=str(_get(data, ["zapret", "runtime_dir"], "data/runtime/zapret")),
        selected_strategy=str(_get(data, ["zapret", "selected_strategy"], "")),
        discord_profile=str(_get(data, ["zapret", "discord_profile"], "")),
        games_profile=str(_get(data, ["zapret", "games_profile"], "")),
        bundle_path=str(_get(data, ["zapret", "bundle_path"], ".\\zapret-win-bundle")),
        winws_path=str(_get(data, ["zapret", "winws_path"], ".\\zapret-win-bundle\\winws.exe")),
        blockcheck_path=str(
            _get(data, ["zapret", "blockcheck_path"], ".\\zapret-win-bundle\\blockcheck\\blockcheck.cmd")
        ),
        active_strategy=str(_get(data, ["zapret", "active_strategy"], "v7")),
        run_mode=str(_get(data, ["zapret", "run_mode"], "process")),
        autostart=bool(_get(data, ["zapret", "autostart"], False)),
        require_admin=bool(_get(data, ["zapret", "require_admin"], True)),
    )
    paths = PathsSection(
        hosts_file=str(_get(data, ["paths", "hosts_file"], r"C:\Windows\System32\drivers\etc\hosts")),
        fake_files_dir=str(_get(data, ["paths", "fake_files_dir"], ".\\zapret-win-bundle\\files\\fake")),
        lists_dir=str(_get(data, ["paths", "lists_dir"], ".\\data\\lists")),
        strategies_dir=str(_get(data, ["paths", "strategies_dir"], ".\\data\\strategies")),
        logs_dir=str(_get(data, ["paths", "logs_dir"], ".\\data\\logs")),
        backup_dir=str(_get(data, ["paths", "backup_dir"], ".\\data\\backup")),
    )
    network = NetworkSection(
        adapter_name=str(_get(data, ["network", "adapter_name"], "")),
        flush_dns_after_hosts_change=bool(_get(data, ["network", "flush_dns_after_hosts_change"], True)),
        enable_tcp_timestamps_if_needed=bool(_get(data, ["network", "enable_tcp_timestamps_if_needed"], False)),
    )
    game_launcher = GameLauncherSection(
        enabled=bool(_get(data, ["game_launcher", "enabled"], True)),
        auto_stop_zapret_on_game_exit=bool(
            _get(data, ["game_launcher", "auto_stop_zapret_on_game_exit"], True)
        ),
    )
    doh = DoHSection(
        enabled=bool(_get(data, ["doh", "enabled"], False)),
        profile=str(_get(data, ["doh", "profile"], "default")),
        listen_addr=str(_get(data, ["doh", "listen_addr"], "127.0.0.1")),
        listen_port=int(_get(data, ["doh", "listen_port"], 5053)),
    )
    return AppConfig(app=app, zapret=zapret, paths=paths, network=network, game_launcher=game_launcher, doh=doh)

