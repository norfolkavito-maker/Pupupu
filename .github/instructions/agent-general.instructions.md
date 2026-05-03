---
applyTo: "**"
---

# Agent — General Instructions

- Follow `AGENTS.md`.
- Read `docs/ai/MASTER_TASK.md` and all `docs/ai/prompts/*.md` before major edits.
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
