from __future__ import annotations

import json
import os
import platform
import time
import zipfile
from pathlib import Path
from typing import Any

from app.zapret_manager import __version__
from app.zapret_manager.core.mask import mask_secrets
from app.zapret_manager.utils.subprocessx import decode_bytes_best_effort


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _tree_text(root: Path, *, limit: int = 4000) -> str:
    out: list[str] = []
    count = 0
    for p in sorted(root.rglob("*")):
        if p.name.startswith("."):
            continue
        rel = str(p.relative_to(root))
        out.append(rel + ("/" if p.is_dir() else ""))
        count += 1
        if count >= limit:
            out.append(f"... <truncated after {limit} entries>")
            break
    return "\n".join(out) + "\n"


def _read_text(p: Path, *, max_len: int = 200_000) -> str:
    try:
        s = p.read_text(encoding="utf-8", errors="replace")
        if len(s) > max_len:
            return s[:max_len] + f"\n... <truncated {len(s) - max_len} chars>\n"
        return s
    except Exception:
        return ""


def generate_bug_report_zip(
    *,
    out_dir: Path,
    logs_dir: Path,
    state_file: Path,
    current_state_file: Path,
    config_file: Path,
    extra_files: list[Path] | None = None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    name = time.strftime("report_%Y%m%d_%H%M%S", time.localtime()) + ".zip"
    out = (out_dir / name).resolve()

    meta: dict[str, Any] = {
        "generated_utc": _utc_iso(),
        "app_version": __version__,
        "os": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "python": platform.python_version(),
    }

    # Optional: add network snapshot (best-effort, masked).
    try:
        import sys

        if os.name == "nt":
            import subprocess

            import locale

            def _run(cmd: list[str]) -> str:
                # Windows console tools often use OEM code page (cp866 for RU).
                # Use bytes mode + best-effort decoding.
                p = subprocess.run(cmd, check=False, capture_output=True, text=False)
                preferred = locale.getpreferredencoding(False) or "utf-8"
                out, enc_out = decode_bytes_best_effort(p.stdout or b"", preferred=preferred)
                err, enc_err = decode_bytes_best_effort(p.stderr or b"", preferred=preferred)
                combined = out + ("\n" + err if err else "")
                # store encoding hints for triage
                meta.setdefault("network_encoding", {})
                meta["network_encoding"]["preferred"] = preferred
                meta["network_encoding"]["ipconfig"] = enc_out
                meta["network_encoding"]["route_print"] = enc_out
                meta["network_encoding"]["netsh_dns"] = enc_out
                if enc_out != enc_err:
                    meta["network_encoding"]["stderr"] = enc_err
                return combined

            meta["network"] = {
                "ipconfig": mask_secrets(_run(["ipconfig", "/all"])),
                "route_print": mask_secrets(_run(["route", "print"])),
                "netsh_dns": mask_secrets(_run(["netsh", "interface", "ip", "show", "dns"])) ,
            }
        else:
            meta["network"] = {"note": f"network snapshot not implemented for os={os.name}"}
    except Exception:
        pass

    # masked config summary
    cfg_text = _read_text(config_file)
    cfg_masked = mask_secrets(cfg_text)

    # masked states
    st_text = _read_text(state_file)
    cur_text = _read_text(current_state_file)
    st_masked = mask_secrets(st_text)
    cur_masked = mask_secrets(cur_text)

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("meta.json", json.dumps(meta, ensure_ascii=False, indent=2))
        z.writestr("config_masked.yaml", str(cfg_masked))
        z.writestr("state_masked.json", str(st_masked))
        z.writestr("current_masked.json", str(cur_masked))
        z.writestr("tree.txt", _tree_text(logs_dir.parent.parent))

        # logs (verbatim, but we still try to mask common secrets in text logs)
        for p in sorted(logs_dir.glob("*.log")):
            z.writestr(f"logs/{p.name}", str(mask_secrets(_read_text(p))))
        for p in sorted(logs_dir.glob("*.jsonl")):
            z.writestr(f"logs/{p.name}", str(mask_secrets(_read_text(p))))

        # results (safe-ish; still masked)
        try:
            results_dir = (logs_dir.parent / "results").resolve()
            if results_dir.exists():
                for p in sorted(results_dir.glob("results_*.txt")):
                    z.writestr(f"results/{p.name}", str(mask_secrets(_read_text(p))))
        except Exception:
            pass

        if extra_files:
            for p in extra_files:
                if not p.exists() or not p.is_file():
                    continue
                z.writestr(f"extra/{p.name}", str(mask_secrets(_read_text(p))))

    return out
