from __future__ import annotations


def discord_profile_args(profile: str) -> list[str]:
    """
    Профили Discord (best-effort перенос из Zapret-Manager.sh).
    Возвращает список аргументов, которые добавляются к текущей стратегии.
    """
    profile = (profile or "").strip()
    if not profile:
        return []

    # Сейчас поддержан минимум: Dv1. Остальные можно добавить аналогично.
    if profile.lower() == "dv1":
        return [
            "--new",
            "--filter-udp=19294-19344,50000-50100",
            "--filter-l7=discord,stun",
            "--dpi-desync=fake",
            "--dpi-desync-repeats=6",
            "--new",
            "--filter-tcp=2053,2083,2087,2096,8443",
            "--hostlist-domains=discord.media",
            "--dpi-desync=multisplit",
            "--dpi-desync-split-seqovl=652",
            "--dpi-desync-split-pos=2",
            "--dpi-desync-split-seqovl-pattern={FAKE:tls_clienthello_www_google_com.bin}",
        ]
    return []


def games_profile_args(profile: str) -> list[str]:
    """
    Профили игр Gv1..Gv4 (best-effort перенос из Zapret-Manager.sh).
    """
    profile = (profile or "").strip()
    if not profile:
        return []

    ports_udp = "88,1024-2407,2409-4499,4502-19293,19345-49999,50101-65535"
    ports_tcp = "2802,2302,2502,6112-6119,6695-6710,25565,27015-27030,27036-27037,50001"

    if profile.lower() in {"gv1", "gv2", "gv3", "gv4"}:
        n = int(profile[-1])
        udp_cutoff = "d2" if n == 1 else f"n{n}"
        udp_pattern = (
            "{FAKE:stun.bin}" if n == 1 else "{FAKE:quic_initial_www_google_com.bin}"
        )
        return [
            "--new",
            f"--filter-udp={ports_udp}",
            "--dpi-desync=fake",
            "--dpi-desync-any-protocol=1",
            "--dpi-desync-repeats=10" if n != 1 else "",
            f"--dpi-desync-fake-unknown-udp={udp_pattern}",
            f"--dpi-desync-cutoff={udp_cutoff}",
            "--new",
            f"--filter-tcp={ports_tcp}",
            "--dpi-desync-any-protocol=1",
            "--dpi-desync-cutoff=n5",
            "--dpi-desync=multisplit",
            "--dpi-desync-split-seqovl=582",
            "--dpi-desync-split-pos=1",
            "--dpi-desync-split-seqovl-pattern={FAKE:stun.bin}",
        ]
    return []


def _compact_args(args: list[str]) -> list[str]:
    return [a for a in args if a and a.strip()]


def apply_overlays(base_args: list[str], *, discord_profile: str, games_profile: str) -> list[str]:
    out = list(base_args)
    out.extend(discord_profile_args(discord_profile))
    out.extend(games_profile_args(games_profile))
    return _compact_args(out)

