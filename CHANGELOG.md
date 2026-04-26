# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed
- Normalized imports to the `app.zapret_manager` package namespace (including nested imports).
- Removed unused imports (ruff auto-fix).
- Unit tests updated to match new package namespace.
- `generate_bat()` now tolerates a minimal context (fallback when runtime paths/state are absent) to keep unit tests and tooling stable.

### Added
- Opt-in **diagnostics session recorder**: records console IO + subprocess activity into `DedZapretData/data/logs/session_*.jsonl`.
- On exit, when diagnostics enabled, prompts to build `report_*.zip` and opens GitHub Issue page with prefilled template.

### Verified
- Full unit test suite passes: `13 passed`.
