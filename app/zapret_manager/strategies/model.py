from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional


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
            wssize_args = self._build_wssize_block(self.wssize)
            full_args.extend(wssize_args)
            
        return full_args
        
    def _build_wssize_block(self, wssize_value: str) -> List[str]:
        """Строит блок аргументов для --wssize."""
        # Пример: "1:6" -> ["--wssize", "1:6", "--wssize-max", "6"]
        parts = wssize_value.split(":")
        if len(parts) == 2:
            min_size, max_size = parts[0], parts[1]
            return [
                "--wssize", wssize_value,
                "--wssize-max", max_size
            ]
        return ["--wssize", wssize_value]


@dataclass
class BuiltinStrategy:
    """Встроенная стратегия."""
    name: str
    title: str
    engine: str = "winws"
    args: List[str] = field(default_factory=list)
    winws_params: List[str] = field(default_factory=list)
    description: str = ""
    category: str = "general"  # general, game, discord, youtube, etc.


@dataclass
class GameStrategy:
    """Игровая стратегия."""
    name: str
    title: str
    fake_files: List[str] = field(default_factory=list)
    udp_ports: List[int] = field(default_factory=list)
    tcp_ports: List[int] = field(default_factory=list)
    dpi_desync_params: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class DiscordStrategy:
    """Discord стратегия."""
    name: str
    title: str
    block_types: List[str] = field(default_factory=list)
    finnish_ips: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class YouTubeStrategy:
    """YouTube стратегия."""
    name: str
    title: str
    list_types: List[str] = field(default_factory=list)
    description: str = ""


