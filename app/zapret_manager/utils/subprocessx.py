from __future__ import annotations

import logging
import subprocess
import locale
import os
from dataclasses import dataclass
from pathlib import Path

from app.zapret_manager.core.diagnostics import diag_log


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class CmdResult:
    code: int
    out: str
    err: str
    encoding_used: str = ""


def decode_bytes_best_effort(data: bytes, *, preferred: str) -> tuple[str, str]:
    """Decode subprocess output bytes with Windows-friendly fallbacks.

    Rationale: many Windows console tools output using OEM code page (often cp866
    for RU), not UTF-8.

    Returns: (text, encoding_used)
    """
    candidates = [preferred]
    # Common Windows fallback(s)
    if preferred.lower() != "cp866":
        candidates.append("cp866")
    if preferred.lower() != "utf-8":
        candidates.append("utf-8")

    # We only accept an encoding as "used" if it doesn't produce replacement chars,
    # otherwise we try the next candidate.
    for enc in candidates:
        try:
            text = data.decode(enc, errors="replace")
            if "\ufffd" in text:
                continue
            return (text, enc)
        except Exception:
            continue

    # Last resort: replace
    return (data.decode(preferred or "utf-8", errors="replace"), preferred or "utf-8")


def _windows_oem_encoding() -> str:
    """Return Windows OEM code page encoding name.

    Many console tools (ping, ipconfig, netsh, etc.) write in OEM code page
    (cp866 for RU), not in ANSI code page. Using utf-8 causes mojibake.
    """
    if os.name != "nt":
        return "utf-8"

    # Best-effort: read current console output CP (OEM) via WinAPI.
    try:
        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        GetConsoleOutputCP = kernel32.GetConsoleOutputCP
        GetConsoleOutputCP.restype = ctypes.c_uint
        cp = int(GetConsoleOutputCP())
        if cp:
            return f"cp{cp}"
    except Exception:
        pass

    # Fallback: OEM code page (RU typical).
    return "cp866"


def _default_text_encoding() -> str:
    if os.name == "nt":
        # Prefer OEM for console utilities.
        return _windows_oem_encoding()
    return "utf-8"


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

    encoding = _default_text_encoding()
    if capture:
        # Use bytes mode to apply our own decoding with fallbacks.
        p = subprocess.run(
            args,
            check=False,
            cwd=cwd,
            timeout=timeout,
            text=False,
            capture_output=True,
        )
        out, enc_out = decode_bytes_best_effort(p.stdout or b"", preferred=encoding)
        err, enc_err = decode_bytes_best_effort(p.stderr or b"", preferred=encoding)
        encoding_used = enc_out if enc_out == enc_err else f"stdout={enc_out}; stderr={enc_err}"
    else:
        p = subprocess.run(
            args,
            check=False,
            cwd=cwd,
            timeout=timeout,
            text=True,
            capture_output=False,
            encoding=encoding,
            errors="replace",
        )
        out, err, encoding_used = "", "", encoding
    if check and p.returncode != 0:
        diag_log(
            "process.error",
            "subprocessx",
            {"args": args, "code": p.returncode, "stderr": err, "stdout": out, "encoding_used": encoding_used},
        )
        raise RuntimeError(f"Command failed ({p.returncode}): {args}\n{p.stderr}")
    diag_log(
        "process.result",
        "subprocessx",
        {"args": args, "code": p.returncode, "stdout": out, "stderr": err, "encoding_used": encoding_used},
    )
    return CmdResult(code=p.returncode, out=out, err=err, encoding_used=encoding_used)


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

