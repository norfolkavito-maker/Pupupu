from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class UpstreamState:
    etag: str | None = None
    last_modified: str | None = None
    synced_at_utc: str | None = None


@dataclass
class RuntimeState:
    installed: bool = False
    runtime_path: str = ""
    winws_path: str = ""
    winws2_path: str = ""


@dataclass
class ZapretRunState:
    running: bool = False
    mode: str = "interactive"
    pid: int | None = None
    base_strategy: str = ""
    selected_strategy: str = ""
    youtube_layer: str = ""
    discord_layer: str = ""
    discord_script: str = ""
    discord_profile: str = ""
    games_profile: str = ""
    rkn_enabled: bool = False
    wssize_enabled: bool = False


@dataclass
class HostsState:
    blocks: dict[str, bool] = field(default_factory=dict)


@dataclass
class DoHRunState:
    enabled: bool = False
    profile: str = "default"
    pid: int | None = None
    prev_dns: dict[str, Any] = field(default_factory=dict)


@dataclass
class AppState:
    upstreams: dict[str, UpstreamState] = field(default_factory=dict)
    runtime: RuntimeState = field(default_factory=RuntimeState)
    zapret: ZapretRunState = field(default_factory=ZapretRunState)
    doh: DoHRunState = field(default_factory=DoHRunState)
    hosts: HostsState = field(default_factory=HostsState)
    tg: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        def asdict_up(u: UpstreamState) -> dict[str, Any]:
            return {
                "etag": u.etag,
                "last_modified": u.last_modified,
                "synced_at_utc": u.synced_at_utc,
            }

        return {
            "upstreams": {k: asdict_up(v) for k, v in self.upstreams.items()},
            "runtime": {
                "installed": self.runtime.installed,
                "runtime_path": self.runtime.runtime_path,
                "winws_path": self.runtime.winws_path,
                "winws2_path": self.runtime.winws2_path,
            },
            "zapret": {
                "running": self.zapret.running,
                "mode": self.zapret.mode,
                "pid": self.zapret.pid,
                "base_strategy": self.zapret.base_strategy,
                "selected_strategy": self.zapret.selected_strategy,
                "youtube_layer": self.zapret.youtube_layer,
                "discord_layer": self.zapret.discord_layer,
                "discord_script": self.zapret.discord_script,
                "discord_profile": self.zapret.discord_profile,
                "games_profile": self.zapret.games_profile,
                "rkn_enabled": self.zapret.rkn_enabled,
                "wssize_enabled": self.zapret.wssize_enabled,
            },
            "doh": {
                "enabled": self.doh.enabled,
                "profile": self.doh.profile,
                "pid": self.doh.pid,
                "prev_dns": self.doh.prev_dns,
            },
            "hosts": {
                "blocks": self.hosts.blocks,
            },
            "tg": self.tg,
        }


def load_state(path: Path) -> AppState:
    if not path.exists():
        st = AppState()
        save_state(path, st)
        return st

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        broken = path.with_suffix(path.suffix + ".broken")
        shutil.move(str(path), str(broken))
        st = AppState()
        save_state(path, st)
        return st
    st = AppState()

    ups = data.get("upstreams", {}) or {}
    for name, u in ups.items():
        st.upstreams[name] = UpstreamState(
            etag=u.get("etag"),
            last_modified=u.get("last_modified"),
            synced_at_utc=u.get("synced_at_utc"),
        )

    rt = data.get("runtime", {}) or {}
    st.runtime = RuntimeState(
        installed=bool(rt.get("installed", False)),
        runtime_path=str(rt.get("runtime_path", "")),
        winws_path=str(rt.get("winws_path", "")),
        winws2_path=str(rt.get("winws2_path", "")),
    )

    z = data.get("zapret", {}) or {}
    st.zapret = ZapretRunState(
        running=bool(z.get("running", False)),
        mode=str(z.get("mode", "interactive")),
        pid=z.get("pid"),
        base_strategy=str(z.get("base_strategy", "")),
        selected_strategy=str(z.get("selected_strategy", "")),
        youtube_layer=str(z.get("youtube_layer", "")),
        discord_layer=str(z.get("discord_layer", "")),
        discord_script=str(z.get("discord_script", "")),
        discord_profile=str(z.get("discord_profile", "")),
        games_profile=str(z.get("games_profile", "")),
        rkn_enabled=bool(z.get("rkn_enabled", False)),
        wssize_enabled=bool(z.get("wssize_enabled", False)),
    )

    d = data.get("doh", {}) or {}
    st.doh = DoHRunState(
        enabled=bool(d.get("enabled", False)),
        profile=str(d.get("profile", "default")),
        pid=d.get("pid"),
        prev_dns=d.get("prev_dns", {}) or {},
    )

    h = data.get("hosts", {}) or {}
    st.hosts = HostsState(blocks=h.get("blocks", {}) or {})

    st.tg = data.get("tg", {}) or {}

    return st


def save_state(path: Path, state: AppState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_json(), ensure_ascii=False, indent=2), encoding="utf-8")