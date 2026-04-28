from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.upstreams.github_release import GitHubRelease, ReleaseAsset, latest_release, download_asset
from app.zapret_manager.utils.console import safe_print


log = logging.getLogger(__name__)


DEFAULT_REPO = "norfolkavito-maker/Pupupu"


@dataclass(frozen=True)
class AppUpdatePlan:
    repo: str
    current_version: str
    latest_tag: str
    asset: ReleaseAsset
    download_path: Path
    backup_zip: Path
    updater_bat: Path
    lock_file: Path
    update_log: Path


class AppUpdateError(RuntimeError):
    pass


def _split_repo(repo: str) -> tuple[str, str]:
    repo = (repo or "").strip()
    if "/" not in repo:
        raise AppUpdateError(f"invalid github_repo: {repo} (expected owner/repo)")
    owner, name = repo.split("/", 1)
    owner = owner.strip()
    name = name.strip()
    if not owner or not name:
        raise AppUpdateError(f"invalid github_repo: {repo} (expected owner/repo)")
    return owner, name


def _portable_zip_asset(rel: GitHubRelease) -> ReleaseAsset:
    # build.yml publishes DedZapret-portable-<tag>.zip
    tag = (rel.tag or "").strip()
    if not tag:
        raise AppUpdateError("latest release has empty tag")
    want_prefix = f"DedZapret-portable-{tag}"
    for a in rel.assets:
        n = (a.name or "").strip()
        if n.lower().endswith(".zip") and n.startswith(want_prefix):
            return a
    # fallback: pick any *portable*.zip
    for a in rel.assets:
        n = (a.name or "").strip().lower()
        if "portable" in n and n.endswith(".zip"):
            return a
    raise AppUpdateError(f"portable zip asset not found in release {tag}")


def _validate_zip(path: Path) -> None:
    if not path.exists() or path.stat().st_size <= 0:
        raise AppUpdateError(f"downloaded zip missing/empty: {path}")
    try:
        with zipfile.ZipFile(path, "r") as z:
            bad = z.testzip()
            if bad:
                raise AppUpdateError(f"zip is corrupted (bad entry: {bad})")
            # sanity: must contain DedZapret/DedZapret.exe in portable
            names = [n.replace("\\", "/") for n in z.namelist()]
            if not any(n.lower().endswith("dedzapret/dedzapret.exe") for n in names):
                raise AppUpdateError("zip does not look like DedZapret portable bundle (missing DedZapret/DedZapret.exe)")
    except zipfile.BadZipFile as e:
        raise AppUpdateError(f"zip is not a valid zip: {e}")


