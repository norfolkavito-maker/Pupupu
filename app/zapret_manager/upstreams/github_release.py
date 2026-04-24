from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import requests

from zapret_manager.upstreams.http import download


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    url: str  # browser_download_url
    size: int


@dataclass(frozen=True)
class GitHubRelease:
    tag: str
    assets: list[ReleaseAsset]


def latest_release(owner: str, repo: str, *, timeout: int = 20) -> GitHubRelease:
    api = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    r = requests.get(api, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    assets = []
    for a in data.get("assets") or []:
        assets.append(
            ReleaseAsset(
                name=str(a.get("name") or ""),
                url=str(a.get("browser_download_url") or ""),
                size=int(a.get("size") or 0),
            )
        )
    return GitHubRelease(tag=str(data.get("tag_name") or ""), assets=assets)


def download_asset(asset: ReleaseAsset, dest: Path) -> Path:
    download(asset.url, dest)
    if asset.size and dest.exists() and dest.stat().st_size != asset.size:
        dest.unlink(missing_ok=True)  # type: ignore[arg-type]
        raise RuntimeError(f"Downloaded asset size mismatch for {asset.name}")
    return dest

