from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.zapret_manager.core.app_context import AppContext


@dataclass(frozen=True)
class DomainSet:
    key: str
    title: str
    rel_path: str
    description: str = ""

    def file_path(self, ctx: AppContext) -> Path:
        return (ctx.paths.data_dir / self.rel_path).resolve()


DOMAIN_SETS: list[DomainSet] = [
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
]


def ensure_domain_sets(ctx: AppContext) -> None:
    """Create default domain set files if missing.

    Users can edit these files in DedZapretData without rebuilding the app.
    """

    base_dir = (ctx.paths.data_dir / "tests").resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    defaults: dict[str, str] = {
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
