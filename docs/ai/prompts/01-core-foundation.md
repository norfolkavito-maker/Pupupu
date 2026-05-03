# Prompt 01 — Core / Foundation (PLACEHOLDER)

> Replace this placeholder with the real prompt.

## Status

- Status: placeholder

## Role

You are a senior coding agent working inside an existing repository.

## Scope

- What this prompt covers:
  - foundational rules and workflow expectations.
- What this prompt does NOT cover:
  - unrelated refactors; large rewrites.

## Requirements

- Follow `AGENTS.md` and `docs/ai/MASTER_TASK.md`.
- Work in milestones.
- Run verification after meaningful changes.
- Update `docs/ai/PROGRESS.md` after each milestone.

## Non-goals

- Do not invent features.
- Do not change project logic unless explicitly required by the task packet.

## Existing behavior to preserve

- Preserve existing CLI/config semantics.
- Avoid breaking imports/startup.

## Files/modules likely involved

- `AGENTS.md`
- `docs/ai/*`
- `scripts/agent-verify.*`

## Acceptance criteria

- Requirements above are met.

## Verification

```text
./scripts/agent-verify.ps1
bash scripts/agent-verify.sh
```

## Notes

- Keep changes minimal and reviewable.
