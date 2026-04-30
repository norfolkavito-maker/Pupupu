from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REG_PATH = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings"


def _run_reg(args: list[str]) -> str:
    p = subprocess.run(args, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
    if p.returncode != 0:
        raise RuntimeError(out.strip() or f"reg command failed: {args}")
    return out


def read_system_proxy() -> dict[str, str | int]:
    if os.name != "nt":
        raise RuntimeError("system proxy is Windows-only")
    txt = _run_reg(["reg", "query", REG_PATH])
    out: dict[str, str | int] = {"ProxyEnable": 0, "ProxyServer": "", "ProxyOverride": ""}
    for ln in txt.splitlines():
        s = ln.strip()
        if s.startswith("ProxyEnable"):
            # ... REG_DWORD 0x1
            if "0x" in s:
                try:
                    out["ProxyEnable"] = int(s.split("0x", 1)[1], 16)
                except Exception:
                    out["ProxyEnable"] = 0
        elif s.startswith("ProxyServer"):
            out["ProxyServer"] = s.split()[-1] if s.split() else ""
        elif s.startswith("ProxyOverride"):
            parts = s.split()
            out["ProxyOverride"] = parts[-1] if parts else ""
    return out


def write_system_proxy(*, enable: int, server: str, override: str) -> None:
    if os.name != "nt":
        raise RuntimeError("system proxy is Windows-only")
    _run_reg(["reg", "add", REG_PATH, "/v", "ProxyEnable", "/t", "REG_DWORD", "/d", str(int(enable)), "/f"])
    _run_reg(["reg", "add", REG_PATH, "/v", "ProxyServer", "/t", "REG_SZ", "/d", server, "/f"])
    _run_reg(["reg", "add", REG_PATH, "/v", "ProxyOverride", "/t", "REG_SZ", "/d", override, "/f"])


def backup_system_proxy(path: Path, *, current: dict[str, str | int] | None = None) -> None:
    data = current if current is not None else read_system_proxy()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def restore_system_proxy(path: Path) -> None:
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    write_system_proxy(
        enable=int(data.get("ProxyEnable", 0) or 0),
        server=str(data.get("ProxyServer", "") or ""),
        override=str(data.get("ProxyOverride", "") or ""),
    )


def enable_local_proxy_with_backup(path: Path, *, host: str = "127.0.0.1", port: int = 2081) -> None:
    backup_system_proxy(path)
    override = "<local>;localhost;127.0.0.1;192.168.*;10.*;172.16.*"
    write_system_proxy(enable=1, server=f"{host}:{int(port)}", override=override)
