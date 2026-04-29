from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import requests

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.upstreams.github_release import GitHubRelease, ReleaseAsset, latest_release, download_asset
from app.zapret_manager.utils.console import safe_print


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReleaseInfo:
    tag: str
    assets: list[ReleaseAsset]
    is_prerelease: bool


@dataclass(frozen=True)
class AppUpdatePlanV2:
    repo: str
    current_version: str
    selected_release: ReleaseInfo
    asset: ReleaseAsset
    download_path: Path
    backup_zip: Path
    updater_bat: Path
    lock_file: Path
    update_log: Path
    release_type: Literal["stable", "test", "manual"]


class AppUpdateV2Error(RuntimeError):
    pass


# Release types and their GitHub API query
RELEASE_TYPES = {
    "stable": "latest",
    "test": "latest?prerelease=true",
    "manual": "all?per_page=100"
}


def _is_windows() -> bool:
    # Keep OS detection behind a function so tests can patch it without
    # mutating global os.name (which breaks pathlib on non-Windows runners).
    return os.name == "nt"


def _get_all_releases(owner: str, repo: str) -> list[GitHubRelease]:
    """Get all releases from GitHub API (for manual selection)."""
    releases = []
    page = 1
    while True:
        api = f"https://api.github.com/repos/{owner}/{repo}/releases?page={page}&per_page=100"
        r = requests.get(api, timeout=30)
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        releases_data = []
        for rel_data in data:
            assets = []
            for a in rel_data.get("assets") or []:
                assets.append(
                    ReleaseAsset(
                        name=str(a.get("name") or ""),
                        url=str(a.get("browser_download_url") or ""),
                        size=int(a.get("size") or 0),
                    )
                )
            releases_data.append(
                GitHubRelease(
                    tag=str(rel_data.get("tag_name") or ""),
                    assets=assets,
                )
            )
        releases.extend(releases_data)
        page += 1
    return releases


def build_update_plan_v2(ctx: AppContext, *, github_repo: str = "norfolkavito-maker/Pupupu", release_type: Literal["stable", "test", "manual"] = "stable") -> AppUpdatePlanV2:
    from app.zapret_manager import __version__

    owner, repo = github_repo.split("/", 1) if "/" in github_repo else (None, None)
    if not owner or not repo:
        raise AppUpdateV2Error(f"invalid github_repo: {github_repo}")

    if release_type == "manual":
        releases = _get_all_releases(owner, repo)
        # For manual selection we will return first 10 releases for UI selection
        selected_release = releases[0] if releases else None
    elif release_type == "test":
        # Get latest including pre-releases
        releases = _get_all_releases(owner, repo)
        selected_release = next((r for r in releases), None)
    else:
        # Stable: official latest release
        selected_release = latest_release(owner, repo)

    if not selected_release:
        raise AppUpdateV2Error("no releases found")

    # Find portable zip asset
    asset = None
    tag = selected_release.tag
    want_prefix = f"DedZapret-portable-{tag}"
    for a in selected_release.assets:
        n = a.name.lower()
        if n.endswith(".zip") and (want_prefix in a.name or "portable" in n):
            asset = a
            break

    if not asset:
        raise AppUpdateV2Error(f"portable zip not found in release {tag}")

    ctx.paths.cache_dir.mkdir(parents=True, exist_ok=True)

    return AppUpdatePlanV2(
        repo=github_repo,
        current_version=str(__version__),
        selected_release=ReleaseInfo(
            tag=selected_release.tag,
            assets=selected_release.assets,
            is_prerelease=release_type == "test"
        ),
        asset=asset,
        download_path=(ctx.paths.cache_dir / asset.name).resolve(),
        backup_zip=(ctx.paths.data_root / "backups" / "app_update" / "pending.zip").resolve(),
        updater_bat=(ctx.paths.data_root / "updater_v2.bat").resolve(),
        lock_file=(ctx.paths.data_root / "update_v2.lock").resolve(),
        update_log=(ctx.paths.logs_dir / "update_v2.log").resolve(),
        release_type=release_type
    )


