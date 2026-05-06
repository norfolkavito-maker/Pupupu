from __future__ import annotations

"""Strategy conflict detection (UX helper).

This module is intentionally heuristic and conservative:
- It MUST NOT modify original strategy files.
- It should only report obvious conflicts and suggest safe toggles.
"""

from dataclasses import dataclass

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.features.selection import find_strategy
from app.zapret_manager.strategies.composer import compose


@dataclass(frozen=True)
class Conflict:
    code: str
    title: str
    details: str
    recommendation: str


def _split_blocks(args: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    cur: list[str] = []
    for a in args:
        if a == "--new":
            if cur:
                blocks.append(cur)
            cur = ["--new"]
        else:
            if not cur:
                cur = []
            cur.append(str(a))
    if cur:
        blocks.append(cur)
    return blocks


def _parse_ports(expr: str) -> set[int]:
    """Best-effort parse for comma-separated ports and ranges (no strict validation)."""
    out: set[int] = set()
    for raw in (expr or "").split(","):
        tok = raw.strip()
        if not tok:
            continue
        if "-" in tok:
            a, b = tok.split("-", 1)
            if a.strip().isdigit() and b.strip().isdigit():
                lo = int(a)
                hi = int(b)
                if lo > hi:
                    lo, hi = hi, lo
                lo = max(1, min(65535, lo))
                hi = max(1, min(65535, hi))
                # cap expansion for safety
                if hi - lo > 10000:
                    # treat as "covers many ports" and include 443 if within range
                    if lo <= 443 <= hi:
                        out.add(443)
                else:
                    for p in range(lo, hi + 1):
                        out.add(p)
            continue
        if tok.isdigit():
            n = int(tok)
            if 1 <= n <= 65535:
                out.add(n)
    return out


def detect_conflicts(*, composed_args: list[str]) -> list[Conflict]:
    """Detect obvious conflicts in already composed winws args."""
    blocks = _split_blocks([str(a) for a in (composed_args or []) if str(a).strip()])

    udp_443_fake_blocks: list[int] = []
    for i, b in enumerate(blocks):
        udp_ports: set[int] = set()
        has_fake_quic = False
        for a in b:
            if a.startswith("--filter-udp="):
                udp_ports |= _parse_ports(a.split("=", 1)[1])
            if a.startswith("--dpi-desync-fake-unknown-udp="):
                has_fake_quic = True
            # Some strategies use fake without explicit file; still a signal.
            if a.startswith("--dpi-desync=") and a.split("=", 1)[1].strip().lower() == "fake":
                has_fake_quic = True

        if 443 in udp_ports and has_fake_quic:
            udp_443_fake_blocks.append(i)

    out: list[Conflict] = []
    if len(udp_443_fake_blocks) >= 2:
        out.append(
            Conflict(
                code="udp443_fake_quic_multi",
                title="Конфликт настроек (UDP/443 + fake QUIC)",
                details=(
                    "Обнаружено несколько блоков, которые одновременно:\n"
                    "- фильтруют UDP/443;\n"
                    "- используют fake QUIC (dpi-desync fake).\n"
                    "\nОбычно рекомендуется оставить только один такой блок."
                ),
                recommendation=(
                    "Попробуйте отключить один из источников QUIC (например: Discord script 50-quic4all "
                    "или Games profile), затем перезапустите режим."
                ),
            )
        )

    return out


def build_conflict_report_for_current_layers(ctx: AppContext) -> str:
    """Build a human-readable report for current selected base/layers."""
    base_name = (ctx.state.zapret.selected_strategy or ctx.state.zapret.base_strategy or "").strip()
    if not base_name:
        return "Не выбрана базовая стратегия.\n"

    base = find_strategy(ctx, base_name, kind="base") or find_strategy(ctx, base_name)
    if not base:
        return f"Базовая стратегия не найдена: {base_name}\n"

    youtube = None
    if (ctx.state.zapret.youtube_layer or "").strip():
        youtube = find_strategy(ctx, ctx.state.zapret.youtube_layer, kind="youtube") or find_strategy(ctx, ctx.state.zapret.youtube_layer)

    discord = None
    if (ctx.state.zapret.discord_layer or "").strip():
        discord = find_strategy(ctx, ctx.state.zapret.discord_layer, kind="discord") or find_strategy(ctx, ctx.state.zapret.discord_layer)

    composed = compose(
        base=base,
        youtube=youtube,
        discord=discord,
        discord_script=ctx.state.zapret.discord_script,
        games_profile=ctx.state.zapret.games_profile,
        rkn_enabled=ctx.state.zapret.rkn_enabled,
        wssize_enabled=ctx.state.zapret.wssize_enabled,
    )

    conflicts = detect_conflicts(composed_args=composed.args)
    if not conflicts:
        return "Конфликтов не найдено (MVP проверка).\n"

    lines: list[str] = []
    for c in conflicts:
        lines.append(c.title)
        lines.append("-" * len(c.title))
        lines.append(c.details.strip())
        lines.append("")
        lines.append("Рекомендация:")
        lines.append(c.recommendation.strip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"

