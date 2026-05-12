"""Runtime asset repair functionality for Stage 03.5.

Repairs missing runtime assets from trusted bundled upstream sources.
Never creates empty fake .bin files.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.zapret_manager.core.app_context import AppContext

from app.zapret_manager.features.upstreams_snapshot import UpstreamSnapshotManager, create_default_snapshot
from app.zapret_manager.utils.jsonx import atomic_write_json

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RepairResult:
    """Result of runtime asset repair operation."""
    total_assets: int
    repaired: int
    created: int
    already_exists: int
    missing_sources: List[str]
    errors: List[str]


class RuntimeAssetRepairer:
    """Repairs runtime assets from bundled upstream sources."""
    
    def __init__(self, ctx: "AppContext"):
        self.ctx = ctx
        self.snapshot_manager = UpstreamSnapshotManager(ctx)
        self.repair_report_file = ctx.paths.data_dir / "runtime_repair_report.json"
    
    def repair_runtime_assets(self) -> RepairResult:
        """Repair runtime assets from bundled upstream sources."""
        log.info("Starting runtime asset repair...")
        
        if not self.snapshot_manager.is_snapshot_available():
            log.warning("No bundled upstream snapshot available for repair")
            return RepairResult(
                total_assets=0,
                repaired=0,
                created=0,
                already_exists=0,
                missing_sources=["bundled snapshot"],
                errors=["No bundled upstream snapshot found"]
            )
        
        total_assets = 0
        repaired = 0
        created = 0
        already_exists = 0
        missing_sources = []
        errors = []
        
        # Repair fake assets from bolvan (trusted source)
        fake_assets = [
            "tls_clienthello_4pda_to.bin",
            "tls_clienthello_4pda_from.bin", 
            "tls_clienthello_sni.bin",
            "tls_clienthello_split.bin"
        ]
        
        for fake_asset in fake_assets:
            total_assets += 1
            result = self._repair_fake_asset("bolvan", f"files/fake/{fake_asset}", fake_asset)
            if result == "repaired":
                repaired += 1
            elif result == "created":
                created += 1
            elif result == "exists":
                already_exists += 1
        
        # Repair list assets from flowseal
        list_assets = ["general.txt", "exclude.txt"]
        for list_asset in list_assets:
            total_assets += 1
            result = self._repair_list_asset("flowseal", f"lists/{list_asset}", list_asset)
            if result == "repaired":
                repaired += 1
            elif result == "created":
                created += 1
            elif result == "exists":
                already_exists += 1
        
        # Create repair report
        report = {
            "timestamp": self._utc_now_iso(),
            "total_assets": total_assets,
            "repaired": repaired,
            "created": created,
            "already_exists": already_exists,
            "missing_sources": missing_sources,
            "errors": errors
        }
        
        atomic_write_json(self.repair_report_file, report)
        
        log.info(
            "Runtime repair completed: total=%d repaired=%d created=%d exists=%d missing=%d",
            total_assets, repaired, created, already_exists, len(missing_sources)
        )
        
        return RepairResult(
            total_assets=total_assets,
            repaired=repaired,
            created=created,
            already_exists=already_exists,
            missing_sources=missing_sources,
            errors=errors
        )
    
    def _repair_fake_asset(self, upstream_name: str, asset_path: str, asset_name: str) -> str:
        """Repair a single fake asset from bundled upstream."""
        runtime_fake_path = self.ctx.paths.zapret_runtime_dir / "files" / "fake" / asset_name
        
        # Check if already exists and is non-empty
        if runtime_fake_path.exists() and runtime_fake_path.stat().st_size > 0:
            log.debug("Fake asset already exists: %s", asset_name)
            return "exists"
        
        # Get bundled source
        bundled_path = self.snapshot_manager.get_bundled_asset_path(upstream_name, asset_path)
        if not bundled_path or not bundled_path.exists() or bundled_path.stat().st_size == 0:
            log.warning("Bundled fake asset missing or empty: %s from %s", asset_name, upstream_name)
            return "missing_source"
        
        try:
            # Ensure directory exists
            runtime_fake_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy from bundled source
            runtime_fake_path.write_bytes(bundled_path.read_bytes())
            log.info("Repaired fake asset: %s", asset_name)
            return "repaired"
        except Exception as e:
            log.error("Failed to repair fake asset %s: %s", asset_name, e)
            return "error"
    
    def _repair_list_asset(self, upstream_name: str, asset_path: str, asset_name: str) -> str:
        """Repair a single list asset from bundled upstream."""
        runtime_list_path = self.ctx.paths.lists_dir / asset_name
        
        # Check if already exists
        if runtime_list_path.exists():
            log.debug("List asset already exists: %s", asset_name)
            return "exists"
        
        # Get bundled source
        bundled_path = self.snapshot_manager.get_bundled_asset_path(upstream_name, asset_path)
        if not bundled_path or not bundled_path.exists():
            log.warning("Bundled list asset missing: %s from %s", asset_name, upstream_name)
            return "missing_source"
        
        try:
            # Ensure directory exists
            runtime_list_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy from bundled source
            runtime_list_path.write_text(bundled_path.read_text(encoding="utf-8"), encoding="utf-8")
            log.info("Repaired list asset: %s", asset_name)
            return "repaired"
        except Exception as e:
            log.error("Failed to repair list asset %s: %s", asset_name, e)
            return "error"
    
    def _utc_now_iso(self) -> str:
        """Get current UTC time in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    
    def get_repair_report(self) -> Optional[Dict]:
        """Get the last repair report."""
        if not self.repair_report_file.exists():
            return None
        try:
            return json.loads(self.repair_report_file.read_text(encoding="utf-8"))
        except Exception:
            return None


def ensure_first_launch_setup(ctx: "AppContext") -> bool:
    """Ensure first launch setup with bundled upstream snapshot and runtime repair."""
    from app.zapret_manager.features.upstreams_snapshot import save_snapshot
    
    # Create default snapshot if doesn't exist
    if not UpstreamSnapshotManager(ctx).is_snapshot_available():
        log.info("Creating default bundled upstream snapshot")
        snapshot = create_default_snapshot(ctx)
        save_snapshot(ctx, snapshot)
    
    # Setup upstream directories from snapshot
    snapshot_manager = UpstreamSnapshotManager(ctx)
    if not snapshot_manager.ensure_first_launch_setup():
        log.error("Failed to setup first launch from bundled snapshot")
        return False
    
    # Repair runtime assets
    repairer = RuntimeAssetRepairer(ctx)
    repair_result = repairer.repair_runtime_assets()
    
    if repair_result.errors or repair_result.missing_sources:
        log.warning("Runtime repair completed with issues: %s", repair_result.errors + repair_result.missing_sources)
    else:
        log.info("Runtime repair completed successfully")
    
    return True
