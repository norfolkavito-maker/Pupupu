from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

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


def popen_detached(
    args: list[str],
    *,
    cwd: str | None = None,
    stdout_path: Path | None = None,
    stderr_path: Path | None = None,
) -> subprocess.Popen:
    log.info("popen: %s", args)
    diag_log("process.popen", "subprocessx", {"args": args, "cwd": cwd})
    # On Windows create new process group to allow taskkill by PID.
    creationflags = 0
    try:
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    except Exception:
        creationflags = 0

    # If stdout/stderr are redirected into files, close parent-side file handles
    # immediately after spawn to avoid handle leaks. Child process keeps its
    # own handles.
    out_f = None
    err_f = None
    try:
        if stdout_path:
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            out_f = open(stdout_path, "ab")
        if stderr_path:
            stderr_path.parent.mkdir(parents=True, exist_ok=True)
            err_f = open(stderr_path, "ab")

        p = subprocess.Popen(
            args,
            cwd=cwd,
            stdout=out_f or subprocess.DEVNULL,
            stderr=err_f or subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        return p
    finally:
        try:
            if out_f:
                out_f.close()
        finally:
            if err_f:
                err_f.close()

