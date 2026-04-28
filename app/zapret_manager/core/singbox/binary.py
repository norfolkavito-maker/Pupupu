from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SingBoxBinary:
    path: Path


def detect_singbox_binary(root: Path) -> SingBoxBinary | None:
    p = (root / "bin" / "sing-box" / "sing-box.exe").resolve()
    if p.exists() and p.is_file():
        return SingBoxBinary(path=p)
    return None


def singbox_version(bin_path: Path, *, timeout_s: float = 3.0) -> str:
    p = subprocess.run(
        [str(bin_path), "version"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_s,
    )
    out = (p.stdout or "").strip() + ("\n" + (p.stderr or "").strip() if (p.stderr or "").strip() else "")
    return out.strip()
