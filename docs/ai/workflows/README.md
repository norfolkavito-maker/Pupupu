# Workflows (staged)

This folder contains **staged implementation workflows** for coding agents.

## What these files are

- Each `*.md` file is a **stage plan** (a structured prompt / checklist / guidance)
  for implementing a specific set of changes.
- Stages are designed to be executed **in order**.

## Rules

- Agents must read **all stages** to understand bigger picture.
- Agents must execute stages **strictly in order**.
- Agents must not skip stages unless human explicitly overrides.
- Each stage must be:
  1) implemented,
  2) tested/verified,
  3) committed,
  4) summarized in `docs/ai/PROGRESS.md`,
  5) reflected in `docs/ai/ACCEPTANCE_CHECKLIST.md`
  before moving to the next stage.
- If tests fail, regression fixes have priority over new work.
- These workflow files are **living documents** and should be updated only when
  project requirements change.
- Completed work must be tracked in `PROGRESS.md` and `ACCEPTANCE_CHECKLIST.md`.
- Do not delete completed items from workflow files; keep history.

## Required verification policy

Each workflow must define:
- **Targeted tests:** Specific tests required for the stage.
- **Release/package tests** if packaging is touched.
- **Full pytest expectation:** What full test suite should achieve.
- **Manual Windows smoke test** if behavior is Windows-only.
- **Agent-verify requirement:** Must pass before stage completion.

A workflow is **complete only when:**
- **Required tests pass.**
- **Workflow-required tests pass.**
- **Agent-verify passes.**
- **Full pytest passes** when reasonable for change scope.
- **Any remaining failures are explicitly listed and classified** as unrelated known failures or blockers.

If full pytest fails:
- **Do not proceed to next stage.**
- **Do not mark stage complete.**
- **Do not claim readiness.**
- **Create a failure table** and fix or document blockers.

## Execution order

### Clean rebuild phases (current)

1. `00_clean_rebuild_overview.md` — strategic overview
2. `01_release_packaging_cleanup.md` — clean portable releases
3. `02_path_resolver_runtime_assets.md` — canonical paths, asset model
4. `03_strategy_import_validation.md` — normalize, validate, index strategies
5. `04_menu_simplification.md` — short main menu, status-first UI
6. `05_singbox_pipeline.md` — node import, config build, lifecycle
7. `06_diagnostics_bug_report.md` — masked diagnostics, structured reports
8. `07_release_verification.md` — full test suite, smoke test, shippable artifact

### Legacy workflow stages (superseded)

These stages are superseded by the clean rebuild phases above.
They remain in the repository as historical reference:

- `01_stabilization_fixes_test10.md`
- `02_test_engine_performance.md`
- `03_tray_and_menu_ux.md`