from __future__ import annotations

import hashlib
import json
import platform
import shutil
import zipfile
from pathlib import Path

from zapret_manager.core.app_context import AppContext
from zapret_manager.utils.fsx import safe_extract_zip
from zapret_manager.utils.timex import now_utc_iso


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def create_dump(ctx: AppContext) -> Path:
    """
    Создаёт "дамп" для обмена:
    - конфиги/стейт/стратегии/листы/результаты/логи
    - манифест runtime с sha256 (без бинарей по умолчанию)
    """
    dumps_dir = ctx.paths.data_dir / "dumps"
    dumps_dir.mkdir(parents=True, exist_ok=True)
    out = dumps_dir / f"dump_{now_utc_iso().replace(':','-')}.zip"

    info = {
        "created_at_utc": now_utc_iso(),
        "platform": platform.platform(),
        "python": platform.python_version(),
    }

    runtime_manifest = []
    runtime_root = (ctx.root / ctx.config.zapret.runtime_dir).resolve()
    if runtime_root.exists():
        for p in sorted(runtime_root.rglob("*")):
            if p.is_file():
                runtime_manifest.append(
                    {
                        "path": str(p.relative_to(runtime_root)).replace("\\", "/"),
                        "size": p.stat().st_size,
                        "sha256": _sha256_file(p),
                    }
                )

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("dump_info.json", json.dumps(info, ensure_ascii=False, indent=2))
        z.writestr(
            "runtime_manifest.json",
            json.dumps({"runtime_root": str(runtime_root), "files": runtime_manifest}, ensure_ascii=False, indent=2),
        )

        def add_if_exists(path: Path, arcname: str) -> None:
            if path.exists() and path.is_file():
                z.write(path, arcname=arcname)

        add_if_exists(ctx.paths.config_file, "config.yaml")
        add_if_exists(ctx.paths.sources_file, "sources.yaml")
        add_if_exists(ctx.paths.state_file, "data/state.json")

        # strategies + results + logs + upstream lists
        for base, arc_base in [
            (ctx.paths.strategies_generated_dir, "data/strategies/generated"),
            (ctx.paths.strategies_custom_dir, "data/strategies/custom"),
            (ctx.paths.results_dir, "data/results"),
            (ctx.paths.logs_dir, "data/logs"),
            (ctx.paths.upstreams_dir / "flowseal", "data/upstreams/flowseal"),
        ]:
            if not base.exists():
                continue
            for p in base.rglob("*"):
                if not p.is_file():
                    continue
                # avoid bundling big binaries from upstream accidentally
                if p.suffix.lower() in {".exe", ".sys", ".dll"}:
                    continue
                rel = p.relative_to(base)
                z.write(p, arcname=str(Path(arc_base) / rel))

    return out


def extract_dump(ctx: AppContext, dump_zip: Path) -> Path:
    """
    Распаковывает дамп в data/imported_dumps/<zip_stem>/ и возвращает путь.
    Ничего не применяет автоматически.
    """
    if not dump_zip.exists():
        raise FileNotFoundError(dump_zip)
    dest = ctx.paths.data_dir / "imported_dumps" / dump_zip.stem
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dump_zip, "r") as z:
        safe_extract_zip(z, dest)
    return dest

