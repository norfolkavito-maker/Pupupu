from __future__ import annotations

import json
import os
import platform
import secrets
import sys
import time
import traceback
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from app.zapret_manager import __version__


def _utc_iso() -> str:
    # ISO without microseconds for readability.
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _truncate_text(s: str, limit: int) -> str:
    if limit <= 0:
        return ""
    if len(s) <= limit:
        return s
    return s[:limit] + f"... <truncated {len(s) - limit} chars>"


def _maybe_redact_paths(text: str) -> str:
    # Best-effort path redaction.
    # We keep only drive letter + "..." or "..." for unix paths.
    # This is intentionally simple: user asked to log everything, but we still
    # support optional redaction.
    import re

    # Windows: C:\Users\name\... -> C:\...\...
    text = re.sub(r"([A-Za-z]:\\)(?:[^\s\"']+\\){2,}", r"\1...\\", text)
    # Unix: /Users/name/... -> /.../
    text = re.sub(r"/(?:[^\s\"']+/){2,}", r"/.../", text)
    return text


def detect_git_commit() -> str:
    # Portable builds may not ship .git; in that case we return empty.
    # In dev runs this helps correlate session with exact source revision.
    # Preferred: env var injected at build time.
    # We can set this from CI/pyinstaller without relying on .git being present.
    env = os.environ.get("DEDZAPRET_GIT_COMMIT") or os.environ.get("GITHUB_SHA")
    if env:
        return env.strip()

    try:
        import subprocess

        p = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if p.returncode == 0:
            return (p.stdout or "").strip()
    except Exception:
        return ""
    return ""


@dataclass(frozen=True)
class SessionMeta:
    session_id: str
    started_utc: str
    app_version: str
    git_commit: str
    python: str
    os: str


class SessionRecorder:
    """Opt-in recorder for 'log everything' debugging sessions.

    Writes JSONL events and can bundle a report zip on exit.
    """

    def __init__(
        self,
        *,
        logs_dir: Path,
        enabled: bool,
        record_console_io: bool = True,
        record_subprocess: bool = True,
        max_text_len: int = 8000,
        redact_paths: bool = False,
    ) -> None:
        self.enabled = enabled
        self.record_console_io = record_console_io
        self.record_subprocess = record_subprocess
        self.max_text_len = max_text_len
        self.redact_paths = redact_paths
        self.logs_dir = logs_dir
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        sid = time.strftime("%Y%m%d_%H%M%S", time.gmtime()) + "_" + secrets.token_hex(4)
        self.meta = SessionMeta(
            session_id=sid,
            started_utc=_utc_iso(),
            app_version=__version__,
            git_commit=detect_git_commit(),
            python=sys.version.replace("\n", " "),
            os=f"{platform.system()} {platform.release()} ({platform.machine()})",
        )
        self.session_file = self.logs_dir / f"session_{sid}.jsonl"

        if self.enabled:
            # Write meta header line.
            self._write_event(
                category="session.start",
                component="diagnostics",
                payload={"meta": self.meta.__dict__},
            )

    def _sanitize_payload(self, payload: Any) -> Any:
        try:
            raw = json.dumps(payload, ensure_ascii=False, default=str)
        except Exception:
            raw = str(payload)
        raw = _truncate_text(raw, self.max_text_len)
        if self.redact_paths:
            raw = _maybe_redact_paths(raw)
        # store as json string to avoid accidental huge nested structures
        return raw

    def _write_event(self, *, category: str, component: str, payload: Any) -> None:
        if not self.enabled:
            return
        event = {
            "ts": _utc_iso(),
            "session_id": self.meta.session_id,
            "category": category,
            "component": component,
            "app_version": self.meta.app_version,
            "git_commit": self.meta.git_commit,
            "payload": self._sanitize_payload(payload),
        }
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        with self.session_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    # Public API
    def log(self, category: str, component: str, payload: Any) -> None:
        self._write_event(category=category, component=component, payload=payload)

    def log_exception(self, component: str, exc: BaseException) -> None:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        self._write_event(
            category="exception",
            component=component,
            payload={"type": type(exc).__name__, "message": str(exc), "traceback": tb},
        )

    def close(self, *, exit_code: int | None = None) -> None:
        self._write_event(
            category="session.end",
            component="diagnostics",
            payload={"exit_code": exit_code},
        )

    def bundle_report_zip(self, *, crash_log: Optional[Path] = None, app_log: Optional[Path] = None) -> Path:
        """Create zip containing session jsonl + app logs.

        We do not auto-upload. UI will ask and open GitHub issues page.
        """
        out = self.logs_dir / f"report_{self.meta.session_id}.zip"
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
            if self.session_file.exists():
                z.write(self.session_file, arcname=self.session_file.name)
            if crash_log and crash_log.exists():
                z.write(crash_log, arcname=crash_log.name)
            if app_log and app_log.exists():
                z.write(app_log, arcname=app_log.name)
            # Also include minimal meta for quick triage.
            meta_name = f"meta_{self.meta.session_id}.json"
            z.writestr(meta_name, json.dumps(self.meta.__dict__, ensure_ascii=False, indent=2))
        return out


def github_issue_url(*, repo: str, title: str, body: str) -> str:
    # GitHub supports title/body query params.
    from urllib.parse import quote

    repo = repo.strip() or "norfolkavito-maker/Pupupu"
    return (
        f"https://github.com/{repo}/issues/new"
        f"?title={quote(title)}"
        f"&body={quote(body)}"
    )


def open_url(url: str) -> None:
    # Best-effort: open default browser.
    try:
        import webbrowser

        webbrowser.open(url)
        return
    except Exception:
        pass

    try:
        import subprocess

        if sys.platform == "darwin":
            subprocess.run(["open", url], check=False)
        elif os.name == "nt":
            os.startfile(url)  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", url], check=False)
    except Exception:
        return


_global_recorder: SessionRecorder | None = None


def set_global_recorder(rec: SessionRecorder | None) -> None:
    global _global_recorder
    _global_recorder = rec


def get_global_recorder() -> SessionRecorder | None:
    return _global_recorder


def diag_log(category: str, component: str, payload: Any) -> None:
    rec = get_global_recorder()
    if not rec:
        return
    if component == "console" and not getattr(rec, "record_console_io", True):
        return
    if component == "subprocessx" and not getattr(rec, "record_subprocess", True):
        return
    rec.log(category, component, payload)
