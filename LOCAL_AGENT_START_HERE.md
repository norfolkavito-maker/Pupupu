# Local Agent старт: copy-paste промпты

Этот файл предназначен для быстрого запуска **локальных** AI-агентов внутри
данного репозитория (Windsurf / Copilot / Claude / ChatGPT и т.д.).

## Полный стартовый промпт (рекомендуется)

Скопируй и вставь агенту:

```text
Read AGENTS.md and docs/ai/MASTER_TASK.md.

You must implement the full task described in docs/ai/MASTER_TASK.md and the four prompt files referenced by it.

Work locally in this repository.

Rules:
- Do not invent features outside the task.
- Preserve existing behavior unless the task explicitly changes it.
- Work in milestones.
- After every milestone, run scripts/agent-verify.ps1.
- If verification fails, fix the failure before continuing.
- Update docs/ai/PROGRESS.md after each milestone.
- Use docs/ai/BLOCKERS.md only for real blockers that cannot be solved without human input.
- Do not stop until the Definition of Done is complete or a real blocker is documented with exact command, error, suspected cause, and proposed next step.

Start by:
1. Reading AGENTS.md.
2. Reading docs/ai/MASTER_TASK.md.
3. Reading all files in docs/ai/prompts/.
4. Inspecting the current repository structure.
5. Writing a short implementation plan into docs/ai/PROGRESS.md.
6. Beginning implementation.
```

## Короткий стартовый промпт

```text
Read AGENTS.md and docs/ai/MASTER_TASK.md. Complete the task fully. Verify with scripts/agent-verify.ps1 after each milestone. Update PROGRESS.md. Stop only when DoD is complete or a real blocker is documented.
```
