from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.state import save_state
from app.zapret_manager.upstreams.github_release import download_asset, latest_release
from app.zapret_manager.utils.platform import is_windows
from app.zapret_manager.utils.subprocessx import popen_detached, run


log = logging.getLogger(__name__)


def _tg_dir(ctx: AppContext) -> Path:
    d = (ctx.paths.runtime_dir / "tg").resolve()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def install_go(ctx: AppContext) -> Path:
    """
    Go-вариант по смыслу StressOzz. На Windows используем Flowseal/tg-ws-proxy asset.
    """
    rel = latest_release("Flowseal", "tg-ws-proxy")
    asset = next((a for a in rel.assets if a.name.lower() == "tgwsproxy_windows.exe"), None)
    if not asset:
        # fallback: any .exe containing windows
        asset = next((a for a in rel.assets if "windows" in a.name.lower() and a.name.lower().endswith(".exe")), None)
    if not asset:
        raise RuntimeError("Не найден Windows asset в Flowseal/tg-ws-proxy latest release.")

    dest = _tg_dir(ctx) / "TgWsProxy_windows.exe"
    download_asset(asset, dest)
    ctx.state.tg["go"] = {"path": str(dest), "sha256": _sha256(dest), "tag": rel.tag}
    save_state(ctx.paths.state_file, ctx.state)
    return dest


def uninstall_go(ctx: AppContext) -> None:
    stop_go(ctx)
    info = ctx.state.tg.get("go") or {}
    p = Path(info.get("path") or "")
    if p.exists():
        p.unlink(missing_ok=True)  # type: ignore[arg-type]
    ctx.state.tg.pop("go", None)
    save_state(ctx.paths.state_file, ctx.state)


def start_go(ctx: AppContext) -> int:
    if not is_windows():
        raise RuntimeError("Windows-only")
    info = ctx.state.tg.get("go") or {}
    p = Path(info.get("path") or "")
    if not p.exists():
        raise RuntimeError("TG WS Proxy Go не установлен. Сначала установи.")
    proc = popen_detached([str(p)], cwd=str(p.parent))
    info["pid"] = int(proc.pid)
    ctx.state.tg["go"] = info
    save_state(ctx.paths.state_file, ctx.state)
    return int(proc.pid)


def stop_go(ctx: AppContext) -> None:
    info = ctx.state.tg.get("go") or {}
    pid = info.get("pid")
    if pid:
        run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False)
        info["pid"] = None
        ctx.state.tg["go"] = info
        save_state(ctx.paths.state_file, ctx.state)


def install_rust(ctx: AppContext) -> Path:
    rel = latest_release("valnesfjord", "tg-ws-proxy-rs")
    # pick windows asset, prefer x86_64
    candidates = [a for a in rel.assets if a.name.lower().endswith(".exe") and "win" in a.name.lower()]
    asset = next((a for a in candidates if "x86_64" in a.name.lower() or "amd64" in a.name.lower()), None) or (candidates[0] if candidates else None)
    if not asset:
        raise RuntimeError("Не найден Windows asset в valnesfjord/tg-ws-proxy-rs latest release.")
    dest = _tg_dir(ctx) / "tg-ws-proxy-rs.exe"
    download_asset(asset, dest)
    ctx.state.tg["rust"] = {"path": str(dest), "sha256": _sha256(dest), "tag": rel.tag}
    save_state(ctx.paths.state_file, ctx.state)
    return dest


def uninstall_rust(ctx: AppContext) -> None:
    stop_rust(ctx)
    info = ctx.state.tg.get("rust") or {}
    p = Path(info.get("path") or "")
    if p.exists():
        p.unlink(missing_ok=True)  # type: ignore[arg-type]
    ctx.state.tg.pop("rust", None)
    save_state(ctx.paths.state_file, ctx.state)


def start_rust(ctx: AppContext, *, host: str = "0.0.0.0", port: int = 2443, secret: str | None = None) -> int:
    if not is_windows():
        raise RuntimeError("Windows-only")
    info = ctx.state.tg.get("rust") or {}
    p = Path(info.get("path") or "")
    if not p.exists():
        raise RuntimeError("TG WS Proxy Rust не установлен. Сначала установи.")
    args = [str(p)]
    # best-effort common CLI flags (Flowseal-compatible)
    args += ["--host", host, "--port", str(port)]
    if secret:
        args += ["--secret", secret]
    proc = popen_detached(args, cwd=str(p.parent))
    info["pid"] = int(proc.pid)
    info["host"] = host
    info["port"] = int(port)
    ctx.state.tg["rust"] = info
    save_state(ctx.paths.state_file, ctx.state)
    return int(proc.pid)


def stop_rust(ctx: AppContext) -> None:
    info = ctx.state.tg.get("rust") or {}
    pid = info.get("pid")
    if pid:
        run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False)
        info["pid"] = None
        ctx.state.tg["rust"] = info
        save_state(ctx.paths.state_file, ctx.state)

