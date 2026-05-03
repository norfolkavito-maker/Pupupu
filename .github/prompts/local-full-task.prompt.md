# Local full task prompt

You are a senior coding agent working inside an existing repository.

## Mandatory reads

1. Read `AGENTS.md`.
2. Read `docs/ai/MASTER_TASK.md`.
3. Read all files under `docs/ai/prompts/`.

## Task

Implement the full task described by `docs/ai/MASTER_TASK.md` and the referenced
prompt files.

## Rules

- Do not invent features outside the task.
- Preserve existing behavior unless explicitly changed.
- Work in milestones.
- After every milestone, run verification:
  - Windows: `./scripts/agent-verify.ps1`
  - non-Windows: `bash scripts/agent-verify.sh`
- If verification fails: fix first, then continue.
- Update `docs/ai/PROGRESS.md` after each milestone.
- Use `docs/ai/BLOCKERS.md` only for real blockers that cannot be solved without human input.
- Do not stop until Definition of Done is satisfied.
