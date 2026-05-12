from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.features.zapret_runtime import stop_zapret
from app.zapret_manager.utils.platform import is_windows
from app.zapret_manager.utils.subprocessx import run

log = logging.getLogger(__name__)


def _blockcheck_dir(ctx: AppContext) -> Path:
    return (ctx.paths.runtime_dir / "zapret" / "blockcheck").resolve()


def _decode_windows_output(output: bytes) -> str:
    """Decode Windows command output properly."""
    try:
        # Try UTF-8 first
        return output.decode("utf-8")
    except UnicodeDecodeError:
        try:
            # Fallback to Windows-1252 (common in Russian Windows)
            return output.decode("cp1252")
        except UnicodeDecodeError:
            # Last resort: replace problematic chars
            return output.decode("utf-8", errors="replace")


def run_blockcheck(ctx: AppContext, *, variant: str = "1") -> Dict[str, Any]:
    """Run blockcheck and return structured result."""
    if not is_windows():
        raise RuntimeError("Windows-only")
    
    stop_zapret(ctx)
    d = _blockcheck_dir(ctx)
    if not d.exists():
        raise RuntimeError(
            "blockcheck directory not found in runtime. "
            "Bundled runtime is missing. Re-download/re-extract the release."
        )

    script = d / ("blockcheck2.cmd" if variant == "2" else "blockcheck.cmd")
    if not script.exists():
        raise RuntimeError(f"{script.name} not found in runtime.")

    # Run script directly in the current console, preserving cwd
    try:
        result = run(["cmd", "/c", str(script)], check=False, capture=True, cwd=str(d))
        
        # Decode output properly
        stdout = _decode_windows_output(result.stdout or b"")
        stderr = _decode_windows_output(result.stderr or b"")
        
        # Parse and structure the result
        blockcheck_result = {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "variant": variant,
            "script": str(script),
            "cwd": str(d)
        }
        
        # Log structured result
        if result.returncode == 0:
            log.info("Blockcheck completed successfully (variant %s)", variant)
        else:
            log.warning("Blockcheck failed (variant %s): returncode=%d", variant, result.returncode)
            log.debug("Blockcheck stderr: %s", stderr)
        
        return blockcheck_result
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "variant": variant,
            "script": str(script),
            "cwd": str(d)
        }
        log.error("Blockcheck execution failed: %s", e)
        return error_result


def run_blockcheck_settings(ctx: AppContext) -> Dict[str, Any]:
    """Run blockcheck settings action and return structured result."""
    return run_blockcheck(ctx, variant="settings")


def parse_blockcheck_output(output: str) -> Dict[str, Any]:
    """Parse blockcheck output for structured information."""
    result = {
        "working_domains": [],
        "broken_domains": [],
        "errors": [],
        "warnings": []
    }
    
    # Simple parsing - can be enhanced based on actual blockcheck output format
    lines = output.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith("OK:"):
            domain = line[3:].strip()
            result["working_domains"].append(domain)
        elif line.startswith("FAIL:"):
            domain = line[5:].strip()
            result["broken_domains"].append(domain)
        elif line.startswith("ERROR:"):
            error = line[6:].strip()
            result["errors"].append(error)
        elif line.startswith("WARNING:"):
            warning = line[9:].strip()
            result["warnings"].append(warning)
    
    return result

