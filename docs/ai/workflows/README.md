# Workflows (staged)

This folder contains **staged implementation workflows** for coding agents.

## What these files are

- Each `*.md` file is a **stage plan** (a structured prompt / checklist / guidance)
  for implementing a specific set of changes.
- Stages are designed to be executed **in order**.

## Rules

- Agents must read **all stages** to understand the bigger picture.
- Agents must execute stages **strictly in order**.
- Agents must not skip stages unless the human explicitly overrides.
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
  Do not delete completed items from workflow files; keep the history.

## Execution order

1. `01_stabilization_fixes_test10.md`
2. `02_test_engine_performance.md`
3. `03_tray_and_menu_ux.md`
