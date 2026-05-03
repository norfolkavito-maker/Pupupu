# OTHER_AGENT_RULES (pasteable)

Use this when an agent/tool does not automatically read `AGENTS.md`.

## Mandatory files to read (before any edits)

1. `AGENTS.md`
2. `docs/ai/MASTER_TASK.md`
3. All files under `docs/ai/prompts/`
4. `docs/ai/ACCEPTANCE_CHECKLIST.md`
5. `docs/ai/PROGRESS.md`
6. `docs/ai/BLOCKERS.md`

## Work loop

1. Plan in small milestones.
2. Implement exactly one milestone.
3. Self-review:
   - no invented features,
   - preserve behavior,
   - no secrets,
   - tests/docs updated.
4. Run verification:
   - Windows: `./scripts/agent-verify.ps1`
   - non-Windows: `bash scripts/agent-verify.sh`
5. Update `docs/ai/PROGRESS.md`.
6. Repeat.

## Stop condition

Stop only when:
- Definition of Done in `docs/ai/MASTER_TASK.md` is satisfied;
- Acceptance checklist is checked;
- verification passes;
- no unresolved critical blockers.

## Final answer format

- What was implemented (high-level)
- Files created/changed
- Verification commands run + results
- Future / Planned items
- Blockers (if any) + next steps
