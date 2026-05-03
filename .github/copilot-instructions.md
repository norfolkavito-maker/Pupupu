# Copilot Instructions (Repository)

Follow these rules when generating or editing code in this repository.

## Mandatory reads

1. `AGENTS.md`
2. `docs/ai/MASTER_TASK.md`
3. `docs/ai/CONTEXT_MAP.md`
4. `docs/ai/workflows/README.md` + all stage files under `docs/ai/workflows/`
3. All files in `docs/ai/prompts/`

## Core rules

- Treat the repository + `docs/ai/*` as source of truth.
- Do not invent features. If something seems logical but is not specified, mark it as **Future / Planned**.
- Preserve existing behavior unless the task explicitly changes it.
- Work in small milestones.
- Before broad repository exploration, read `docs/ai/CONTEXT_MAP.md`.
- Use `CONTEXT_MAP.md` to locate likely files before scanning the whole repository.
- Update `CONTEXT_MAP.md` when structure/entry points/commands/workflows change.
- Do not use `CONTEXT_MAP.md` as a progress log.
- Follow staged workflows in `docs/ai/workflows/` (execute in order unless explicitly overridden).
- After every meaningful change, run verification:
  - Windows: `./scripts/agent-verify.ps1`
  - non-Windows: `bash scripts/agent-verify.sh`
- Update `docs/ai/PROGRESS.md` after each milestone.
- Use `docs/ai/BLOCKERS.md` only for real blockers with exact command + error.
- Never expose secrets (tokens, credentials, subscription URLs with tokens, private keys, personal data).
- Do not push directly to main/master unless explicitly instructed.
