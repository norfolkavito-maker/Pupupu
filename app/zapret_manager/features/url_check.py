from __future__ import annotations

import logging
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Iterable

from zapret_manager.utils.subprocessx import run


log = logging.getLogger(__name__)


DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) curl/8.0"


@dataclass(frozen=True)
class UrlCheck:
    name: str
    url: str


def curl_path() -> str:
    p = shutil.which("curl")
    return p or "curl"


def check_url(url: str, *, connect_timeout: int = 4, max_time: int = 6) -> bool:
    """
    Best-effort аналог StressOzz check_url(): "успешно" если код 2xx-4xx и curl не упал.
    """
    args = [
        curl_path(),
        "-L",
        "-k",
        "-sS",
        "--connect-timeout",
        str(connect_timeout),
        "--max-time",
        str(max_time),
        "--speed-time",
        "3",
        "--speed-limit",
        "1",
        "--range",
        "0-65535",
        "-A",
        DEFAULT_UA,
        "-o",
        "NUL",
        "-w",
        "%{http_code}",
        url,
    ]
    r = run(args, check=False, capture=True)
    code = (r.out or "").strip()[-3:]
    try:
        n = int(code)
    except Exception:
        return False
    return 200 <= n < 500


def check_all(urls: Iterable[UrlCheck], *, parallel: int = 8) -> tuple[int, int]:
    ok = 0
    total = 0
    with ThreadPoolExecutor(max_workers=parallel) as ex:
        futs = {}
        for u in urls:
            if not u.url:
                continue
            total += 1
            futs[ex.submit(check_url, u.url)] = u
        for f in as_completed(futs):
            try:
                if f.result():
                    ok += 1
            except Exception:
                pass
    return ok, total

