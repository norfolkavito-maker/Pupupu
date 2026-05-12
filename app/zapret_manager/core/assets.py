from __future__ import annotations

"""Asset resolution helpers (Phase 2).

This module centralizes how strategy placeholders and file references are mapped
to the canonical portable layout.

Rules:
- User-owned list files MUST resolve from DedZapretData/data/lists.
- Upstream cache (DedZapretData/data/upstreams/*) is read-only source material.
- Fake binary assets MUST resolve from DedZapretData/runtime/zapret/files/fake.
- Controlled repair may copy real fake assets from Flowseal upstream cache.
- Never create empty fake .bin files.
"""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Iterable, Literal

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.zapret_manager.core.app_context import AppContext


AssetKind = Literal["user_list", "list", "ipset", "fake"]


@dataclass(frozen=True)
class AssetCandidate:
    kind: AssetKind
    name: str
    path: Path
    source: str  # e.g. mgr_lists, flowseal_lists, runtime_fake, flowseal_bin

    def exists_nonempty(self) -> bool:
        try:
            return self.path.is_file() and self.path.stat().st_size > 0
        except Exception:
            return False

    def exists_allow_empty(self) -> bool:
        try:
            return self.path.is_file()
        except Exception:
            return False


def _safe_resolve(base: Path, child: str) -> Path:
    """Resolve child under base without allowing path traversal."""
    # Note: `resolve()` will normalize `..`, so we can detect escapes.
    p = (base / child).resolve()
    try:
        p.relative_to(base.resolve())
    except Exception as e:
        raise ValueError(f"path escapes base: {p} (base={base})") from e
    return p


def resolve_user_list(ctx: AppContext, name: str) -> Path:
    """Resolve a user-owned list/ipset file under data/lists."""
    return _safe_resolve(ctx.paths.lists_dir.resolve(), name)


def resolve_fake_asset(ctx: AppContext, name: str) -> Path:
    """Resolve fake asset under runtime/zapret/files/fake."""
    fake_dir = (ctx.paths.zapret_runtime_dir / "files" / "fake").resolve()
    return _safe_resolve(fake_dir, name)


def find_asset_candidates(ctx: AppContext, *, kind: AssetKind, name: str) -> list[AssetCandidate]:
    """Return ordered candidate locations for an asset."""
    out: list[AssetCandidate] = []

    if kind in {"user_list", "list", "ipset"}:
        # Manager working dir is always first.
        out.append(AssetCandidate(kind, name, resolve_user_list(ctx, name), "mgr_lists"))
        # For non-user lists we may also allow upstream-provided lists.
        if kind != "user_list":
            out.append(
                AssetCandidate(
                    kind,
                    name,
                    _safe_resolve(ctx.paths.flowseal_lists_dir.resolve(), name),
                    "flowseal_lists",
                )
            )
        return out

    if kind == "fake":
        out.append(AssetCandidate(kind, name, resolve_fake_asset(ctx, name), "runtime_fake"))
        # controlled source material: Flowseal upstream bin
        out.append(
            AssetCandidate(kind, name, _safe_resolve(ctx.paths.flowseal_bin_dir.resolve(), name), "flowseal_bin")
        )
        return out

    return out


def validate_asset_exists(ctx: AppContext, *, kind: AssetKind, name: str) -> tuple[bool, str, Path | None]:
    """Validate an asset.

    Returns (ok, status, resolved_path).
    status:
      - OK
      - OK_EMPTY_ALLOWED
      - MISSING
      - INVALID_EMPTY_FAKE
    """
    cands = find_asset_candidates(ctx, kind=kind, name=name)
    for c in cands:
        if kind == "fake":
            if c.exists_nonempty():
                return True, "OK", c.path
            if c.path.exists() and c.path.is_file():
                try:
                    if c.path.stat().st_size == 0:
                        return False, "INVALID_EMPTY_FAKE", c.path
                except Exception:
                    pass
            continue

        # lists/ipset: empty is allowed for user-owned files.
        if c.exists_allow_empty():
            try:
                if c.path.stat().st_size == 0 and kind in {"user_list", "ipset"}:
                    return True, "OK_EMPTY_ALLOWED", c.path
            except Exception:
                pass
            return True, "OK", c.path

    return False, "MISSING", (cands[0].path if cands else None)


def expand_placeholders(ctx: AppContext, arg: str) -> str:
    """Expand known placeholders using canonical Paths + asset resolver.

    Supported:
    - {DATA}, {RUNTIME}
    - {LISTS}, {MGR_LISTS}
    - {FLOWSEAL_LISTS}, {FLOWSEAL_BIN}
    - {FAKE}
    - {FAKE:filename.bin} -> resolved candidate (runtime fake preferred)
    """
    s = str(arg)
    sep = "\\" if os.name == "nt" else "/"
    # base placeholders
    s = s.replace("{DATA}", str(ctx.paths.data_dir.resolve()) + sep)
    s = s.replace("{RUNTIME}", str(ctx.paths.runtime_dir.resolve()) + sep)
    s = s.replace("{LISTS}", str(ctx.paths.lists_dir.resolve()) + sep)
    s = s.replace("{MGR_LISTS}", str(ctx.paths.lists_dir.resolve()) + sep)
    s = s.replace("{FLOWSEAL_LISTS}", str(ctx.paths.flowseal_lists_dir.resolve()) + sep)
    s = s.replace("{FLOWSEAL_BIN}", str(ctx.paths.flowseal_bin_dir.resolve()) + sep)
    s = s.replace("{FAKE}", str((ctx.paths.zapret_runtime_dir / "files" / "fake").resolve()) + sep)

    # {FAKE:...} expansion
    if "{FAKE:" not in s:
        return s

    import re

    def repl(m: re.Match[str]) -> str:
        name = m.group(1)
        # prefer runtime fake, else flowseal bin, else just name
        for c in find_asset_candidates(ctx, kind="fake", name=name):
            if c.exists_nonempty():
                return str(c.path)
        return name

    return re.sub(r"\{FAKE:([^}]+)\}", repl, s)
