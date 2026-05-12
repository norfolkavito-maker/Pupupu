"""Problem domains bridge for Stage 03.7.

Manages problem domains as virtual test set and strategy ranking integration.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.zapret_manager.core.app_context import AppContext

from app.zapret_manager.utils.jsonx import atomic_write_json

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class StrategyRankingEntry:
    """Represents a strategy ranking entry."""
    strategy_id: str
    strategy_name: str
    status: str  # VALID, INVALID, CONNECTIVITY_FAILURE, ERROR
    working_domains: List[str] = field(default_factory=list)
    broken_domains: List[str] = field(default_factory=list)
    error_message: str = ""
    test_time: str = ""


@dataclass(frozen=True)
class RankingReport:
    """Strategy ranking report."""
    generated_at: str
    total_strategies: int
    valid_strategies: int
    invalid_strategies: int
    connectivity_failures: int
    errors: int
    entries: List[StrategyRankingEntry]


class ProblemDomainsBridge:
    """Manages problem domains as virtual test set and strategy ranking."""
    
    def __init__(self, ctx: "AppContext"):
        self.ctx = ctx
        self.problem_domains_file = ctx.paths.data_dir / "problem_domains.json"
        self.ranking_file = ctx.paths.data_dir / "latest_strategy_ranking.txt"
    
    def load_problem_domains(self) -> List[str]:
        """Load problem domains as virtual test set."""
        if not self.problem_domains_file.exists():
            return []
        
        try:
            data = json.loads(self.problem_domains_file.read_text(encoding="utf-8"))
            return data.get("domains", [])
        except Exception as e:
            log.warning("Failed to load problem domains: %s", e)
            return []
    
    def save_problem_domains(self, domains: List[str]) -> None:
        """Save problem domains to file."""
        data = {
            "version": 2,
            "updated_at": self._utc_now_iso(),
            "domains": sorted(set(domains))  # Remove duplicates
        }
        
        self.problem_domains_file.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(self.problem_domains_file, data)
        log.info("Saved %d problem domains", len(domains))
    
    def add_problem_domains(self, domains: List[str]) -> None:
        """Add domains to problem domains list."""
        existing = self.load_problem_domains()
        updated = existing + domains
        self.save_problem_domains(updated)
    
    def create_ranking_report(self, test_results: List[Dict]) -> RankingReport:
        """Create strategy ranking report from test results."""
        entries = []
        total_strategies = len(test_results)
        valid_strategies = 0
        invalid_strategies = 0
        connectivity_failures = 0
        errors = 0
        
        for result in test_results:
            strategy_id = result.get("strategy_id", "unknown")
            strategy_name = result.get("strategy_name", "Unknown Strategy")
            status = result.get("status", "ERROR")
            working_domains = result.get("working_domains", [])
            broken_domains = result.get("broken_domains", [])
            error_message = result.get("error", "")
            test_time = result.get("test_time", "")
            
            if status == "VALID":
                valid_strategies += 1
            elif status == "INVALID":
                invalid_strategies += 1
            elif status in ["CONNECTIVITY_FAILURE", "TIMEOUT"]:
                connectivity_failures += 1
            else:
                errors += 1
            
            entries.append(StrategyRankingEntry(
                strategy_id=strategy_id,
                strategy_name=strategy_name,
                status=status,
                working_domains=working_domains,
                broken_domains=broken_domains,
                error_message=error_message,
                test_time=test_time
            ))
        
        return RankingReport(
            generated_at=self._utc_now_iso(),
            total_strategies=total_strategies,
            valid_strategies=valid_strategies,
            invalid_strategies=invalid_strategies,
            connectivity_failures=connectivity_failures,
            errors=errors,
            entries=entries
        )
    
    def save_ranking_report(self, report: RankingReport) -> None:
        """Save strategy ranking report to files."""
        # Save JSON version for diagnostics
        json_data = {
            "generated_at": report.generated_at,
            "summary": {
                "total_strategies": report.total_strategies,
                "valid_strategies": report.valid_strategies,
                "invalid_strategies": report.invalid_strategies,
                "connectivity_failures": report.connectivity_failures,
                "errors": report.errors
            },
            "entries": [
                {
                    "strategy_id": entry.strategy_id,
                    "strategy_name": entry.strategy_name,
                    "status": entry.status,
                    "working_domains": entry.working_domains,
                    "broken_domains": entry.broken_domains,
                    "error_message": entry.error_message,
                    "test_time": entry.test_time
                }
                for entry in report.entries
            ]
        }
        
        self.ranking_file.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(self.ranking_file.with_suffix(".json"), json_data)
        
        # Save human-readable text version
        lines = [
            f"# Strategy Ranking Report - Generated {report.generated_at}",
            f"",
            f"Total strategies tested: {report.total_strategies}",
            f"Valid strategies: {report.valid_strategies}",
            f"Invalid strategies: {report.invalid_strategies}",
            f"Connectivity failures: {report.connectivity_failures}",
            f"Errors: {report.errors}",
            f"",
            "# Ranking by status (VALID first):",
            f""
        ]
        
        # Sort entries: VALID first, then by name
        sorted_entries = sorted(
            report.entries,
            key=lambda x: (0 if x.status == "VALID" else 1, x.strategy_name.lower())
        )
        
        for entry in sorted_entries:
            status_icon = {
                "VALID": "✅",
                "INVALID": "❌", 
                "CONNECTIVITY_FAILURE": "🌐",
                "ERROR": "⚠️"
            }.get(entry.status, "❓")
            
            lines.append(f"{status_icon} {entry.strategy_name} ({entry.status})")
            
            if entry.working_domains:
                lines.append(f"  Working: {', '.join(entry.working_domains)}")
            
            if entry.broken_domains:
                lines.append(f"  Broken: {', '.join(entry.broken_domains)}")
            
            if entry.error_message:
                lines.append(f"  Error: {entry.error_message}")
            
            lines.append("")
        
        self.ranking_file.write_text("\n".join(lines), encoding="utf-8")
        log.info("Strategy ranking report saved: %d strategies", report.total_strategies)
    
    def get_problem_domains_as_test_set(self) -> List[str]:
        """Get problem domains formatted as test set for strategy testing."""
        domains = self.load_problem_domains()
        if not domains:
            return []
        
        # Return as list for test framework compatibility
        return domains
    
    def _utc_now_iso(self) -> str:
        """Get current UTC time in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_problem_domains_setup(ctx: "AppContext") -> None:
    """Ensure problem domains are set up as virtual test set."""
    bridge = ProblemDomainsBridge(ctx)
    
    # Create initial problem domains if doesn't exist
    if not bridge.problem_domains_file.exists():
        initial_domains = [
            "vk.com",
            "ok.ru", 
            "yandex.ru",
            "youtube.com",
            "discord.com"
        ]
        bridge.save_problem_domains(initial_domains)
        log.info("Created initial problem domains set with %d domains", len(initial_domains))
    else:
        log.debug("Problem domains file already exists")


def add_failed_domains_to_problem_set(ctx: "AppContext", failed_domains: List[str]) -> None:
    """Add failed domains from strategy testing to problem domains set."""
    if not failed_domains:
        return
    
    bridge = ProblemDomainsBridge(ctx)
    bridge.add_problem_domains(failed_domains)
    log.info("Added %d failed domains to problem set", len(failed_domains))
