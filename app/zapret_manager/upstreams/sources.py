from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class RepoZipSource:
    name: str
    owner: str
    repo: str
    ref: str
    select_subdir: str | None = None

    @property
    def zip_url(self) -> str:
        # codeload is stable and fast for zip downloads
        return f"https://codeload.github.com/{self.owner}/{self.repo}/zip/refs/heads/{self.ref}"


@dataclass(frozen=True)
class RawUrlSource:
    name: str
    url: str


Source = RepoZipSource | RawUrlSource


def load_sources(path: Path) -> dict[str, Source]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out: dict[str, Source] = {}
    sources = data.get("sources", {}) or {}
    for name, s in sources.items():
        kind = str(s.get("kind", "")).strip()
        if kind == "repo_zip":
            out[name] = RepoZipSource(
                name=name,
                owner=str(s["owner"]),
                repo=str(s["repo"]),
                ref=str(s.get("ref", "main")),
                select_subdir=str(s.get("select_subdir")) if s.get("select_subdir") else None,
            )
        elif kind == "raw_url":
            out[name] = RawUrlSource(name=name, url=str(s["url"]))
        else:
            raise ValueError(f"Unknown source kind for {name}: {kind}")
    return out

