from __future__ import annotations

import logging
import shutil
import tempfile
import zipfile
from pathlib import Path

from app.zapret_manager.core.state import AppState, UpstreamState
from app.zapret_manager.upstreams.http import download, head
from app.zapret_manager.upstreams.sources import RepoZipSource, Source
from app.zapret_manager.utils.fsx import atomic_replace_dir, ensure_empty_dir, safe_extract_zip
from app.zapret_manager.utils.timex import now_utc_iso


log = logging.getLogger(__name__)


def _get_upstream_state(app_state: AppState, name: str) -> UpstreamState:
    if name not in app_state.upstreams:
        app_state.upstreams[name] = UpstreamState()
    return app_state.upstreams[name]


def check_update(source: Source, app_state: AppState) -> tuple[bool, str]:
    if isinstance(source, RepoZipSource):
        r = head(source.zip_url, timeout=20)
        etag = r.headers.get("ETag")
        last_mod = r.headers.get("Last-Modified")
        st = _get_upstream_state(app_state, source.name)
        changed = (etag and etag != st.etag) or (last_mod and last_mod != st.last_modified)
        msg = f"ETag={etag or '-'} Last-Modified={last_mod or '-'}"
        return bool(changed), msg
    return False, "no-check"


def sync_repo_zip(source: RepoZipSource, *, dest_dir: Path, cache_dir: Path, app_state: AppState) -> str:
    """
    Синкит upstream в dest_dir (полная замена).
    Возвращает путь к корневой папке извлечённого архива.
    """
    cache_file = cache_dir / f"{source.owner}_{source.repo}_{source.ref}.zip"
    etag, last_mod = download(source.zip_url, cache_file)

    tmp_root = Path(tempfile.mkdtemp(prefix="zapret_sync_"))
    extracted_root = tmp_root / "extracted"
    extracted_root.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(cache_file, "r") as z:
        safe_extract_zip(z, extracted_root)

    # GitHub zip всегда содержит единственную корневую папку.
    roots = [p for p in extracted_root.iterdir() if p.is_dir()]
    if len(roots) != 1:
        raise RuntimeError(f"Unexpected zip layout for {source.name}: roots={roots}")
    zip_top = roots[0]

    selected = zip_top
    if source.select_subdir:
        cand = zip_top / source.select_subdir
        if not cand.exists():
            raise RuntimeError(
                f"select_subdir not found: {source.select_subdir} in {zip_top}"
            )
        selected = cand

    # NOTE: shutil.copytree requires the destination to NOT exist unless
    # dirs_exist_ok=True. We intentionally keep dirs_exist_ok=False to avoid
    # mixing old/new files, so staging must not exist.
    staging = tmp_root / "staging"
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    shutil.copytree(selected, staging, dirs_exist_ok=False)

    atomic_replace_dir(staging, dest_dir)

    st = _get_upstream_state(app_state, source.name)
    st.etag = etag
    st.last_modified = last_mod
    st.synced_at_utc = now_utc_iso()

    log.info("synced %s to %s", source.name, dest_dir)
    shutil.rmtree(tmp_root, ignore_errors=True)
    return str(dest_dir)

