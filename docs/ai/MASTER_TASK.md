# Master Task

## Project

DedZapret Manager — портативная Windows-утилита для управления DPI-desync (zapret/winws2), стратегиями обхода, тестированием, proxy/VPN, автозапуском, системным треем, профилями и диагностикой.

## Goal

Build and stabilize a **portable Windows utility** for managing:

- zapret / winws2 strategies;
- Flowseal / StressOzz strategy packs;
- sing-box / VPN (where applicable);
- diagnostics, logs, bug reports;
- tray layer (optional, config-gated);
- profiles, autostart, watcher.

## Build mode

This is a **fresh rebuild** using the existing repository as reference.
- Preserve useful behavior and requirements, not accidental code structure.
- Do not copy messy modules directly.
- Extract intent, write clean modules, cover with tests.
- The old repository (Git history) is reference material for bugs to avoid, UI/UX lessons, strategy logic, and test scenarios.

## Source of truth

- Repository code + docs.
- Local agent workflow docs in `docs/ai/`.
- `docs/ai/DEDZAPRET_AGENT_RULES.md` — project-specific safety rules.
- `docs/ai/RUNTIME_SOURCE_POLICY.md` — upstream source roles.
- `docs/ai/development_history_merged.md` — history of bugs and regressions to avoid.
- `docs/ai/REGRESSION_PREVENTION_CHECKLIST.md` — mandatory checklist before releases.

## Current staged workflow

See: `docs/ai/workflows/README.md`.

Agents must read all workflow stages for context, but execute them **strictly in order**
unless the human explicitly overrides.

## Priority order

1. Stabilization fixes.
2. Test engine performance.
3. Tray and menu UX.
4. Documentation and rules consolidation.

## Non-goals unless explicitly requested

- Do not invent new original strategies.
- Do not make winws2 default.
- Do not make tray mandatory.
- Do not rewrite the whole application at once.
- Do not log secrets (tokens, subscription URLs with tokens, raw node links, private keys, node UUIDs).
- Do not perform migration-in-place of old architecture — this is a fresh build with reference.

## Mandatory reads (Phase 0)

Before broad exploration or edits:

1. `AGENTS.md`
2. `LOCAL_AGENT_START_HERE.md`
3. `docs/ai/MASTER_TASK.md`
4. `docs/ai/CONTEXT_MAP.md`
5. `docs/ai/workflows/README.md`
6. The currently active workflow stage file(s) under `docs/ai/workflows/`
7. `docs/ai/PROGRESS.md`, `docs/ai/ACCEPTANCE_CHECKLIST.md`, `docs/ai/BLOCKERS.md`
8. `docs/ai/DEDZAPRET_AGENT_RULES.md`
9. `docs/ai/RUNTIME_SOURCE_POLICY.md`
10. `docs/ai/development_history_merged.md` (if present)
11. `docs/ai/REGRESSION_PREVENTION_CHECKLIST.md` (before risky operations)

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
- No secrets are exposed in logs, fixtures, reports, screenshots, or generated files.
- `docs/ai/REGRESSION_PREVENTION_CHECKLIST.md` items are satisfied before release.