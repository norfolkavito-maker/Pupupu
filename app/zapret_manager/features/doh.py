from __future__ import annotations

import logging
from pathlib import Path

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.state import save_state
from app.zapret_manager.utils.platform import is_admin, is_windows
from app.zapret_manager.utils.subprocessx import popen_detached, run


log = logging.getLogger(__name__)


PROFILES: dict[str, str] = {
    "default": "https://cloudflare-dns.com/dns-query",
    "comss": "https://dns.comss.one/dns-query",
    "xbox": "https://xbox-dns.ru/dns-query",
    "malw": "https://dns.malw.link/dns-query",
    "malw_cf": "https://5u35p8m9i7.cloudflare-gateway.com/dns-query",
    "mafioznik": "https://dns.mafioznik.xyz/dns-query",
    "astracat": "https://dns.astracat.ru/dns-query",
}


def _cloudflared_path(ctx: AppContext) -> Path:
    return (ctx.paths.runtime_dir / "doh" / "cloudflared.exe").resolve()


def ensure_admin_windows() -> None:
    if not is_windows():
        raise RuntimeError("Windows-only")
    if not is_admin():
        raise RuntimeError("Нужны права администратора (для DNS).")


def detect_adapter(ctx: AppContext) -> str:
    if ctx.config.network.adapter_name.strip():
        return ctx.config.network.adapter_name.strip()
    # Best-effort auto-detect active adapter
    ps = [
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object -First 1 -ExpandProperty Name",
    ]
    r = run(ps, check=False, capture=True)
    name = (r.out or "").strip()
    if not name:
        raise RuntimeError("Не удалось определить сетевой адаптер. Укажи network.adapter_name в config.yaml.")
    return name


def _get_dns_state(adapter: str) -> dict:
    ps = [
        "powershell",
        "-NoProfile",
        "-Command",
        (
            "$a=$args[0];"
            "$ip=Get-NetIPInterface -InterfaceAlias $a -AddressFamily IPv4 | Select-Object -First 1;"
            "$dns=Get-DnsClientServerAddress -InterfaceAlias $a -AddressFamily IPv4 | Select-Object -First 1;"
            "$obj=[PSCustomObject]@{ IsDhcp=($ip.Dhcp -eq 'Enabled'); Servers=$dns.ServerAddresses };"
            "$obj | ConvertTo-Json -Compress"
        ),
        adapter,
    ]
    r = run(ps, check=True, capture=True)
    import json

    return json.loads(r.out)


def _set_dns(adapter: str, *, mode: str, servers: list[str] | None = None) -> None:
    if mode == "dhcp":
        run(["netsh", "interface", "ip", "set", "dns", f"name={adapter}", "source=dhcp"], check=True)
        return
    servers = servers or []
    if not servers:
        raise RuntimeError("servers required for static dns")
    # set primary
    run(
        ["netsh", "interface", "ip", "set", "dns", f"name={adapter}", "source=static", f"addr={servers[0]}", "register=primary"],
        check=True,
    )
    # add others
    for idx, srv in enumerate(servers[1:], start=2):
        run(
            ["netsh", "interface", "ip", "add", "dns", f"name={adapter}", srv, f"index={idx}"],
            check=True,
        )


def start_doh(ctx: AppContext, profile: str) -> None:
    ensure_admin_windows()
    profile = (profile or "default").strip()
    if profile not in PROFILES:
        raise RuntimeError(f"Unknown DoH profile: {profile}")

    bin_path = _cloudflared_path(ctx)
    if not bin_path.exists():
        raise RuntimeError(
            "cloudflared.exe не найден. Сначала установи DoH runtime (будет добавлено в меню)."
        )

    adapter = detect_adapter(ctx)
    prev = _get_dns_state(adapter)
    ctx.state.doh.prev_dns = {"adapter": adapter, "state": prev}

    listen = f"{ctx.config.doh.listen_addr}:{ctx.config.doh.listen_port}"
    upstream = PROFILES[profile]
    args = [
        str(bin_path),
        "proxy-dns",
        "--address",
        ctx.config.doh.listen_addr,
        "--port",
        str(ctx.config.doh.listen_port),
        "--upstream",
        upstream,
    ]
    p = popen_detached(args, cwd=str(bin_path.parent))

    _set_dns(adapter, mode="static", servers=[ctx.config.doh.listen_addr])

    ctx.state.doh.enabled = True
    ctx.state.doh.profile = profile
    ctx.state.doh.pid = int(p.pid)
    save_state(ctx.paths.state_file, ctx.state)
    log.info("DoH started: %s (pid=%s) on %s", profile, p.pid, listen)


def stop_doh(ctx: AppContext) -> None:
    ensure_admin_windows()
    pid = ctx.state.doh.pid
    if pid:
        run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False)

    prev = ctx.state.doh.prev_dns or {}
    adapter = prev.get("adapter")
    state = prev.get("state") or {}
    if adapter:
        is_dhcp = bool(state.get("IsDhcp"))
        servers = state.get("Servers") or []
        if is_dhcp:
            _set_dns(adapter, mode="dhcp")
        else:
            _set_dns(adapter, mode="static", servers=[str(x) for x in servers] if servers else ["8.8.8.8"])

    ctx.state.doh.enabled = False
    ctx.state.doh.pid = None
    ctx.state.doh.prev_dns = {}
    save_state(ctx.paths.state_file, ctx.state)

