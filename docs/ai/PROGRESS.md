# PROGRESS

## Current status

- Status: Not started
- Current milestone: Phase 0 — Read and plan
- Last verification: Not run

## Milestones

- [ ] Phase 0 — Read and plan
- [ ] Phase 1 — Implement safely (milestone-by-milestone)
- [ ] Phase 2 — Self-review
- [ ] Finalize — DoD + Acceptance checklist + Verification

## Change log

Use one entry per milestone.

### 2026-05-03 11:45 — Add CONTEXT_MAP and enforce reading/maintenance rules

- Scope:
  - Created `docs/ai/CONTEXT_MAP.md` (concise repository navigation map).
  - Updated agent workflow rules to require reading `CONTEXT_MAP.md` before broad exploration and maintaining it when structure changes.
  - Updated acceptance checklist with CONTEXT_MAP global checkboxes.
- Files changed:
  - docs/ai/CONTEXT_MAP.md
  - AGENTS.md
  - docs/ai/MASTER_TASK.md
  - LOCAL_AGENT_START_HERE.md
  - docs/ai/OTHER_AGENT_RULES.md
  - docs/ai/AGENT_COMMANDS.md
  - .github/copilot-instructions.md
  - .github/instructions/agent-general.instructions.md
  - .github/prompts/local-full-task.prompt.md
  - .github/prompts/self-review.prompt.md
  - .windsurf/rules/agent-general.md
  - .windsurf/rules/project-local-workflow.md
  - docs/ai/ACCEPTANCE_CHECKLIST.md
- Verification:
  - Command(s):
    - (pending) `bash scripts/agent-verify.sh`
  - Result: PENDING
- Notes:
  - No project logic changed (docs/rules only).
- Next step:
  - Run verification and commit changes.

### Milestone — Added AI Workflow Documentation

- Date: 2026-05-03
- Goal: Add repository navigation and staged workflow docs for agents.
- Files changed:
  - docs/ai/CONTEXT_MAP.md
  - docs/ai/MASTER_TASK.md
  - docs/ai/PROGRESS.md
  - docs/ai/ACCEPTANCE_CHECKLIST.md
  - docs/ai/BLOCKERS.md
  - docs/ai/workflows/README.md
  - docs/ai/workflows/01_stabilization_fixes_test10.md
  - docs/ai/workflows/02_test_engine_performance.md
  - docs/ai/workflows/03_tray_and_menu_ux.md
  - AGENTS.md
  - LOCAL_AGENT_START_HERE.md
  - docs/ai/OTHER_AGENT_RULES.md
  - docs/ai/AGENT_COMMANDS.md
  - .github/* agent rules/prompts
  - .windsurf/rules/*
- What changed:
  - Added stable project navigation map.
  - Added staged workflow docs under `docs/ai/workflows/`.
  - Updated agent rules to read and maintain `CONTEXT_MAP.md` and follow workflow stage order.
  - No project logic changed.
- Verification command:
  - Docs-only check + `bash scripts/agent-verify.sh`
- Verification result:
  - Pending
- Remaining work:
  - Execute workflow Stage 1 (stabilization) when requested.

### YYYY-MM-DD HH:MM — <milestone title>

- Scope:
  - ...
- Files changed:
  - ...
- Verification:
  - Command(s):
    - ...
  - Result: PASS/FAIL
- Notes:
  - ...
- Next step:
  - ...

## Final summary template

When the task is complete, fill this section.

- What was implemented:
  - ...
- Files created/changed:
  - ...
- Verification:
  - ...
- Future / Planned:
  - ...
- Blockers:
  - ...
