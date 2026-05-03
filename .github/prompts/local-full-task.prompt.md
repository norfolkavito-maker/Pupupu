# Local full task prompt

You are a senior coding agent working inside an existing repository.

## Mandatory reads

1. Read `AGENTS.md`.
2. Read `docs/ai/MASTER_TASK.md`.
3. Read `docs/ai/CONTEXT_MAP.md` (before broad exploration).
4. Read `docs/ai/workflows/README.md` and all stage files under `docs/ai/workflows/`.
5. Read all files under `docs/ai/prompts/` (legacy/optional).

## Task

Implement the full task described by `docs/ai/MASTER_TASK.md` and the referenced
prompt files.

## Rules

- Do not invent features outside the task.
- Preserve existing behavior unless explicitly changed.
- Work in milestones.
- Before broad repository exploration, use `docs/ai/CONTEXT_MAP.md`.
- Update `docs/ai/CONTEXT_MAP.md` when structure/entry points/commands/workflows change.
- Do not use `CONTEXT_MAP.md` as a progress log.
- Follow staged workflows in `docs/ai/workflows/` (execute in order unless explicitly overridden).
- After every milestone, run verification:
  - Windows: `./scripts/agent-verify.ps1`
  - non-Windows: `bash scripts/agent-verify.sh`
- If verification fails: fix first, then continue.
- Update `docs/ai/PROGRESS.md` after each milestone.
- Use `docs/ai/BLOCKERS.md` only for real blockers that cannot be solved without human input.
- Do not stop until Definition of Done is satisfied.
