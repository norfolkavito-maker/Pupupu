# Windsurf rule: project-local-workflow

This repository uses a local "task packet" workflow.

## Required reads

- `AGENTS.md`
- `docs/ai/MASTER_TASK.md`
- `docs/ai/CONTEXT_MAP.md`
- `docs/ai/workflows/README.md`
- all `docs/ai/prompts/*.md`
- `docs/ai/DEDZAPRET_AGENT_RULES.md`
- `docs/ai/RUNTIME_SOURCE_POLICY.md`
- `docs/ai/development_history_merged.md` (if present)

## Workflow

1. Plan in milestones.
2. Implement one milestone.
3. Self-review using:
   - `docs/ai/ACCEPTANCE_CHECKLIST.md`
   - `docs/ai/PROGRESS.md`
   - `docs/ai/BLOCKERS.md`
   - `docs/ai/REGRESSION_PREVENTION_CHECKLIST.md`
4. Run verification script.
5. Update progress log.

Stages:
- Follow workflow stage order from `docs/ai/workflows/README.md` unless explicitly overridden.

## Guardrails

- Do not invent features.
- Preserve existing behavior unless explicitly changed.
- Avoid unrelated refactors.
- Use BLOCKERS only when truly blocked.
- Prefer CONTEXT_MAP before full-repo scans; update it when structure changes.
- Before rebuilding risky areas, read `docs/ai/development_history_merged.md` and `docs/ai/REGRESSION_PREVENTION_CHECKLIST.md`.

## Stop condition

Stop only when DoD in `docs/ai/MASTER_TASK.md` is satisfied.