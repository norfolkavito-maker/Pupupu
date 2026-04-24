from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass(frozen=True)
class Strategy:
    name: str
    engine: str  # winws|winws2|bat
    args: list[str]
    source_file: str = ""
    upstream: str = ""
    kind: str = "base"
    winws_params: List[str] = field(default_factory=list)
    discord_profile: Optional[str] = None
    games_profile: Optional[str] = None
    hostlist_exclude: List[str] = field(default_factory=list)
    wssize: Optional[str] = None  # "1:6"

    @staticmethod
    def from_json(data: dict[str, Any]) -> "Strategy":
        return Strategy(
            name=str(data["name"]),
            engine=str(data.get("engine", "winws")),
            args=[str(x) for x in (data.get("args") or [])],
            source_file=str(data.get("source_file", "")),
            upstream=str(data.get("upstream", "")),
            kind=str(data.get("kind", "base")),
            winws_params=[str(x) for x in (data.get("winws_params") or [])],
            discord_profile=str(data.get("discord_profile", "")) if data.get("discord_profile") else None,
            games_profile=str(data.get("games_profile", "")) if data.get("games_profile") else None,
            hostlist_exclude=[str(x) for x in (data.get("hostlist_exclude") or [])],
            wssize=str(data.get("wssize", "")) if data.get("wssize") else None,
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "engine": self.engine,
            "args": self.args,
            "source_file": self.source_file,
            "upstream": self.upstream,
            "kind": self.kind,
            "winws_params": self.winws_params,
            "discord_profile": self.discord_profile,
            "games_profile": self.games_profile,
            "hostlist_exclude": self.hostlist_exclude,
            "wssize": self.wssize,
        }

    def get_full_args(self) -> List[str]:
        """Возвращает полный список аргументов с учетом winws_params и wssize."""
        full_args = self.args.copy()
        # Добавляем winws_params
        full_args.extend(self.winws_params)
        # Добавляем wssize блок, если указан
        if self.wssize:
            full_args.extend(["--new", "--filter-tcp=443", "--wssize", self.wssize])
        return full_args
