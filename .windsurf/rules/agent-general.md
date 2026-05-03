# Windsurf rule: agent-general

- Follow `AGENTS.md`.
- Before major edits, read:
  - `docs/ai/MASTER_TASK.md`
  - `docs/ai/CONTEXT_MAP.md`
  - `docs/ai/workflows/README.md`
  - all files under `docs/ai/prompts/`
- Work in small milestones.
- After each milestone:
  - run verification (`./scripts/agent-verify.ps1` on Windows or `bash scripts/agent-verify.sh` elsewhere)
  - update `docs/ai/PROGRESS.md`
- Use `docs/ai/BLOCKERS.md` only for real blockers with exact command + error.
- Do not invent features; mark missing items as **Future / Planned**.
- Use `CONTEXT_MAP.md` to locate likely files before scanning the whole repository.
- Update `CONTEXT_MAP.md` when structure/entry points/important paths change.
- Do not use `CONTEXT_MAP.md` as a progress log.
- Follow staged workflows in `docs/ai/workflows/` (execute in order unless explicitly overridden).
- Stop only when Definition of Done in `docs/ai/MASTER_TASK.md` is satisfied.
