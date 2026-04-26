from __future__ import annotations

from dataclasses import dataclass

from app.zapret_manager.strategies.model import Strategy
from app.zapret_manager.strategies.overlays import games_profile_args


DISCORD_PORTS = "2053,2083,2087,2096,8443"


@dataclass(frozen=True)
class ComposedStrategy:
    engine: str
    args: list[str]
    warnings: list[str]


def compose(
    *,
    base: Strategy,
    youtube: Strategy | None,
    discord: Strategy | None,
    discord_script: str,
    games_profile: str,
    rkn_enabled: bool,
    wssize_enabled: bool,
) -> ComposedStrategy:
    if base.kind != "base":
        raise ValueError("base strategy must be kind=base")

    args = list(base.args)
    warnings: list[str] = []

    if youtube:
        args = _insert_before_first_new(args, youtube.args)

    if discord:
        args = _replace_discord_block(args, discord.args)

    if discord_script:
        args = _append_block(args, _discord_script_args(discord_script))

    if games_profile:
        args = _append_block(args, games_profile_args(games_profile))

    if wssize_enabled:
        args = _append_block(args, ["--new", "--filter-tcp=443", "--wssize", "1:6"])

    if rkn_enabled:
        args = _toggle_rkn(args, enabled=True)

    # timestamps hint
    if any("=ts" in a or a.endswith("ts") or "fooling=ts" in a for a in args):
        warnings.append("Для работы стратегии включи TCP timestamps: netsh int tcp set global timestamps=enabled")

    return ComposedStrategy(engine=base.engine, args=_compact(args), warnings=warnings)


def _compact(args: list[str]) -> list[str]:
    return [a for a in args if a and a.strip()]


def _insert_before_first_new(base_args: list[str], insert_args: list[str]) -> list[str]:
    out = list(base_args)
    try:
        idx = out.index("--new")
    except ValueError:
        idx = 0
    return out[:idx] + list(insert_args) + out[idx:]


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
            cur.append(a)
    if cur:
        blocks.append(cur)
    return blocks


def _is_discord_block(block: list[str]) -> bool:
    joined = " ".join(block).lower()
    if "discord.media" in joined:
        return True
    if "filter-l7=discord" in joined:
        return True
    if DISCORD_PORTS in joined:
        return True
    return False


def _replace_discord_block(args: list[str], dv_args: list[str]) -> list[str]:
    blocks = _split_blocks(args)
    idx = None
    for i, b in enumerate(blocks):
        if _is_discord_block(b):
            idx = i
            break
    replacement = list(dv_args)
    if not replacement or replacement[0] != "--new":
        replacement = ["--new"] + replacement
    if idx is None:
        # fallback: добавить новый Discord-блок в конец
        return list(args) + replacement
    blocks[idx] = replacement
    return [a for b in blocks for a in b]


def _append_block(args: list[str], block_args: list[str]) -> list[str]:
    b = _compact(block_args)
    if not b:
        return args
    if b[0] != "--new":
        b = ["--new"] + b
    return list(args) + b


def _toggle_rkn(args: list[str], *, enabled: bool) -> list[str]:
    out: list[str] = []
    for a in args:
        if a.startswith("--hostlist-exclude=") and enabled:
            # use manager list placeholder
            out.append("--hostlist={MGR_LISTS}rkn.txt")
            continue
        if a.startswith("--hostlist=") and not enabled and "{MGR_LISTS}rkn.txt" in a:
            out.append("--hostlist-exclude={MGR_LISTS}exclude.txt")
            continue
        out.append(a)
    return out


def _discord_script_args(script_name: str) -> list[str]:
    s = script_name.strip().lower()
    if not s:
        return []
    if s in {"50-stun4all", "stun4all"}:
        return ["--new", "--filter-udp=1-65535", "--filter-l7=stun", "--dpi-desync=fake", "--dpi-desync-repeats=2"]
    if s in {"50-quic4all", "quic4all"}:
        return [
            "--new",
            "--filter-udp=1-65535",
            "--dpi-desync=fake",
            "--dpi-desync-repeats=2",
            "--dpi-desync-fake-unknown-udp={FAKE:quic_initial_ietf.bin}",
        ]
    if s in {"50-discord-media", "discord-media"}:
        return ["--new", f"--filter-tcp={DISCORD_PORTS}", "--hostlist-domains=discord.media", "--dpi-desync=fake", "--dpi-desync-repeats=2"]
    if s in {"50-discord", "discord"}:
        return ["--new", f"--filter-tcp={DISCORD_PORTS}", "--hostlist-domains=discord.media", "--dpi-desync=multisplit", "--dpi-desync-repeats=4"]
    return []

