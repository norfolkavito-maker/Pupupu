# Copilot Instructions (Repository)

Follow these rules when generating or editing code in this repository.

## Mandatory reads

1. `AGENTS.md`
2. `docs/ai/MASTER_TASK.md`
3. All files in `docs/ai/prompts/`

## Core rules

- Treat the repository + `docs/ai/*` as source of truth.
- Do not invent features. If something seems logical but is not specified, mark it as **Future / Planned**.
- Preserve existing behavior unless the task explicitly changes it.
- Work in small milestones.
- After every meaningful change, run verification:
  - Windows: `./scripts/agent-verify.ps1`
  - non-Windows: `bash scripts/agent-verify.sh`
- Update `docs/ai/PROGRESS.md` after each milestone.
- Use `docs/ai/BLOCKERS.md` only for real blockers with exact command + error.
- Never expose secrets (tokens, credentials, subscription URLs with tokens, private keys, personal data).
- Do not push directly to main/master unless explicitly instructed.
