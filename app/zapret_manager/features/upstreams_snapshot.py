"""
Bundled upstream snapshot management for Stage 03.5.

This provides first-launch functionality without requiring GitHub downloads.
Upstream assets are stored in DedZapretData/data/upstreams/ and used as trusted sources.
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
class UpstreamSnapshot:
    """Represents a bundled upstream snapshot."""
    version: str
    created_at: str
    sources: Dict[str, "UpstreamSource"]


@dataclass(frozen=True)
class UpstreamSource:
    """Represents a single upstream source in snapshot."""
    name: str
    path: str  # relative to upstreams root
    kind: str  # flowseal, stressozz, bolvan
    description: str = ""
    assets: List[str] = field(default_factory=list)  # known good assets


class UpstreamSnapshotManager:
    """Manages bundled upstream snapshots and first-launch setup."""
    
    def __init__(self, ctx: "AppContext"):
        self.ctx = ctx
        self.upstreams_dir = ctx.paths.upstreams_dir
        self.snapshot_file = self.upstreams_dir / "snapshot.json"
    
    def is_snapshot_available(self) -> bool:
        """Check if bundled upstream snapshot exists."""
        return self.snapshot_file.exists()
    
    def load_snapshot(self) -> Optional[UpstreamSnapshot]:
        """Load the bundled upstream snapshot."""
        if not self.is_snapshot_available():
            return None
        
        try:
            data = json.loads(self.snapshot_file.read_text(encoding="utf-8"))
            sources = {}
            for name, source_data in data.get("sources", {}).items():
                sources[name] = UpstreamSource(**source_data)
            
            return UpstreamSnapshot(
                version=data.get("version", "unknown"),
                created_at=data.get("created_at", ""),
                sources=sources
            )
        except Exception as e:
            log.warning("Failed to load upstream snapshot: %s", e)
            return None
    
    def ensure_first_launch_setup(self) -> bool:
        """Ensure first-launch setup using bundled upstream snapshot."""
        if not self.is_snapshot_available():
            log.info("No bundled upstream snapshot found")
            return False
        
        snapshot = self.load_snapshot()
        if not snapshot:
            return False
        
        log.info("Setting up first launch from bundled upstream snapshot v%s", snapshot.version)
        
        # Create upstream directories
        for source_name, source in snapshot.sources.items():
            source_dir = self.upstreams_dir / source_name
            source_dir.mkdir(parents=True, exist_ok=True)
            
            # Mark as bundled source (read-only reference)
            marker_file = source_dir / ".bundled"
            marker_file.write_text(f"Version: {snapshot.version}\nCreated: {source.created_at}", encoding="utf-8")
            
            log.debug("Created upstream directory: %s (%s)", source_name, source.kind)
        
        return True
    
    def get_bundled_asset_path(self, upstream_name: str, asset_path: str) -> Optional[Path]:
        """Get path to bundled asset within upstream."""
        snapshot = self.load_snapshot()
        if not snapshot:
            return None
        
        if upstream_name not in snapshot.sources:
            return None
        
        source = snapshot.sources[upstream_name]
        return self.upstreams_dir / upstream_name / asset_path
    
    def list_bundled_assets(self, upstream_name: str) -> List[str]:
        """List all known good assets for an upstream."""
        snapshot = self.load_snapshot()
        if not snapshot or upstream_name not in snapshot.sources:
            return []
        
        return snapshot.sources[upstream_name].assets
    
    def is_asset_bundled(self, upstream_name: str, asset_name: str) -> bool:
        """Check if specific asset is in bundled snapshot."""
        return asset_name in self.list_bundled_assets(upstream_name)


def create_default_snapshot(ctx: "AppContext") -> UpstreamSnapshot:
    """Create a default upstream snapshot structure."""
    return UpstreamSnapshot(
        version="1.0.0",
        created_at="2026-05-11T00:00:00Z",
        sources={
            "flowseal": UpstreamSource(
                name="flowseal",
                path="flowseal",
                kind="flowseal",
                description="Flowseal zapret-discord-youtube strategies and runtime",
                assets=[
                    "bin/winws.exe",
                    "bin/winws2.exe", 
                    "bin/WinDivert.dll",
                    "bin/WinDivert64.sys",
                    "lists/general.txt",
                    "lists/exclude.txt"
                ]
            ),
            "stressozz": UpstreamSource(
                name="stressozz",
                path="stressozz", 
                kind="stressozz",
                description="StressOzz Zapret-Manager.sh strategies and workflows",
                assets=[
                    "ipset/rkn.txt",
                    "ipset/exclude.txt"
                ]
            ),
            "bolvan": UpstreamSource(
                name="bolvan",
                path="bolvan",
                kind="bolvan",
                description="bol-van zapret reference implementation",
                assets=[
                    "files/fake/tls_clienthello_4pda_to.bin",
                    "files/fake/tls_clienthello_4pda_from.bin",
                    "files/fake/tls_clienthello_sni.bin",
                    "files/fake/tls_clienthello_split.bin"
                ]
            )
        }
    )


def save_snapshot(ctx: "AppContext", snapshot: UpstreamSnapshot) -> None:
    """Save upstream snapshot to file."""
    ctx.paths.upstreams_dir.mkdir(parents=True, exist_ok=True)
    
    snapshot_data = {
        "version": snapshot.version,
        "created_at": snapshot.created_at,
        "sources": {}
    }
    
    for name, source in snapshot.sources.items():
        snapshot_data["sources"][name] = {
            "name": source.name,
            "path": source.path,
            "kind": source.kind,
            "description": source.description,
            "assets": source.assets
        }
    
    atomic_write_json(ctx.paths.upstreams_dir / "snapshot.json", snapshot_data)