class StrategyFactory:
    """Фабрика для создания стратегий."""
    
    @staticmethod
    def create_builtin_strategy(name: str, **kwargs) -> Strategy:
        """Создает встроенную стратегию."""
        strategy_data = StrategyFactory.get_builtin_strategy_data(name)
        if not strategy_data:
            raise ValueError(f"Unknown builtin strategy: {name}")
            
        return Strategy(
            name=name,
            engine=strategy_data["engine"],
            args=strategy_data["args"],
            kind="base",
            winws_params=strategy_data.get("winws_params", []),
            **kwargs
        )
        
    @staticmethod
    def get_builtin_strategy_data(name: str) -> Optional[Dict[str, Any]]:
        """Возвращает данные для встроенной стратегии."""
        strategies = {
            "v1": {
                "engine": "winws",
                "args": ["--wf-tcp=80,443", "--wf-udp=53,443"],
                "winws_params": ["--hostlist-exclude", "localhost", "127.0.0.1"],
                "description": "Базовая стратегия (TCP 80,443, UDP 53,443)"
            },
            "v2": {
                "engine": "winws",
                "args": ["--wf-tcp=80,443,8080", "--wf-udp=53,443,5353"],
                "winws_params": ["--hostlist-exclude", "localhost", "127.0.0.1"],
                "description": "Расширенная стратегия (больше портов)"
            },
            "v3": {
                "engine": "winws",
                "args": ["--wf-tcp=80,443,8080,8443", "--wf-udp=53,443,5353,1900"],
                "winws_params": ["--hostlist-exclude", "localhost", "127.0.0.1"],
                "description": "Максимальная стратегия (максимум портов)"
            },
            "v4": {
                "engine": "winws",
                "args": ["--wf-tcp=80,443", "--wf-udp=53,443", "--dpi-desync=fake", "--dpi-desync-tls=fake"],
                "winws_params": ["--hostlist-exclude", "localhost", "127.0.0.1"],
                "description": "Стратегия с fake-файлами"
            },
            "v5": {
                "engine": "winws",
                "args": ["--wf-tcp=80,443,8080", "--wf-udp=53,443,5353", "--dpi-desync=fake"],
                "winws_params": ["--hostlist-exclude", "localhost", "127.0.0.1"],
                "description": "Стратегия с fake-файлами и дополнительными портами"
            },
            "v6": {
                "engine": "winws",
                "args": ["--wf-tcp=80,443,8080,8443", "--wf-udp=53,443,5353,1900", "--dpi-desync=fake"],
                "winws_params": ["--hostlist-exclude", "localhost", "127.0.0.1"],
                "description": "Максимальная стратегия с fake-файлами"
            },
            "v7": {
                "engine": "winws",
                "args": ["--wf-tcp=80,443,8080,8443", "--wf-udp=53,443,5353,1900", "--dpi-desync=fake", "--dpi-desync-tls=fake"],
                "winws_params": ["--hostlist-exclude", "localhost", "127.0.0.1"],
                "description": "Комплексная стратегия (все включено)"
            },
            "v8": {
                "engine": "winws",
                "args": ["--wf-tcp=80,443", "--wf-udp=53,443", "--hostlist", "rkn-list.txt"],
                "winws_params": ["--hostlist-exclude", "localhost", "127.0.0.1"],
                "description": "Стратегия с RKN списком"
            },
            "v9": {
                "engine": "winws",
                "args": ["--wf-tcp=80,443,8080", "--wf-udp=53,443,5353", "--hostlist", "rkn-list.txt"],
                "winws_params": ["--hostlist-exclude", "localhost", "127.0.0.1"],
                "description": "Расширенная стратегия с RKN списком"
            }
        }
        
        return strategies.get(name)
        
    @staticmethod
    def create_game_strategy(name: str, **kwargs) -> Strategy:
        """Создает игровую стратегию."""
        game_data = StrategyFactory.get_game_strategy_data(name)
        if not game_data:
            raise ValueError(f"Unknown game strategy: {name}")
            
        # Добавляем fake-файлы в аргументы
        args = list(game_data.get("args", []))
        fake_files = game_data.get("fake_files", [])
        for fake_file in fake_files:
            args.append(f"--fake={fake_file}")
            
        # Добавляем порты
        if game_data.get("udp_ports"):
            args.append(f"--wf-udp={','.join(map(str, game_data['udp_ports']))}")
        if game_data.get("tcp_ports"):
            args.append(f"--wf-tcp={','.join(map(str, game_data['tcp_ports']))}")
            
        # Добавляем параметры DPI desync
        args.extend(game_data.get("dpi_desync_params", []))
        
        return Strategy(
            name=name,
            engine="winws",
            args=args,
            kind="game",
            winws_params=game_data.get("winws_params", []),
            **kwargs
        )
        
    @staticmethod
    def get_game_strategy_data(name: str) -> Optional[Dict[str, Any]]:
        """Возвращает данные для игровой стратегии."""
        games = {
            "Gv1": {
                "title": "CS:GO",
                "fake_files": ["stun.bin"],
                "udp_ports": [27015, 27020],
                "tcp_ports": [27015, 27020],
                "dpi_desync_params": ["--dpi-desync=fake", "--dpi-desync-tls=fake"],
                "winws_params": ["--hostlist-exclude", "localhost", "127.0.0.1"],
                "description": "Counter-Strike: Global Offensive"
            },
            "Gv2": {
                "title": "Dota 2",
                "fake_files": ["stun.bin", "quic_initial_www_google_com.bin"],
                "udp_ports": [27015, 27016, 27017, 27018, 27019],
                "tcp_ports": [27015, 27016, 27017, 27018, 27019],
                "dpi_desync_params": ["--dpi-desync=fake", "--dpi-desync-tls=fake"],
                "winws_params": ["--hostlist-exclude", "localhost", "127.0.0.1"],
                "description": "Dota 2"
            },
            "Gv3": {
                "title": "PUBG",
                "fake_files": ["stun.bin", "quic_initial_www_google_com.bin"],
                "udp_ports": [27015, 27016, 27017, 27018, 27019, 27020],
                "tcp_ports": [27015, 27016, 27017, 27018, 27019, 27020],
                "dpi_desync_params": ["--dpi-desync=fake", "--dpi-desync-tls=fake"],
                "winws_params": ["--hostlist-exclude", "localhost", "127.0.0.1"],
                "description": "PlayerUnknown's Battlegrounds"
            },
            "Gv4": {
                "title": "Warface",
                "fake_files": ["stun.bin", "quic_initial_www_google_com.bin"],
                "udp_ports": [27015, 27016, 27017, 27018, 27019, 27020, 27021],
                "tcp_ports": [27015, 27016, 27017, 27018, 27019, 27020, 27021],
                "dpi_desync_params": ["--dpi-desync=fake", "--dpi-desync-tls=fake"],
                "winws_params": ["--hostlist-exclude", "localhost", "127.0.0.1"],
                "description": "Warface"
            }
        }
        
        return games.get(name)
        
    @staticmethod
    def create_discord_strategy(name: str, **kwargs) -> Strategy:
        """Создает Discord стратегию."""
        discord_data = StrategyFactory.get_discord_strategy_data(name)
        if not discord_data:
            raise ValueError(f"Unknown discord strategy: {name}")
            
        args = list(discord_data.get("args", []))
        
        # Добавляем блоки
        for block_type in discord_data.get("block_types", []):
            args.append(f"--block={block_type}")
            
        # Добавляем финские IP
        if discord_data.get("finnish_ips"):
            args.append(f"--hostlist={','.join(discord_data['finnish_ips'])}")
            
        return Strategy(
            name=name,
            engine="winws",
            args=args,
            kind="discord",
            winws_params=discord_data.get("winws_params", []),
            **kwargs
        )
        
    @staticmethod
    def get_discord_strategy_data(name: str) -> Optional[Dict[str, Any]]:
        """Возвращает данные для Discord стратегии."""
        discords = {
            "Dv1": {
                "title": "Discord Basic",
                "block_types": ["Yv1"],
                "finnish_ips": ["31.13.72.36", "31.13.73.36"],
                "winws_params": ["--hostlist-exclude", "localhost", "127.0.0.1"],
                "description": "Базовая блокировка Discord"
            },
            "Dv2": {
                "title": "Discord Extended",
                "block_types": ["Yv1", "Yv2"],
                "finnish_ips": ["31.13.72.36", "31.13.73.36", "31.13.74.36"],
                "winws_params": ["--hostlist-exclude", "localhost", "127.0.0.1"],
                "description": "Расширенная блокировка Discord"
            },
            "Dv3": {
                "title": "Discord Full",
                "block_types": ["Yv1", "Yv2", "Yv3"],
                "finnish_ips": ["31.13.72.36", "31.13.73.36", "31.13.74.36", "31.13.75.36"],
                "winws_params": ["--hostlist-exclude", "localhost", "127.0.0.1"],
                "description": "Полная блокировка Discord"
            },
            # ... можно добавить больше Dv4-Dv17
        }
        
        return discords.get(name)
        
    @staticmethod
    def create_youtube_strategy(name: str, **kwargs) -> Strategy:
        """Создает YouTube стратегию."""
        youtube_data = StrategyFactory.get_youtube_strategy_data(name)
        if not youtube_data:
            raise ValueError(f"Unknown youtube strategy: {name}")
            
        args = list(youtube_data.get("args", []))
        
        # Добавляем списки
        for list_type in youtube_data.get("list_types", []):
            args.append(f"--hostlist={list_type}.txt")
            
        return Strategy(
            name=name,
            engine="winws",
            args=args,
            kind="youtube",
            winws_params=youtube_data.get("winws_params", []),
            **kwargs
        )
        
    @staticmethod
    def get_youtube_strategy_data(name: str) -> Optional[Dict[str, Any]]:
        """Возвращает данные для YouTube стратегии."""
        youtubes = {
            "Yv1": {
                "title": "YouTube Basic",
                "list_types": ["ListStrYou"],
                "winws_params": ["--hostlist-exclude", "localhost", "127.0.0.1"],
                "description": "Базовая блокировка YouTube"
            },
            "Yv2": {
                "title": "YouTube Extended",
                "list_types": ["ListStrYou", "ListStrYouEx"],
                "winws_params": ["--hostlist-exclude", "localhost", "127.0.0.1"],
                "description": "Расширенная блокировка YouTube"
            },
            # ... можно добавить больше Yv3-YvXX
        }
        
        return youtubes.get(name)