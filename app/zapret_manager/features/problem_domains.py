"""Problem domains canonical storage (v2).

This module is the single entry point for reading/writing
`DedZapretData/data/problem_domains.json`.

Key goals:
- backward compatible loader (old list-format -> migrate);
- never lose user data without a backup;
- tolerate corrupted JSON (backup + reset);
- provide summary artifacts suitable for GUI/tray and bug reports.
"""

from __future__ import annotations

import logging
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.zapret_manager.utils.jsonx import atomic_write_json

log = logging.getLogger(__name__)

_SCHEMA_VERSION = 2
_PROBLEM_DOMAINS_FILE = "problem_domains.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_any_iso(s: str) -> datetime | None:
    s = (s or "").strip()
    if not s:
        return None
    try:
        # tolerate both ...Z and ...+00:00 and with/without microseconds
        if s.endswith("Z"):
            s2 = s[:-1] + "+00:00"
        else:
            s2 = s
        return datetime.fromisoformat(s2)
    except Exception:
        return None


def _fmt_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class ProblemDomainV2:
    domain: str
    first_seen: str
    last_seen: str
    fail_count: int
    last_error: str
    last_strategy: str
    best_strategy: str
    status: str
    notes: str


def _problem_domains_path(ctx) -> Path:
    return (ctx.paths.data_dir / _PROBLEM_DOMAINS_FILE).resolve()


def _backup_copy(src: Path, *, suffix: str) -> Path | None:
    if not src.exists():
        return None
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    dst = src.with_name(src.name + f".{suffix}.{ts}")
    try:
        dst.write_bytes(src.read_bytes())
        return dst
    except Exception:
        return None


def _empty_v2() -> dict[str, Any]:
    return {"schema_version": _SCHEMA_VERSION, "domains": {}}


def _normalize_domain(domain: str) -> str:
    d = (domain or "").strip().lower()
    if not d:
        return ""
    for prefix in ("https://", "http://"):
        if d.startswith(prefix):
            d = d[len(prefix) :]
    return d.strip("/").strip()


