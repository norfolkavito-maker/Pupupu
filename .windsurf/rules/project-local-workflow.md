# Windsurf rule: project-local-workflow

This repository uses a local “task packet” workflow.

## Required reads

- `AGENTS.md`
- `docs/ai/MASTER_TASK.md`
- all `docs/ai/prompts/*.md`

## Workflow

1. Plan in milestones.
2. Implement one milestone.
3. Self-review using:
   - `docs/ai/ACCEPTANCE_CHECKLIST.md`
   - `docs/ai/PROGRESS.md`
   - `docs/ai/BLOCKERS.md`
4. Run verification script.
5. Update progress log.

## Guardrails

- Do not invent features.
- Preserve existing behavior unless explicitly changed.
- Avoid unrelated refactors.
- Use BLOCKERS only when truly blocked.

## Stop condition

Stop only when DoD in `docs/ai/MASTER_TASK.md` is satisfied.
