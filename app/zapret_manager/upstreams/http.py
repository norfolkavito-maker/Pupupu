from __future__ import annotations

import logging
import os
from pathlib import Path
from urllib.parse import urlparse

import requests


log = logging.getLogger(__name__)


def head(url: str, *, timeout: int = 20) -> requests.Response:
    return requests.head(url, allow_redirects=True, timeout=timeout)


def download(url: str, dest: Path, *, timeout: int = 120) -> tuple[str | None, str | None]:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise RuntimeError(f"Only HTTPS downloads are allowed: {url}")

    dest.parent.mkdir(parents=True, exist_ok=True)
    log.info("download: %s -> %s", url, dest)

    tmp = dest.with_suffix(dest.suffix + ".tmp")
    if tmp.exists():
        tmp.unlink()

    with requests.get(url, stream=True, timeout=timeout, allow_redirects=True) as r:
        r.raise_for_status()
        etag = r.headers.get("ETag")
        last_mod = r.headers.get("Last-Modified")
        with tmp.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)
    os.replace(tmp, dest)
    return etag, last_mod

