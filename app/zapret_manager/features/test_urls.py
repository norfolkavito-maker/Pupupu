from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable

import requests

from zapret_manager.features.url_check import UrlCheck


RAW_SUITE_URL = "https://raw.githubusercontent.com/hyperion-cs/dpi-checkers/refs/heads/main/ru/tcp-16-20/suite.v2.json"


DEFAULT_DOMAINS = [
    "https://gosuslugi.ru/",
    "https://esia.gosuslugi.ru/",
    "https://nalog.ru/",
    "https://rutube.ru/",
    "https://ntc.party/",
    "https://instagram.com/",
    "https://facebook.com/",
    "https://rutor.info/",
    "https://rutracker.org/",
    "https://openwrt.org/",
    "https://discord.com/",
    "https://x.com/",
    "https://flightradar24.com/",
    "https://play.google.com/",
    "https://kinozal.tv/",
]


def prepare_urls(*, include_suite: bool = True, timeout_s: int = 15) -> list[UrlCheck]:
    urls: list[str] = list(DEFAULT_DOMAINS)
    if include_suite:
        try:
            r = requests.get(RAW_SUITE_URL, timeout=timeout_s)
            r.raise_for_status()
            data = r.json()
            # best-effort: suite.v2.json contains list of tests; each has url or urls
            for t in data.get("tests", []) if isinstance(data, dict) else []:
                if isinstance(t, dict):
                    u = t.get("url")
                    if isinstance(u, str) and u.startswith("http"):
                        urls.append(u)
        except Exception:
            pass

    # dedup while preserving order
    seen = set()
    out: list[UrlCheck] = []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        out.append(UrlCheck(name=u, url=u))
    return out

