from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass

from app.zapret_manager.core.diagnostics import diag_log


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class CmdResult:
    code: int
    out: str
    err: str


def run(
    args: list[str],
    *,
    check: bool = False,
    capture: bool = True,
    cwd: str | None = None,
    timeout: int | None = None,
) -> CmdResult:
    log.info("run: %s", args)
    diag_log("process.run", "subprocessx", {"args": args, "cwd": cwd, "timeout": timeout, "capture": capture})
    p = subprocess.run(
        args,
        check=False,
        cwd=cwd,
        timeout=timeout,
        text=True,
        capture_output=capture,
        encoding="utf-8",
        errors="replace",
    )
    if check and p.returncode != 0:
        diag_log(
            "process.error",
            "subprocessx",
            {"args": args, "code": p.returncode, "stderr": p.stderr or "", "stdout": p.stdout or ""},
        )
        raise RuntimeError(f"Command failed ({p.returncode}): {args}\n{p.stderr}")
    diag_log(
        "process.result",
        "subprocessx",
        {"args": args, "code": p.returncode, "stdout": p.stdout or "", "stderr": p.stderr or ""},
    )
    return CmdResult(code=p.returncode, out=p.stdout or "", err=p.stderr or "")


def popen_detached(args: list[str], *, cwd: str | None = None) -> subprocess.Popen:
    log.info("popen: %s", args)
    diag_log("process.popen", "subprocessx", {"args": args, "cwd": cwd})
    # On Windows create new process group to allow taskkill by PID.
    creationflags = 0
    try:
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    except Exception:
        creationflags = 0

    return subprocess.Popen(
        args,
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
    )

