"""
Release packaging tests.

These tests verify that a staged portable release directory is clean:
- required files are present
- forbidden artifacts are absent
- no local absolute paths
- no macOS metadata

Tests can run:
  - against a real bundle directory (set DEDZAPRET_BUNDLE_DIR env var)
  - against temp directories for unit tests (fixtures generate deliberate dirty/clean bundles)
"""

import os
from pathlib import Path
import pytest


# --- Forbidden glob patterns ---
FORBIDDEN_PATTERNS = [
    "__MACOSX",
    "__MACOSX/**",
    "**/__MACOSX",
    "**/__MACOSX/**",
    "**/.DS_Store",
    "**/._*",
    "**/session_*.jsonl",
    "**/report_*.zip",
    "**/zapret_manager.log",
    "**/winws_stdout*.log",
    "**/winws_stderr*.log",
]

# --- Forbidden stale runtime state ---
FORBIDDEN_STATE = [
    "**/data/state/state.json",
    "**/data/state/current.json",
]

# --- Required files ---
REQUIRED_FILES = [
    "DedZapret.exe",
    "DedZapretData/config.yaml",
    "DedZapretData/sources.yaml",
    "DedZapretData/data/lists",
    "DedZapretData/data/strategies/builtin",
    "DedZapretData/data/strategies/custom",
]


def walk_bundle(bundle_dir: Path) -> list[Path]:
    """Return all file and directory paths under bundle_dir, relative to it."""
    result = []
    for root, dirs, files in os.walk(bundle_dir):
        for name in dirs:
            result.append(Path(root) / name)
        for name in files:
            result.append(Path(root) / name)
    return result


def check_forbidden_glob(bundle_dir: Path, glob_pattern: str) -> list[str]:
    """Return relative paths matching a forbidden glob pattern.

    Uses PurePath.match() which supports ** wildcards.
    """
    matches = []
    for item in walk_bundle(bundle_dir):
        rel = item.relative_to(bundle_dir)
        if rel.match(glob_pattern):
            matches.append(str(rel))
    return matches


def check_local_absolute_paths(bundle_dir: Path) -> list[str]:
    """Return filenames containing local absolute paths."""
    violations = []
    for root, _dirs, files in os.walk(bundle_dir):
        for fname in files:
            fpath = Path(root) / fname
            try:
                text = fpath.read_text(errors="replace")
                if "C:\\Users\\" in text or "C:/Users/" in text:
                    rel = fpath.relative_to(bundle_dir)
                    violations.append(str(rel))
            except Exception:
                pass
    return violations


# --- Fixtures ---

@pytest.fixture
def clean_bundle(tmp_path: Path) -> Path:
    """Create a clean minimal bundle structure."""
    bundle = tmp_path / "DedZapret"
    bundle.mkdir()

    (bundle / "DedZapret.exe").write_text("fake exe")
    data = bundle / "DedZapretData"
    data.mkdir()
    (data / "config.yaml").write_text("config: test")
    (data / "sources.yaml").write_text("sources: test")
    (data / "data" / "lists").mkdir(parents=True)
    (data / "data" / "strategies" / "builtin").mkdir(parents=True)
    (data / "data" / "strategies" / "custom").mkdir(parents=True)
    return bundle


@pytest.fixture
def dirty_bundle(clean_bundle: Path) -> Path:
    """Add forbidden files to a clean bundle."""
    # __MACOSX (inside the bundle where it would appear in a real archive)
    macosx = clean_bundle / "__MACOSX"
    macosx.mkdir()
    (macosx / "garbage").write_text("")

    # .DS_Store
    (clean_bundle / ".DS_Store").write_text("")
    (clean_bundle / "DedZapretData" / ".DS_Store").write_text("")

    # session and report files
    logs_dir = clean_bundle / "DedZapretData" / "data" / "logs"
    logs_dir.mkdir(parents=True)
    (logs_dir / "session_test.jsonl").write_text("{}")
    (logs_dir / "report_test.zip").write_text("fake zip")

    # stale state
    state_dir = clean_bundle / "DedZapretData" / "data" / "state"
    state_dir.mkdir(parents=True)
    (state_dir / "state.json").write_text('{"stale": true}')
    (state_dir / "current.json").write_text('{"stale": true}')

    # local path in a text file
    (clean_bundle / "DedZapretData" / "bad_config.txt").write_text(
        'Some path: C:\\Users\\developer\\stuff\n'
    )
    return clean_bundle


# --- Tests ---

class TestReleasePreflight:
    """Positive and negative tests for release packaging rules."""

    # --- Clean bundle — must pass ---

    def test_clean_bundle_has_required_files(self, clean_bundle: Path):
        for req in REQUIRED_FILES:
            path = clean_bundle / req
            assert path.exists(), f"Missing required: {req}"

    def test_clean_bundle_no_forbidden_patterns(self, clean_bundle: Path):
        for pattern in FORBIDDEN_PATTERNS:
            matches = check_forbidden_glob(clean_bundle, pattern)
            assert len(matches) == 0, \
                f"Forbidden {pattern}: {matches}"

    def test_clean_bundle_no_stale_state(self, clean_bundle: Path):
        for pattern in FORBIDDEN_STATE:
            matches = check_forbidden_glob(clean_bundle, pattern)
            assert len(matches) == 0, \
                f"Forbidden state {pattern}: {matches}"

    def test_clean_bundle_no_local_paths(self, clean_bundle: Path):
        violations = check_local_absolute_paths(clean_bundle)
        assert len(violations) == 0, \
            f"Local path violations: {violations}"

    # --- Dirty bundle — must fail ---

    def test_dirty_bundle_has_forbidden_macosx(self, dirty_bundle: Path):
        matches = check_forbidden_glob(dirty_bundle, "__MACOSX")
        matches += check_forbidden_glob(dirty_bundle, "__MACOSX/**")
        matches += check_forbidden_glob(dirty_bundle, "**/__MACOSX")
        matches += check_forbidden_glob(dirty_bundle, "**/__MACOSX/**")
        assert len(matches) > 0, "Should detect __MACOSX"

    def test_dirty_bundle_has_forbidden_ds_store(self, dirty_bundle: Path):
        matches = check_forbidden_glob(dirty_bundle, "**/.DS_Store")
        assert len(matches) > 0, "Should detect .DS_Store"

    def test_dirty_bundle_has_forbidden_session(self, dirty_bundle: Path):
        matches = check_forbidden_glob(dirty_bundle, "**/session_*.jsonl")
        assert len(matches) > 0, "Should detect session jsonl"

    def test_dirty_bundle_has_forbidden_report(self, dirty_bundle: Path):
        matches = check_forbidden_glob(dirty_bundle, "**/report_*.zip")
        assert len(matches) > 0, "Should detect report zip"

    def test_dirty_bundle_has_forbidden_state(self, dirty_bundle: Path):
        matches = check_forbidden_glob(dirty_bundle, "**/data/state/state.json")
        matches += check_forbidden_glob(dirty_bundle, "**/data/state/current.json")
        assert len(matches) > 0, "Should detect stale state"

    def test_dirty_bundle_has_local_paths(self, dirty_bundle: Path):
        violations = check_local_absolute_paths(dirty_bundle)
        assert len(violations) > 0, "Should detect C:\\Users\\ paths"