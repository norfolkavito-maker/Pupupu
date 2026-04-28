"""Problem domains tracker for DedZapret.

Captures domains that fail tests (control or strategy) and provides
them as a special domain set for quick auto-tune and proof-of-effect.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.zapret_manager.core.state import AppState, load_state, save_state

log = logging.getLogger(__name__)

# File stored alongside state.json
_PROBLEM_DOMAINS_FILE = "problem_domains.json"


@dataclass
class ProblemDomain:
    """One problem domain record."""

    domain: str
    first_seen: str  # ISO UTC
    last_seen: str  # ISO UTC
    fail_reason: str  # control_fail, strategy_fail, dns_fail, tcp_fail, http_fail, ping_fail, timeout
    source: str  # control | strategy
    last_error: str = ""


def _problem_domains_path(ctx) -> Path:
    return ctx.paths.state_file.parent / _PROBLEM_DOMAINS_FILE


def load_problem_domains(ctx) -> list[ProblemDomain]:
    p = _problem_domains_path(ctx)
    if not p.exists():
        return []
    try:
        text = p.read_text(encoding="utf-8")
        data = json.loads(text)
        out: list[ProblemDomain] = []
        for item in data:
            out.append(
                ProblemDomain(
                    domain=str(item.get("domain", "")),
                    first_seen=str(item.get("first_seen", "")),
                    last_seen=str(item.get("last_seen", "")),
                    fail_reason=str(item.get("fail_reason", "unknown")),
                    source=str(item.get("source", "unknown")),
                    last_error=str(item.get("last_error", "")),
                )
            )
        return out
    except Exception as e:
        log.warning("Failed to load problem_domains: %s", e)
        return []


def save_problem_domains(ctx, domains: list[ProblemDomain]) -> None:
    p = _problem_domains_path(ctx)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = [
        {
            "domain": d.domain,
            "first_seen": d.first_seen,
            "last_seen": d.last_seen,
            "fail_reason": d.fail_reason,
            "source": d.source,
            "last_error": d.last_error,
        }
        for d in domains
    ]
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_problem_domain(
    ctx,
    domain: str,
    *,
    source: str = "unknown",
    fail_reason: str = "unknown",
    error: str = "",
) -> None:
    """Add or update a problem domain."""
    domain = (domain or "").strip()
    if not domain:
        return
    # Normalize: remove scheme and trailing slashes
    for prefix in ("https://", "http://"):
        if domain.startswith(prefix):
            domain = domain[len(prefix):]
    domain = domain.strip("/").strip()

    domains = load_problem_domains(ctx)
    now = datetime.now(timezone.utc).isoformat()

    for d in domains:
        if d.domain == domain:
            # Update existing
            d.last_seen = now
            d.fail_reason = fail_reason
            d.source = source
            d.last_error = error
            save_problem_domains(ctx, domains)
            log.info("Updated problem domain: %s (%s)", domain, fail_reason)
            return

    # New domain
    domains.append(
        ProblemDomain(
            domain=domain,
            first_seen=now,
            last_seen=now,
            fail_reason=fail_reason,
            source=source,
            last_error=error,
        )
    )
    save_problem_domains(ctx, domains)
    log.info("Added problem domain: %s (%s)", domain, fail_reason)


def add_from_domain_checks(
    ctx,
    checks: list[Any],  # list of DomainCheck
    *,
    source: str = "unknown",
) -> None:
    """Add failed domains from a list of DomainCheck objects."""
    for check in checks:
        if check.ok:
            continue
        # Determine fail reason
        reason = "unknown"
        if check.error:
            err = check.error.lower()
            if "dns" in err or not check.dns_ok:
                reason = "dns_fail"
            elif "tcp" in err or not check.tcp_ok:
                reason = "tcp_fail"
            elif "http" in err or "status" in err:
                reason = "http_fail"
            elif "ping" in err or not check.ping_ok:
                reason = "ping_fail"
            elif "timeout" in err:
                reason = "timeout"
            else:
                reason = "fail"
        else:
            if not check.dns_ok:
                reason = "dns_fail"
            elif not check.tcp_ok:
                reason = "tcp_fail"
            elif not check.ping_ok:
                reason = "ping_fail"
            else:
                reason = "fail"

        add_problem_domain(
            ctx,
            domain=check.domain,
            source=source,
            fail_reason=reason,
            error=check.error or "",
        )


def get_problem_domains(ctx) -> list[str]:
    """Return just the domain names for use as a domain set."""
    domains = load_problem_domains(ctx)
    return [d.domain for d in domains]


def clear_problem_domains(ctx) -> None:
    """Clear all problem domains."""
    p = _problem_domains_path(ctx)
    if p.exists():
        p.unlink()
    log.info("Cleared problem domains")


def problem_domains_summary(ctx) -> str:
    """Human-readable summary of problem domains."""
    domains = load_problem_domains(ctx)
    if not domains:
        return "Проблемные домены: пока нет"
    lines = [
        f"Проблемные домены: {len(domains)}",
        "",
    ]
    for i, d in enumerate(domains, start=1):
        lines.append(f"{i}. {d.domain} — {d.source} / {d.fail_reason}")
        if d.last_error:
            lines.append(f"   last error: {d.last_error}")
        lines.append(f"   first seen: {d.first_seen}")
        lines.append(f"   last seen: {d.last_seen}")
    return "\n".join(lines)


def remove_resolved_domain(ctx, domain: str) -> None:
    """Remove a domain that is now OK (called after successful strategy test)."""
    domains = load_problem_domains(ctx)
    before = len(domains)
    domains = [d for d in domains if d.domain != domain]
    if len(domains) < before:
        save_problem_domains(ctx, domains)
        log.info("Removed resolved problem domain: %s", domain)