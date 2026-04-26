from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.zapret_manager.core.app_context import AppContext


@dataclass(frozen=True)
class DomainSet:
    key: str
    title: str
    rel_path: str
    description: str = ""

    def file_path(self, ctx: "AppContext") -> Path:
        return (ctx.paths.data_dir / self.rel_path).resolve()


DOMAIN_SETS: list[DomainSet] = [
    DomainSet(
        key="all",
        title="All (все наборы)",
        rel_path="tests/domains_all.txt",
        description="Объединение всех наборов (default + youtube + cdn + amazon + discord + instagram + games).",
    ),
    DomainSet(
        key="default",
        title="Default (общий набор)",
        rel_path="tests/domains_default.txt",
        description="Базовый набор доменов для проверки доступности.",
    ),
    DomainSet(
        key="youtube",
        title="YouTube / GoogleVideo (замедление)",
        rel_path="tests/domains_youtube.txt",
        description="youtube.com, googlevideo, ytimg, ggpht.",
    ),
    DomainSet(
        key="cdn",
        title="CDN / Cloudflare / Fastly",
        rel_path="tests/domains_cdn.txt",
        description="cloudflare/fastly/akamai — полезно для диагностики DPI/HTTPS.",
    ),
    DomainSet(
        key="amazon",
        title="Amazon / AWS",
        rel_path="tests/domains_amazon.txt",
        description="amazon/primevideo/aws endpoints.",
    ),
    DomainSet(
        key="discord",
        title="Discord",
        rel_path="tests/domains_discord.txt",
        description="discord.com и связанные домены.",
    ),
    DomainSet(
        key="instagram",
        title="Instagram / Meta",
        rel_path="tests/domains_instagram.txt",
        description="instagram + fbcdn/cdninstagram.",
    ),
    DomainSet(
        key="games",
        title="Games (общие игровые домены)",
        rel_path="tests/domains_games.txt",
        description="Набор доменов для диагностики игровых сервисов (best-effort).",
    ),
]


def ensure_domain_sets(ctx: "AppContext") -> None:
    """Create default domain set files if missing.

    Users can edit these files in DedZapretData without rebuilding the app.
    """

    base_dir = (ctx.paths.data_dir / "tests").resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    defaults: dict[str, str] = {
        # NOTE: domains_all.txt is not created by default. "all" set is computed
        # dynamically by combining other set files.
        "tests/domains_default.txt": "\n".join(
            [
                "# Default domains (one per line). You can add/remove lines.",
                "# Lines starting with # are ignored.",
                "https://gosuslugi.ru/",
                "https://nalog.ru/",
                "https://discord.com/",
                "https://x.com/",
                "https://instagram.com/",
                "https://facebook.com/",
                "https://rutracker.org/",
                "https://rutor.info/",
                "https://openwrt.org/",
                "https://cloudflare.com/",
                "https://speed.cloudflare.com/",
                "https://amazon.com/",
                "https://aws.amazon.com/",
                "",
            ]
        ),
        "tests/domains_youtube.txt": "\n".join(
            [
                "# YouTube/GoogleVideo slow/blocked probes",
                "https://youtube.com/",
                "https://www.youtube.com/",
                "https://m.youtube.com/",
                "https://ytimg.com/",
                "https://i.ytimg.com/",
                "https://ggpht.com/",
                "https://googlevideo.com/",
                # real probe hosts often change; user can paste their own
                "rr1---sn-gvnuxaxjvh-jx3z.googlevideo.com",
                "rr1---sn-gvnuxaxjvh-jx3l.googlevideo.com",
                "",
            ]
        ),
        "tests/domains_cdn.txt": "\n".join(
            [
                "# CDN endpoints",
                "https://cloudflare.com/",
                "https://speed.cloudflare.com/",
                "https://cdnjs.cloudflare.com/",
                "https://fastly.com/",
                "https://www.akamai.com/",
                "",
            ]
        ),
        "tests/domains_amazon.txt": "\n".join(
            [
                "# Amazon/AWS endpoints",
                "https://amazon.com/",
                "https://www.amazon.com/",
                "https://primevideo.com/",
                "https://aws.amazon.com/",
                "",
            ]
        ),
        "tests/domains_discord.txt": "\n".join(
            [
                "# Discord domains",
                "https://discord.com/",
                "https://discordapp.com/",
                "https://discord.gg/",
                "https://discord.media/",
                "https://gateway.discord.gg/",
                "",
            ]
        ),
        "tests/domains_instagram.txt": "\n".join(
            [
                "# Instagram / Meta domains",
                "https://instagram.com/",
                "https://www.instagram.com/",
                "https://cdninstagram.com/",
                "https://fbcdn.net/",
                "https://facebook.com/",
                "",
            ]
        ),
        "tests/domains_games.txt": "\n".join(
            [
                "# Games / gaming services (best-effort)",
                "# NOTE: game connectivity is often UDP-only and can't be reliably checked by HTTP.",
                "# Keep this list for auxiliary diagnostics.",
                "https://store.steampowered.com/",
                "https://steamcommunity.com/",
                "https://api.steampowered.com/",
                "https://epicgames.com/",
                "https://www.epicgames.com/",
                "https://origin.com/",
                "",
            ]
        ),
    }

    for rel, content in defaults.items():
        p = (ctx.paths.data_dir / rel).resolve()
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")


def read_domain_set_file(path: Path) -> list[str]:
    if not path.exists():
        return []
    out: list[str] = []
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        out.append(ln)
    return out


def combine_domain_sets(ctx: "AppContext", keys: list[str]) -> list[str]:
    """Combine multiple domain sets with deduplication, preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for key in keys:
        ds = next((d for d in DOMAIN_SETS if d.key == key), None)
        if not ds:
            continue
        for ln in read_domain_set_file(ds.file_path(ctx)):
            if ln in seen:
                continue
            seen.add(ln)
            out.append(ln)
    return out
