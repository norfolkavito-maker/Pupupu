# Workflow 01 — Release packaging cleanup

## Scope
Audit and clean up the current release packaging pipeline so that portable archives are clean zero-state packages, not snapshots of a test machine.

## Tasks

### 1.1 Audit current release workflow
- Inspect `.github/workflows/build.yml` and `check.yml`.
- List all files that get packaged into release artifacts.
- Identify stale/test files that should not be in release archives.

### 1.2 Define clean portable layout
Document and enforce the target layout from `00_clean_rebuild_overview.md`.

### 1.3 Exclude stale state from releases
Add `.gitignore` or build script exclusions for:
- `DedZapretData/data/logs/session_*.jsonl`
- `DedZapretData/data/logs/report_*.zip`
- `DedZapretData/data/results/*`
- `DedZapretData/data/telemetry/*`
- `DedZapretData/data/state/state.json`
- `DedZapretData/data/problem_domains.json` (unless intentional default template)
- Local absolute paths
- `__MACOSX/*`
- `.DS_Store`
- `._*` AppleDouble files
- Developer machine logs
- Stale generated reports
- Stale telemetry
- Stale process state

### 1.4 First-run state generation
Ensure that on first launch, the program creates:
- state.json
- current.json
- audit records
- logs directory
- reports directory
- default user list files if needed

### 1.5 Package inspection test
Add a test that verifies the release archive is clean:
- Contains expected binaries
- Does not contain stale state
- Does not contain __MACOSX or .DS_Store

## Acceptance criteria
- [ ] Release archive contains only clean portable files.
- [ ] First launch generates state/logs/reports automatically.
- [ ] Package inspection test exists and passes.
- [ ] No stale test machine data in releases.

## Related files
- `.github/workflows/build.yml`
- `.github/workflows/check.yml`
- `app/zapret_manager/packaging/__init__.py`
- `release/` notes