def _write_update_log(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    text = "\n".join([f"[{ts}] {ln}" for ln in lines]) + "\n"
    path.write_text(text, encoding="utf-8", errors="replace")


def _acquire_lock(lock_file: Path) -> None:
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    if lock_file.exists():
        raise AppUpdateError(f"update is already in progress (lock exists): {lock_file}")
    lock_file.write_text(str(time.time()), encoding="utf-8", errors="replace")


def _release_lock(lock_file: Path) -> None:
    try:
        lock_file.unlink(missing_ok=True)  # type: ignore[arg-type]
    except Exception:
        pass


def _backup_dedzapret_data(ctx: AppContext, *, update_log: Path) -> Path:
    data_root = ctx.paths.data_root.resolve()
    backups_dir = (data_root / "backups" / "app_update").resolve()
    backups_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    out = (backups_dir / f"{ts}_DedZapretData.zip").resolve()
    # shutil.make_archive wants path without extension
    base = str(out)[:-4] if str(out).lower().endswith(".zip") else str(out)
    # NOTE: make_archive returns full path with .zip
    zip_path = Path(shutil.make_archive(base, "zip", root_dir=str(data_root))).resolve()
    _write_update_log(update_log, [f"backup created: {zip_path}"])
    return zip_path


def build_update_plan(ctx: AppContext, *, github_repo: str = DEFAULT_REPO) -> AppUpdatePlan:
    from app.zapret_manager import __version__

    owner, repo = _split_repo(github_repo)
    rel = latest_release(owner, repo)
    if not rel.tag:
        raise AppUpdateError("latest release not found")
    asset = _portable_zip_asset(rel)

    # download into cache
    ctx.paths.cache_dir.mkdir(parents=True, exist_ok=True)
    download_path = (ctx.paths.cache_dir / asset.name).resolve()

    update_log = (ctx.paths.logs_dir / "update.log").resolve()
    lock_file = (ctx.paths.data_root / "update.lock").resolve()
    updater_bat = (ctx.paths.data_root / "updater.bat").resolve()
    # backup path will be computed during run (timestamped), but keep placeholder dir
    backup_zip = (ctx.paths.data_root / "backups" / "app_update" / "PENDING.zip").resolve()

    return AppUpdatePlan(
        repo=f"{owner}/{repo}",
        current_version=str(__version__),
        latest_tag=str(rel.tag),
        asset=asset,
        download_path=download_path,
        backup_zip=backup_zip,
        updater_bat=updater_bat,
        lock_file=lock_file,
        update_log=update_log,
    )


def generate_updater_bat(*, root_dir: Path, zip_path: Path, log_path: Path) -> str:
    """Generate updater.bat.

    It will:
    - unpack zip into temp dir
    - robocopy everything except DedZapretData to root_dir
    - start DedZapret.exe
    """
    root = str(root_dir)
    z = str(zip_path)
    log = str(log_path)
    # We rely on powershell Expand-Archive (available on Win10/11).
    return "\r\n".join(
        [
            "@echo off",
            "setlocal enableextensions",
            f"set ROOT={root}",
            f"set ZIP={z}",
            f"set LOG={log}",
            "echo [updater] starting >> \"%LOG%\"",
            "set TMP=%TEMP%\\DedZapretUpdate_%RANDOM%_%RANDOM%",
            "mkdir \"%TMP%\" 2>nul",
            "echo [updater] extracting zip to %TMP% >> \"%LOG%\"",
            "powershell -NoProfile -Command \"Expand-Archive -Force '%ZIP%' '%TMP%'\" >> \"%LOG%\" 2>&1",
            "if errorlevel 1 (echo [updater] ERROR: Expand-Archive failed >> \"%LOG%\" & exit /b 2)",
            "set SRC=%TMP%\\DedZapret",
            "if not exist \"%SRC%\\DedZapret.exe\" (echo [updater] ERROR: missing %SRC%\\DedZapret.exe >> \"%LOG%\" & exit /b 3)",
            "echo [updater] copying app files (excluding DedZapretData) >> \"%LOG%\"",
            "robocopy \"%SRC%\" \"%ROOT%\\DedZapret\" /E /NFL /NDL /NJH /NJS /NC /NS /NP /XD DedZapretData >> \"%LOG%\"",
            "echo [updater] starting new app >> \"%LOG%\"",
            "start \"\" \"%ROOT%\\DedZapret\\DedZapret.exe\"",
            "echo [updater] done >> \"%LOG%\"",
            "rmdir /S /Q \"%TMP%\" 2>nul",
            "exit /b 0",
        ]
    )


def run_update(ctx: AppContext, *, github_repo: str = DEFAULT_REPO) -> AppUpdatePlan:
    """Prepare update and launch updater.bat.

    This function does NOT try to overwrite running exe itself.
    It writes updater.bat into DedZapretData and starts it.
    """
    # Must not even start downloads/backups on non-Windows.
    if os.name != "nt":
        raise AppUpdateError("self-update is Windows-only")

    plan = build_update_plan(ctx, github_repo=github_repo)

    # lock
    _acquire_lock(plan.lock_file)
    try:
        _write_update_log(plan.update_log, [f"update requested (repo={plan.repo})", f"current={plan.current_version}", f"latest={plan.latest_tag}"])

        # download
        download_asset(plan.asset, plan.download_path)
        _write_update_log(plan.update_log, [f"downloaded: {plan.download_path}"])

        # zip validation
        _validate_zip(plan.download_path)
        _write_update_log(plan.update_log, ["zip validated OK"])

        # mandatory backup
        backup_zip = _backup_dedzapret_data(ctx, update_log=plan.update_log)
        if not backup_zip.exists() or backup_zip.stat().st_size <= 0:
            raise AppUpdateError("DedZapretData backup failed (zip missing/empty)")

        # write updater
        # Avoid Path.resolve() here: on some environments it may behave differently
        # depending on platform path flavor. Root is already absolute in portable mode.
        txt = generate_updater_bat(root_dir=ctx.paths.root, zip_path=plan.download_path, log_path=plan.update_log)
        plan.updater_bat.write_text(txt, encoding="utf-8", errors="replace")
        _write_update_log(plan.update_log, [f"updater written: {plan.updater_bat}"])

        # start updater and exit current app
        subprocess.Popen(["cmd", "/c", str(plan.updater_bat)], cwd=str(ctx.paths.root))
        _write_update_log(plan.update_log, ["updater started"])

        safe_print("\nОбновление запущено. Текущее окно DedZapret можно закрыть.\n")
        return plan
    except Exception as e:
        _write_update_log(plan.update_log, [f"ERROR: {type(e).__name__}: {e}"])
        raise
    finally:
        # release lock so user can retry if updater didn't start
        _release_lock(plan.lock_file)