def generate_updater_bat_v2(*, root_dir: Path, zip_path: Path, log_path: Path) -> str:
    """
    GENERATE UPDATER V2 WITH PROCESS WAITING AND LOCK RETRY
    This bat will run OUTSIDE app folder, wait for DedZapret.exe to exit, then replace files
    """
    root = str(root_dir)
    z = str(zip_path)
    log = str(log_path)

    return "\r\n".join(
        [
            "@echo off",
            "setlocal enableextensions",
            f"set ROOT={root}",
            f"set ZIP={z}",
            f"set LOG={log}",
            "set TMP=%TEMP%\\DedZapretUpdate_%RANDOM%_%RANDOM%",
            "",
            "echo [updater] starting > \"%LOG%\"",
            "mkdir \"%TMP%\" 2>nul",
            "",
            "echo [updater] waiting for DedZapret.exe to exit... >> \"%LOG%\"",
            ":waitloop",
            "tasklist /FI \"IMAGENAME eq DedZapret.exe\" 2>NUL | find /I /N \"DedZapret.exe\">NUL",
            "if \"%ERRORLEVEL%\"==\"0\" (timeout /t 1 /nobreak >nul & goto waitloop)",
            "",
            "echo [updater] extracting zip >> \"%LOG%\"",
            "powershell -NoProfile -Command \"Expand-Archive -Force '%ZIP%' '%TMP%'\" >> \"%LOG%\" 2>&1",
            "if errorlevel 1 (echo ERROR: Expand-Archive failed >> \"%LOG%\" & exit /b 2)",
            "",
            "set SRC=%TMP%\\DedZapret",
            "if not exist \"%SRC%\\DedZapret.exe\" (echo ERROR: missing DedZapret.exe >> \"%LOG%\" & exit /b 3)",
            "",
            "echo [updater] copying files... >> \"%LOG%\"",
            "",
            "REM Robocopy with retry for locked files",
            "set RETRIES=10",
            ":copyloop",
            "robocopy \"%SRC%\" \"%ROOT%\" /E /NFL /NDL /NJH /NJS /NC /NS /NP /XD DedZapretData /R:5 /W:1 >> \"%LOG%\"",
            "set EC=%ERRORLEVEL%",
            "if %EC% GEQ 8 (set /a RETRIES-=1 & if %RETRIES% GTR 0 (timeout /t 1 /nobreak >nul & goto copyloop))",
            "",
            "echo [updater] starting new version >> \"%LOG%\"",
            "start \"\" \"%ROOT%\\DedZapret.exe\"",
            "",
            "echo [updater] done >> \"%LOG%\"",
            "rmdir /S /Q \"%TMP%\" 2>nul",
            "exit /b 0",
        ]
    )


def run_update_v2(ctx: AppContext, *, github_repo: str = "norfolkavito-maker/Pupupu", release_type: Literal["stable", "test", "manual"] = "stable") -> AppUpdatePlanV2:
    if not _is_windows():
        raise AppUpdateV2Error("self-update is Windows-only")

    plan = build_update_plan_v2(ctx, github_repo=github_repo, release_type=release_type)

    # Acquire lock
    if plan.lock_file.exists():
        raise AppUpdateV2Error(f"update already in progress: {plan.lock_file}")
    plan.lock_file.write_text(str(time.time()), encoding="utf-8")

    try:
        # Download
        download_asset(plan.asset, plan.download_path)

        # Validate zip with ZIP64 support
        if not plan.download_path.exists() or plan.download_path.stat().st_size <= 0:
            raise AppUpdateV2Error(f"downloaded zip missing: {plan.download_path}")

        with zipfile.ZipFile(plan.download_path, "r", allowZip64=True) as z:
            if z.testzip() is not None:
                raise AppUpdateV2Error("zip file is corrupted")

        # Backup all data
        plan.backup_zip.parent.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        backup_base = str(plan.backup_zip.parent / f"{ts}_DedZapretData")
        backup_path = Path(shutil.make_archive(backup_base, "zip", root_dir=str(ctx.paths.data_root), verbose=0)).resolve()

        # Write updater bat
        txt = generate_updater_bat_v2(root_dir=ctx.paths.root, zip_path=plan.download_path, log_path=plan.update_log)
        plan.updater_bat.write_text(txt, encoding="utf-8")

        # Start updater in detached process and exit
        subprocess.Popen(["cmd", "/c", str(plan.updater_bat)], cwd=str(ctx.paths.root), shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

        safe_print("\n✅ Обновление запущено. Приложение можно закрыть.\n")
        return plan

    except Exception as e:
        raise
    finally:
        plan.lock_file.unlink(missing_ok=True)
