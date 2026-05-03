# Master Task

## Project

DedZapret / “ЗапретМенеджер на винду”

## Goal

Build and stabilize a **portable Windows utility** for managing:

- zapret / winws strategies;
- Flowseal / StressOzz strategy packs;
- sing-box / VPN (where applicable);
- diagnostics, logs, bug reports;
- future optional tray layer (no mandatory tray, no full GUI unless explicitly requested).

## Source of truth

- Repository code + docs.
- Local agent workflow docs in `docs/ai/`.

## Current staged workflow

See: `docs/ai/workflows/README.md`.

Agents must read all workflow stages for context, but execute them **strictly in order**
unless the human explicitly overrides.

## Priority order

1. Stabilization fixes.
2. Test engine performance.
3. Tray and menu UX.

## Non-goals unless explicitly requested

- Do not invent new original strategies.
- Do not make winws2 default.
- Do not make tray mandatory.
- Do not rewrite the whole application.
- Do not log secrets (tokens, subscription URLs with tokens, raw node links, private keys).

## Mandatory reads (Phase 0)

Before broad exploration or edits:

1. `AGENTS.md`
2. `LOCAL_AGENT_START_HERE.md`
3. `docs/ai/MASTER_TASK.md`
4. `docs/ai/CONTEXT_MAP.md`
5. `docs/ai/workflows/README.md`
6. The currently active workflow stage file(s) under `docs/ai/workflows/`
7. `docs/ai/PROGRESS.md`, `docs/ai/ACCEPTANCE_CHECKLIST.md`, `docs/ai/BLOCKERS.md`

## Verification

After every meaningful change:

- Windows: `./scripts/agent-verify.ps1`
- non-Windows: `bash scripts/agent-verify.sh`

## Definition of Done (DoD)

Work is considered complete only when:

- The active workflow stage(s) requirements are met.
- Relevant items in `docs/ai/ACCEPTANCE_CHECKLIST.md` are checked.
- Verification passes (script above).
- `docs/ai/PROGRESS.md` has an appended entry describing what changed and how it was verified.
- `docs/ai/BLOCKERS.md` contains only real blockers (or states no active blockers).
