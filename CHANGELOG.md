# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- New agent rules documentation from DedZapret agent workflow pack:
  - `docs/ai/DEDZAPRET_AGENT_RULES.md` — project-specific safety rules
  - `docs/ai/RUNTIME_SOURCE_POLICY.md` — upstream source roles
  - `docs/ai/development_history_merged.md` — unified bug/regression history
  - `docs/ai/HISTORY_AUDIT_WORKFLOW.md` / `docs/ai/HISTORY_AUDIT.md` — history audit process
  - `docs/ai/REGRESSION_PREVENTION_CHECKLIST.md` — release safety checklist
  - `docs/ai/STRATEGY_COMPATIBILITY_WORKFLOW.md` / `docs/ai/STRATEGY_COMPATIBILITY_MATRIX.md`
  - `docs/ai/PRODUCT_OVERVIEW.md` / `docs/ai/OPERATIONS_AND_QOL_SPEC.md`
- New Python package structure aligned with PROGRAM_BLUEPRINT:
  - `app/zapret_manager/runtime/` (winws2/, windivert/)
  - `app/zapret_manager/windows_ops/`
  - `app/zapret_manager/profiles/`
  - `app/zapret_manager/tests_engine/`
  - `app/zapret_manager/packaging/`
- `.gitignore` now includes `__MACOSX/` pattern
- Updated README.md with project overview and agent rules references

### Changed
- `AGENTS.md` — expanded with DedZapret-specific safety rules, upstream source roles, runtime audit logging, history/regression prevention section, and additional mandatory reads
- `.github/copilot-instructions.md` — added references to new docs (DEDZAPRET_AGENT_RULES, RUNTIME_SOURCE_POLICY, development_history_merged, REGRESSION_PREVENTION_CHECKLIST)
- `.github/prompts/` — updated self-review and full-task prompts
- `.windsurf/rules/agent-general.md` — added new mandatory docs to read list
- `.windsurf/rules/project-local-workflow.md` — added new docs and regression prevention to workflow
- `docs/ai/MASTER_TASK.md` — fresh build mode clarification, expanded source of truth, additional mandatory reads
- `docs/ai/ACCEPTANCE_CHECKLIST.md` — added DedZapret/Windows runtime safety section and agent rules docs checklist
- `docs/ai/CONTEXT_MAP.md` — updated to reflect new module structure

### Fixed
- Normalized imports to the `app.zapret_manager` package namespace (including nested imports).
- Removed unused imports (ruff auto-fix).
- Unit tests updated to match new package namespace.
- `generate_bat()` now tolerates a minimal context (fallback when runtime paths/state are absent) to keep unit tests and tooling stable.

### Verified
- Full unit test suite passes.
- Agent verify script passes.