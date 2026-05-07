# Workflow 00 — History and Regression Audit

## Goal

Inspect the original repository history and `development_history_merged.md` to prevent reintroducing old bugs, unsafe patterns and broken workflows.

## Required inputs

- `docs/ai/development_history_merged.md` if present.
- Git commit history.
- Existing tests.
- Old issue list: P-001..P-014, TASK 1..11, UX-001..UX-004, DEV-001..DEV-003.

## Required workflow

1. Read `development_history_merged.md`.
2. Create a checklist of all P-codes, TASK items, UX complaints and DEV issues.
3. Inspect git history:
   - `git log --oneline --decorate --all`
   - `git log --stat`
   - `git log -p -- <high-risk-file>`
4. For each old issue, determine status:
   - fixed;
   - partially fixed;
   - still open;
   - unknown / needs verification.
5. Search for dangerous patterns:
   - `shell=True`
   - `extractall(`
   - hardcoded `C:\Users`
   - direct hosts edits
   - direct DNS/netsh/powershell calls
   - unsafe deletes
   - config/state writes without atomic replace
   - logs containing tokens, subscription URLs, UUIDs or passwords
6. Produce or update:
   - `docs/ai/HISTORY_AUDIT.md`
   - `docs/ai/REGRESSION_PREVENTION_CHECKLIST.md`
7. Do not modify runtime logic during this workflow.

## Output format for HISTORY_AUDIT.md

For each issue:

- ID
- Original problem
- Evidence from history
- Current status
- Remaining risk
- Required follow-up
- Tests needed
