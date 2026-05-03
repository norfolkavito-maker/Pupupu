---
applyTo: "**"
---

# Agent — General Instructions

- Follow `AGENTS.md`.
- Read `docs/ai/MASTER_TASK.md` and all `docs/ai/prompts/*.md` before major edits.
- Before broad repository exploration, read `docs/ai/CONTEXT_MAP.md`.
- Read `docs/ai/workflows/README.md` and follow staged workflow order unless explicitly overridden.
- Use `CONTEXT_MAP.md` to locate likely files before scanning the whole repository.
- Update `CONTEXT_MAP.md` when structure/entry points/important paths change.
- Do not use `CONTEXT_MAP.md` as a progress log.
- Treat repository files + `docs/ai/*` as source of truth.
- Do not invent features; mark missing logical items as **Future / Planned**.
- Preserve existing behavior unless explicitly changed.
- Work in small milestones.
- Verify after meaningful changes:
  - Windows: `./scripts/agent-verify.ps1`
  - non-Windows: `bash scripts/agent-verify.sh`
- Update `docs/ai/PROGRESS.md` after each milestone.
- Use `docs/ai/BLOCKERS.md` only for real blockers with exact command + error.
- Never expose secrets.
