from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from app.zapret_manager.core.app_context import AppContext


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RepairItem:
    name: str
    status: str  # OK|CREATED|COPIED|MISSING
    details: str = ""


def _ensure_empty_file(path: Path) -> RepairItem:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return RepairItem(path.name, "OK", str(path))
    path.write_text("", encoding="utf-8")
    return RepairItem(path.name, "CREATED", str(path))


def _ensure_alias_copy(*, src: Path, dst: Path) -> RepairItem:
    """Ensure dst exists by copying src if needed.

    - If dst exists and non-empty -> OK
    - Else if src exists and non-empty -> COPIED
    - Else -> MISSING
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        if dst.exists() and dst.is_file() and dst.stat().st_size > 0:
            return RepairItem(dst.name, "OK", str(dst))
    except Exception:
        pass

    try:
        if src.exists() and src.is_file() and src.stat().st_size > 0:
            dst.write_bytes(src.read_bytes())
            return RepairItem(dst.name, "COPIED", f"{src} -> {dst}")
    except Exception as e:
        return RepairItem(dst.name, "MISSING", f"failed to copy from {src}: {e}")

    return RepairItem(dst.name, "MISSING", f"no source for alias copy (src={src})")


def _repo_builtin_lists_dir() -> Path:
    # We ship a minimal set of lists in repo under data/lists.
    return (Path(__file__).resolve().parents[3] / "data" / "lists").resolve()


def ensure_base_lists(ctx: AppContext) -> list[RepairItem]:
    """Ensure minimal list assets exist in canonical manager lists dir.

    - Creates DedZapretData/data/lists
    - Copies base lists from repo (if present in this build)
    - Does NOT download from network (safe for unit tests)
    """
    out: list[RepairItem] = []
    target = ctx.paths.lists_dir.resolve()
    if not target.exists():
        target.mkdir(parents=True, exist_ok=True)
        out.append(RepairItem("lists_dir", "CREATED", str(target)))
    else:
        out.append(RepairItem("lists_dir", "OK", str(target)))

    src_dir = _repo_builtin_lists_dir()
    base_names = [
        # builtin strategies use these (at least)
        "google.txt",
        "exclude.txt",
        # optional but used by overlays
        "rkn.txt",
    ]

    for name in base_names:
        dest = (target / name).resolve()
        if dest.exists() and dest.stat().st_size > 0:
            out.append(RepairItem(name, "OK", str(dest)))
            continue

        # Prefer an already-present alias file in target (from a bundled runtime)
        # before copying template lists from repo.
        alt_in_target: dict[str, list[str]] = {
            "google.txt": ["list-google.txt"],
            "exclude.txt": ["list-exclude.txt", "hostlist-exclude.txt"],
            "rkn.txt": [],
        }
        for alt in alt_in_target.get(name, []):
            src_alt = (target / alt).resolve()
            try:
                if src_alt.exists() and src_alt.is_file() and src_alt.stat().st_size > 0:
                    dest.write_bytes(src_alt.read_bytes())
                    out.append(RepairItem(name, "COPIED", f"{src_alt} -> {dest}"))
                    break
            except Exception:
                continue
        else:
            # Try to copy from repo assets (dev/source builds).
            candidates = [
                src_dir / name,
                src_dir / f"list-{name}",
            ]
            copied = False
            for c in candidates:
                if c.exists() and c.is_file() and c.stat().st_size > 0:
                    dest.write_bytes(c.read_bytes())
                    out.append(RepairItem(name, "COPIED", f"{c} -> {dest}"))
                    copied = True
                    break
            if copied:
                continue

            out.append(RepairItem(name, "MISSING", f"not found in {target} and no bundled source to copy"))
            continue

        # (If alias copy was used, we already appended COPIED and should continue.)
        continue

    # Strategy compatibility aliases expected by some upstreams/bundles.
    # If one exists, make the other exist too (copy).
    alias_pairs = [
        ("google.txt", "list-google.txt"),
        ("exclude.txt", "list-exclude.txt"),
        ("general.txt", "list-general.txt"),
    ]
    for a, b in alias_pairs:
        pa = (target / a).resolve()
        pb = (target / b).resolve()
        if pa.exists() and not pb.exists():
            out.append(_ensure_alias_copy(src=pa, dst=pb))
        elif pb.exists() and not pa.exists():
            out.append(_ensure_alias_copy(src=pb, dst=pa))

    # Optional user-editable lists / ipsets (must not block startup).
    #
    # Note: validate_winws_command() treats --ipset/--ipset-exclude as required files.
    # An empty file is OK for our use-cases, but the file must exist to avoid
    # WinwsStartError(preflight).
    optional_user_files = [
        "list-general-user.txt",
        "list-exclude-user.txt",
        "ipset-exclude-user.txt",
        # Common upstream file names (keep empty placeholders to satisfy preflight)
        "ipset-exclude.txt",
        "list-ipset-exclude.txt",
        "ipset-all.txt",
        "list-ipset-all.txt",
    ]
    for name in optional_user_files:
        out.append(_ensure_empty_file((target / name).resolve()))

    # ipset alias compatibility pairs.
    ipset_alias_pairs = [
        ("ipset-exclude.txt", "list-ipset-exclude.txt"),
        ("ipset-all.txt", "list-ipset-all.txt"),
    ]
    for a, b in ipset_alias_pairs:
        pa = (target / a).resolve()
        pb = (target / b).resolve()
        if pa.exists() and not pb.exists():
            out.append(_ensure_alias_copy(src=pa, dst=pb))
        elif pb.exists() and not pa.exists():
            out.append(_ensure_alias_copy(src=pb, dst=pa))

    return out


def ensure_fake_assets(ctx: AppContext) -> list[RepairItem]:
    """Ensure required fake *.bin assets are present under runtime/zapret/files/fake.

    Rules:
    - Do NOT create empty fake binaries.
    - If asset is found elsewhere under runtime root, copy into canonical fake dir.
    """
    # Canonical fake dir (Phase 2): DedZapretData/runtime/zapret/files/fake
    # Source material: DedZapretData/data/upstreams/flowseal/bin
    from app.zapret_manager.features.zapret_runtime import zapret_root

    rt_root = ctx.paths.runtime_dir.resolve()
    zr = zapret_root(ctx)
    fake_dir = (zr / "files" / "fake").resolve()
    fake_dir.mkdir(parents=True, exist_ok=True)

    required = [
        # Common QUIC/TLS fakes used by bundled strategies (incl. builtin v3/v8).
        "quic_initial_www_google_com.bin",
        "tls_clienthello_max_ru.bin",
        "tls_clienthello_www_google_com.bin",
        "tls_clienthello_vk_com.bin",
        "tls_clienthello_gosuslugi_ru.bin",
        "4pda.bin",
        "t2.bin",
        # Used by some overlays (e.g. split-seqovl-pattern={FAKE:stun.bin})
        "stun.bin",
    ]

    out: list[RepairItem] = []

    # Prefer canonical flowseal_bin_dir if present on ctx.paths (new Paths resolver)
    flowseal_bin: Path | None = None
    try:
        flowseal_bin = Path(str(ctx.paths.flowseal_bin_dir)).resolve()  # type: ignore[attr-defined]
    except Exception:
        flowseal_bin = None
    if not flowseal_bin:
        # Backward compatibility: ctx.paths may be a minimal namespace with upstreams_dir
        upstreams_dir = getattr(getattr(ctx, "paths", None), "upstreams_dir", None)
        try:
            if upstreams_dir:
                flowseal_bin = (Path(str(upstreams_dir)) / "flowseal" / "bin").resolve()
        except Exception:
            flowseal_bin = None

    def find_anywhere(name: str) -> Path | None:
        # Prefer flowseal bin cache if present (canonical source for Flowseal fakes)
        if flowseal_bin:
            try:
                p = (flowseal_bin / name).resolve()
                if p.is_file() and p.stat().st_size > 0:
                    return p
            except Exception:
                pass
        # search under runtime root first
        try:
            for p in rt_root.rglob(name):
                if p.is_file() and p.stat().st_size > 0:
                    return p
        except Exception:
            pass
        # also search under zapret root (just in case rt_root is huge/different)
        try:
            for p in zr.rglob(name):
                if p.is_file() and p.stat().st_size > 0:
                    return p
        except Exception:
            pass
        return None

    for name in required:
        dst = (fake_dir / name).resolve()
        try:
            if dst.exists() and dst.is_file() and dst.stat().st_size > 0:
                out.append(RepairItem(name, "OK", str(dst)))
                continue
        except Exception:
            pass

        found = find_anywhere(name)
        if found:
            try:
                dst.write_bytes(found.read_bytes())
                out.append(RepairItem(name, "COPIED", f"{found} -> {dst}"))
            except Exception as e:
                out.append(RepairItem(name, "MISSING", f"copy failed: {e}"))
        else:
            out.append(RepairItem(name, "MISSING", "not found anywhere under runtime"))

    return out


def ensure_flowseal_lists(ctx: AppContext) -> list[RepairItem]:
    """Ensure Flowseal list assets exist under canonical manager lists dir.

    We do not download anything. If Flowseal upstream is present, we can copy
    upstream-local lists (e.g. list-general.txt) into DedZapretData/data/lists.
    """

    target = ctx.paths.lists_dir.resolve()
    target.mkdir(parents=True, exist_ok=True)

    # Prefer canonical flowseal_lists_dir if present on ctx.paths (new Paths resolver)
    flowseal_lists: Path | None = None
    try:
        flowseal_lists = Path(str(ctx.paths.flowseal_lists_dir)).resolve()  # type: ignore[attr-defined]
    except Exception:
        flowseal_lists = None
    if not flowseal_lists:
        upstreams_dir = getattr(getattr(ctx, "paths", None), "upstreams_dir", None)
        if not upstreams_dir:
            return []
        flowseal_lists = (Path(str(upstreams_dir)) / "flowseal" / "lists").resolve()
    out: list[RepairItem] = []

    # Minimum required by Flowseal strategies
    required = ["list-general.txt"]
    for name in required:
        dst = (target / name).resolve()
        try:
            if dst.exists() and dst.is_file() and dst.stat().st_size > 0:
                out.append(RepairItem(name, "OK", str(dst)))
                continue
        except Exception:
            pass

        src = (flowseal_lists / name).resolve() if flowseal_lists else (target / name).resolve()
        try:
            if src.exists() and src.is_file() and src.stat().st_size > 0:
                dst.write_bytes(src.read_bytes())
                out.append(RepairItem(name, "COPIED", f"{src} -> {dst}"))
                continue
        except Exception as e:
            out.append(RepairItem(name, "MISSING", f"copy failed: {e}"))
            continue

        out.append(RepairItem(name, "MISSING", f"not found in flowseal upstream lists ({flowseal_lists})"))

    return out


def repair_runtime_assets(ctx: AppContext) -> list[RepairItem]:
    """High-level repair action used by UI/diagnostics."""
    out: list[RepairItem] = []
    out.extend(ensure_base_lists(ctx))
    out.extend(ensure_flowseal_lists(ctx))
    out.extend(ensure_fake_assets(ctx))
    out.extend(ensure_winws2_binary(ctx))
    return out


def ensure_winws2_binary(ctx: AppContext) -> list[RepairItem]:
    """Best-effort ensure winws2.exe exists if it is present somewhere under runtime.

    Guardrails:
    - Do NOT download anything.
    - Do NOT create empty exe.
    - Only copy an existing non-empty winws2.exe into canonical zapret root.
    """
    from app.zapret_manager.features.zapret_runtime import zapret_root

    rt_root = ctx.paths.runtime_dir.resolve()
    zr = zapret_root(ctx)
    dst = (zr / "winws2.exe").resolve()

    try:
        if dst.exists() and dst.is_file() and dst.stat().st_size > 0:
            return [RepairItem("winws2.exe", "OK", str(dst))]
    except Exception:
        pass

    found: Path | None = None
    try:
        for p in rt_root.rglob("winws2.exe"):
            try:
                if p.is_file() and p.stat().st_size > 0:
                    found = p
                    break
            except Exception:
                continue
    except Exception:
        found = None

    if found:
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(found.read_bytes())
            return [RepairItem("winws2.exe", "COPIED", f"{found} -> {dst}")]
        except Exception as e:
            return [RepairItem("winws2.exe", "MISSING", f"copy failed: {e}")]

    return [RepairItem("winws2.exe", "MISSING", "not found anywhere under runtime")]