def _merge_entry(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
    """Merge src into dst following rules from spec."""
    # timestamps
    dst_first = _parse_any_iso(str(dst.get("first_seen", "")))
    dst_last = _parse_any_iso(str(dst.get("last_seen", "")))
    src_first = _parse_any_iso(str(src.get("first_seen", "")))
    src_last = _parse_any_iso(str(src.get("last_seen", "")))
    first = min([d for d in [dst_first, src_first] if d is not None], default=None)
    last = max([d for d in [dst_last, src_last] if d is not None], default=None)
    if first is None:
        first = datetime.now(timezone.utc)
    if last is None:
        last = first

    # fail_count: sum if both ints >=0 else max
    def _as_int(x: Any) -> int | None:
        try:
            i = int(x)
            return i if i >= 0 else None
        except Exception:
            return None

    a = _as_int(dst.get("fail_count"))
    b = _as_int(src.get("fail_count"))
    if a is not None and b is not None:
        fail_count = a + b
    else:
        fail_count = max([i for i in [a, b] if i is not None], default=1)

    # newest record wins for last_error / last_strategy
    newest_from_src = (src_last or datetime.min.replace(tzinfo=timezone.utc)) >= (dst_last or datetime.min.replace(tzinfo=timezone.utc))
    last_error = str(src.get("last_error", "")) if newest_from_src else str(dst.get("last_error", ""))
    last_strategy = str(src.get("last_strategy", "")) if newest_from_src else str(dst.get("last_strategy", ""))

    best_strategy = str(dst.get("best_strategy") or src.get("best_strategy") or "")
    status = str(dst.get("status") or src.get("status") or "failing")
    notes = str(dst.get("notes") or src.get("notes") or "")

    return {
        "first_seen": _fmt_iso(first),
        "last_seen": _fmt_iso(last),
        "fail_count": fail_count,
        "last_error": last_error,
        "last_strategy": last_strategy,
        "best_strategy": best_strategy,
        "status": status,
        "notes": notes,
    }


def load_problem_domains(ctx) -> dict[str, Any]:
    """Load canonical storage.

    Returns dict with keys: schema_version, domains.
    Can migrate older formats in-place with backups.
    """
    p = _problem_domains_path(ctx)
    if not p.exists():
        return _empty_v2()

    try:
        raw = p.read_text(encoding="utf-8", errors="replace")
        data = json.loads(raw)
    except Exception as e:
        _backup_copy(p, suffix="corrupt")
        log.warning("problem_domains.json corrupted, reset to empty v2: %s", e)
        empty = _empty_v2()
        atomic_write_json(p, empty)
        return empty

    # Already v2
    if isinstance(data, dict) and data.get("schema_version") == _SCHEMA_VERSION and isinstance(data.get("domains"), dict):
        return data

    # Old list-format: list[ProblemDomain]
    if isinstance(data, list):
        _backup_copy(p, suffix="bak")
        migrated = _empty_v2()
        for item in data:
            if not isinstance(item, dict):
                continue
            d = _normalize_domain(str(item.get("domain", "")))
            if not d:
                continue
            # old schema fields
            first_seen = str(item.get("first_seen", ""))
            last_seen = str(item.get("last_seen", ""))
            last_error = str(item.get("last_error", ""))
            # best-effort mapping
            entry = {
                "first_seen": first_seen,
                "last_seen": last_seen,
                "fail_count": 1,
                "last_error": last_error,
                "last_strategy": "",
                "best_strategy": "",
                "status": "failing",
                "notes": "",
            }
            cur = migrated["domains"].get(d) if isinstance(migrated["domains"], dict) else None
            if isinstance(cur, dict):
                migrated["domains"][d] = _merge_entry(cur, entry)
            else:
                migrated["domains"][d] = _merge_entry({}, entry)
        atomic_write_json(p, migrated)
        return migrated

    # Unknown dict format: best-effort migration if safe.
    if isinstance(data, dict) and isinstance(data.get("domains"), dict):
        _backup_copy(p, suffix="bak")
        migrated = _empty_v2()
        for dom, rec in data.get("domains", {}).items():
            d = _normalize_domain(str(dom))
            if not d:
                continue
            if isinstance(rec, dict):
                migrated["domains"][d] = _merge_entry({}, rec)
        atomic_write_json(p, migrated)
        return migrated

    # Unrecognized -> backup + reset.
    _backup_copy(p, suffix="bak")
    empty = _empty_v2()
    atomic_write_json(p, empty)
    return empty


def save_problem_domains(ctx, data: dict[str, Any]) -> None:
    p = _problem_domains_path(ctx)
    if not isinstance(data, dict):
        data = _empty_v2()
    if data.get("schema_version") != _SCHEMA_VERSION:
        data = _empty_v2()
    if not isinstance(data.get("domains"), dict):
        data["domains"] = {}
    atomic_write_json(p, data)


def add_problem_domain(
    ctx,
    domain: str,
    *,
    error: str = "",
    strategy: str = "",
    ts: str | None = None,
) -> None:
    """Add or update one failing domain (dedup by normalized domain)."""
    d = _normalize_domain(domain)
    if not d:
        return
    when = _parse_any_iso(ts or "") or datetime.now(timezone.utc)
    data = load_problem_domains(ctx)
    domains = data.get("domains") if isinstance(data, dict) else None
    if not isinstance(domains, dict):
        data = _empty_v2()
        domains = data["domains"]

    cur = domains.get(d)
    base = cur if isinstance(cur, dict) else {}
    patch = {
        "first_seen": base.get("first_seen") or _fmt_iso(when),
        "last_seen": _fmt_iso(when),
        "fail_count": int(base.get("fail_count") or 0) + 1,
        "last_error": error or str(base.get("last_error", "")),
        "last_strategy": strategy or str(base.get("last_strategy", "")),
        "best_strategy": str(base.get("best_strategy", "")) or "",
        "status": str(base.get("status", "failing")) or "failing",
        "notes": str(base.get("notes", "")) or "",
    }
    domains[d] = _merge_entry(base, patch)
    save_problem_domains(ctx, data)


def add_problem_domains_from_results(ctx, results: list[Any]) -> int:
    """Store failing domains collected from strategy sweep results.

    Returns number of domains added/updated (best-effort).
    """
    added = 0
    ts = _utc_now_iso()
    for r in results or []:
        st = str(getattr(r, "strategy", "") or "")
        checks = getattr(r, "checks", None)
        if not checks:
            continue
        for c in checks:
            ok = bool(getattr(c, "ok", False))
            if ok:
                continue
            dom = str(getattr(c, "domain", "") or "")
            err = str(getattr(c, "error", "") or "")
            if not dom:
                continue
            add_problem_domain(ctx, dom, error=err, strategy=st, ts=ts)
            added += 1
    return added


def get_problem_domain_list(ctx) -> list[str]:
    """Return clean list of domains for test sets."""
    data = load_problem_domains(ctx)
    doms = data.get("domains") if isinstance(data, dict) else None
    if not isinstance(doms, dict):
        return []
    out = []
    for d in sorted(doms.keys()):
        dd = _normalize_domain(d)
        if dd:
            out.append(dd)
    return out


def clear_problem_domains(ctx) -> None:
    data = _empty_v2()
    save_problem_domains(ctx, data)


def export_problem_domains_summary(ctx) -> dict[str, Any]:
    data = load_problem_domains(ctx)
    doms = data.get("domains") if isinstance(data, dict) else None
    if not isinstance(doms, dict):
        doms = {}
    total = len(doms)
    failing = 0
    fixed = 0
    last_seen: str | None = None
    worst: list[dict[str, Any]] = []
    for dom, rec in doms.items():
        if not isinstance(rec, dict):
            continue
        status = str(rec.get("status", "failing"))
        if status == "fixed":
            fixed += 1
        else:
            failing += 1
        ls = str(rec.get("last_seen", ""))
        if ls and (last_seen is None or ls > last_seen):
            last_seen = ls
        worst.append(
            {
                "domain": dom,
                "fail_count": int(rec.get("fail_count") or 0),
                "last_seen": ls,
                "last_error": str(rec.get("last_error", "")),
                "last_strategy": str(rec.get("last_strategy", "")),
                "best_strategy": str(rec.get("best_strategy", "")),
                "status": status,
            }
        )
    worst.sort(key=lambda x: (x.get("fail_count", 0), x.get("last_seen", "")), reverse=True)
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_utc": _utc_now_iso(),
        "total": total,
        "failing": failing,
        "fixed": fixed,
        "last_seen": last_seen,
        "worst": worst[:20],
    }


