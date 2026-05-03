# Prompt 02 — UI / UX (PLACEHOLDER)

> Replace this placeholder with the real prompt.

## Status

- Status: placeholder

## Role

You are a senior coding agent improving UI/UX in an existing desktop-oriented app.

## Scope

- UI menus, prompts, confirmations, and user-facing texts.

## Requirements

- Follow `AGENTS.md`.
- User-facing Russian text must be clear and consistent.
- Dangerous operations must require confirmation and provide rollback path.
- Keep UI responsive; long operations should show progress.

## Non-goals

- Do not invent new menu items unless explicitly requested.
- Do not refactor unrelated code.

## Existing behavior to preserve

- Preserve current menu navigation and existing command semantics.

## Files/modules likely involved

- `app/zapret_manager/ui/*`
- `app/zapret_manager/core/confirm.py`

## Acceptance criteria

- All requirements implemented; no regressions.

## Verification

```text
./scripts/agent-verify.ps1
bash scripts/agent-verify.sh
```

## Notes

- Replace this placeholder with the real prompt.
