# MASTER_TASK — Local AI Agent Workflow Pack

## Goal

Create and maintain a **local AI-agent workflow pack** inside this repository.
The pack must allow future coding agents to:
- read task files and prompts from the repo;
- follow strict rules and safety constraints;
- self-review their changes;
- run verification scripts;
- update progress and blockers logs;
- stop only when Definition of Done is satisfied.

## Project context

This repository contains a Python project. The agent workflow pack must be
repository-local, explicit, reviewable and versioned in git.

## Required workflow

Agents must follow this loop:
1. Read mandatory rule files (Phase 0).
2. Plan in small milestones.
3. Implement one milestone.
4. Self-review and ensure no secrets.
5. Run verification.
6. Update `docs/ai/PROGRESS.md`.
7. Repeat until DoD is satisfied.

## Prompt files referenced by this contract

These files are part of the “task packet” and must be read before meaningful edits:

- `docs/ai/prompts/01-core-foundation.md`
- `docs/ai/prompts/02-ui-ux.md`
- `docs/ai/prompts/03-tests-diagnostics.md`
- `docs/ai/prompts/04-release-polish.md`

## Phase 0 — Read and plan (mandatory)

Before editing any project logic:
- Read `AGENTS.md`.
- Read this file: `docs/ai/MASTER_TASK.md`.
- Read `docs/ai/CONTEXT_MAP.md` before broad repository exploration.
- Read **all** files under `docs/ai/prompts/`.
- Inspect repository structure.
- Write a short implementation plan into `docs/ai/PROGRESS.md`.

## Phase 1 — Implement safely

- Work in **small milestones**.
- Preserve existing behavior unless the task explicitly changes it.
- Do not invent features; if something seems reasonable but is not requested,
  write it down as **Future / Planned**.
- Avoid unrelated refactors.

## Phase 2 — Self-review

After each milestone, the agent must perform a self-review:
- Compare changes against requirements and non-goals.
- Check for secrets in logs/notes.
- Ensure tests were updated if behavior changed.
- Ensure docs are updated if user-visible behavior changed.

## Self-review loop (required)

If self-review finds issues:
1. Fix issues.
2. Re-run verification.
3. Update `docs/ai/PROGRESS.md` with what changed.

## Verification command

After every meaningful change:
- Windows: `./scripts/agent-verify.ps1`
- Non-Windows: `bash scripts/agent-verify.sh`

## Definition of Done (DoD)

This task is complete only when all conditions below are met:

1. All actionable requirements from **all prompt files** are complete:
   - `docs/ai/prompts/01-core-foundation.md`
   - `docs/ai/prompts/02-ui-ux.md`
   - `docs/ai/prompts/03-tests-diagnostics.md`
   - `docs/ai/prompts/04-release-polish.md`
2. All relevant items in `docs/ai/ACCEPTANCE_CHECKLIST.md` are checked.
3. Verification script passes:
   - `./scripts/agent-verify.ps1` (on Windows) or
   - `bash scripts/agent-verify.sh` (on non-Windows).
4. Existing tests pass.
5. Changed behavior has tests where reasonable.
6. `docs/ai/PROGRESS.md` contains a final summary.
7. `docs/ai/BLOCKERS.md` has **no unresolved critical blockers**.
8. No secrets are exposed (tokens, credentials, private keys, personal data).
9. Changes are minimal and related to the task.
10. Documentation is updated if user-visible behavior changed.