def format_problem_domains_summary_ru(summary: dict[str, Any]) -> str:
    total = int(summary.get("total") or 0)
    failing = int(summary.get("failing") or 0)
    fixed = int(summary.get("fixed") or 0)
    last_seen = summary.get("last_seen") or "-"
    lines = [
        f"Проблемные домены: всего {total} (failing={failing}, fixed={fixed})",
        f"Последний раз замечены: {last_seen}",
        "",
    ]
    worst = summary.get("worst")
    if isinstance(worst, list) and worst:
        lines.append("Топ проблемных доменов:")
        for i, w in enumerate(worst[:10], start=1):
            if not isinstance(w, dict):
                continue
            dom = w.get("domain")
            fc = w.get("fail_count")
            ls = w.get("last_seen")
            st = w.get("last_strategy") or "-"
            err = w.get("last_error") or "-"
            lines.append(f"{i:02d}. {dom} — fail_count={fc}, last_seen={ls}, last_strategy={st}")
            if err != "-":
                lines.append(f"    last_error: {err}")
    else:
        lines.append("Список пуст.")
    return "\n".join(lines) + "\n"


def write_problem_domains_summary_artifacts(ctx) -> list[Path]:
    out_dir = (ctx.paths.data_dir / "diagnostics").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = export_problem_domains_summary(ctx)
    p_json = out_dir / "problem_domains_summary.json"
    p_txt = out_dir / "problem_domains_summary.txt"
    atomic_write_json(p_json, summary)
    p_txt.write_text(format_problem_domains_summary_ru(summary), encoding="utf-8")
    return [p_json, p_txt]


def remove_resolved_domain(ctx, domain: str) -> None:
    """Mark domain as fixed (keeps history)."""
    d = _normalize_domain(domain)
    if not d:
        return
    data = load_problem_domains(ctx)
    doms = data.get("domains") if isinstance(data, dict) else None
    if not isinstance(doms, dict):
        return
    rec = doms.get(d)
    if not isinstance(rec, dict):
        return
    rec = dict(rec)
    rec["status"] = "fixed"
    doms[d] = rec
    save_problem_domains(ctx, data)


# Backward-compat alias for callers in older code.
def get_problem_domains(ctx) -> list[str]:
    return get_problem_domain_list(ctx)


def problem_domains_summary(ctx) -> str:
    return format_problem_domains_summary_ru(export_problem_domains_summary(ctx))