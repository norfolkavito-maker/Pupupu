# Self-review prompt

Perform a strict self-review of your changes.

## Inputs to consult

- `AGENTS.md`
- `docs/ai/MASTER_TASK.md`
- `docs/ai/ACCEPTANCE_CHECKLIST.md`
- `docs/ai/PROGRESS.md`
- `docs/ai/BLOCKERS.md`
- List of changed files (`git status --short`)
- Diff (`git diff`)

## Checklist

1. Scope correctness:
   - Are changes strictly related to the task packet?
   - Any unrelated refactors/formatting? If yes, revert.

2. Source of truth:
   - Did you follow repository + task files?
   - Did you avoid inventing features? If something is missing, mark **Future / Planned**.

3. Secrets/safety:
   - Ensure no tokens/credentials/private keys/personal data are in code/logs/docs.

4. Tests and verification:
   - Did you run `./scripts/agent-verify.ps1` or `bash scripts/agent-verify.sh`?
   - Did existing tests pass?

5. Progress and blockers:
   - Is `docs/ai/PROGRESS.md` updated with this milestone?
   - Are blockers documented only when truly blocked?

## Output format

- Summary of changes
- Risks found (if any)
- Verification commands + results
- Remaining TODOs
