from __future__ import annotations

from pathlib import Path

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.upstreams.http import download


def doh_dir(ctx: AppContext) -> Path:
    return (ctx.paths.runtime_dir / "doh").resolve()


def cloudflared_path(ctx: AppContext) -> Path:
    return doh_dir(ctx) / "cloudflared.exe"


def install_cloudflared(ctx: AppContext) -> Path:
    d = doh_dir(ctx)
    d.mkdir(parents=True, exist_ok=True)
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    dest = cloudflared_path(ctx)
    download(url, dest)
    return dest


def uninstall_cloudflared(ctx: AppContext) -> None:
    d = doh_dir(ctx)
    if d.exists():
        for p in d.glob("*"):
            try:
                p.unlink()
            except Exception:
                pass
        try:
            d.rmdir()
        except Exception:
            pass

