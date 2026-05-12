# MASTER TASK - DedZapret clean rebuild

## Objective
Turn the current DedZapret repository into a clean, maintainable, portable Windows utility.

The application must preserve existing capabilities, but remove accidental complexity:
- inconsistent runtime paths;
- broken imported strategies;
- dirty release artifacts;
- stale state in portable releases;
- noisy logs;
- raw tracebacks in user flows;
- overloaded menu structure.

## Build mode
This is a **fresh rebuild** with reference to the existing repository as source material.
- Preserve useful behavior and requirements, not accidental code structure.
- Extract intent, write clean modules, cover with tests.
- The old repository is reference material only:
  - useful behavior;
  - bugs to avoid;
  - strategy logic;
  - UI/UX lessons;
  - tests and diagnostics lessons.
- Do not preserve old architecture if it is messy.

## Non-goals
- Do not rewrite the whole app from scratch.
- Do not remove existing features unless marked broken and approved.
- Do not invent new product features.
- Do not silently change Windows proxy/DNS/hosts/firewall.
- Do not ship fake empty `.bin` files.
- Do not treat missing runtime/preflight as domain test failures.

## Product direction
DedZapret is a Windows product layer over zapret/winws, Flowseal runtime examples, and StressOzz workflow ideas.

DedZapret must:
- normalize upstream strategies;
- validate assets before exposing strategies as runnable;
- manage portable paths safely;
- provide clean Russian UX;
- support diagnostics and rollback;
- separate zapret strategies from sing-box nodes/proxy.

## Source of truth
- Repository code + docs.
- Local agent workflow docs in `docs/ai/`.
- `docs/ai/DEDZAPRET_AGENT_RULES.md` — project-specific safety rules.
- `docs/ai/RUNTIME_SOURCE_POLICY.md` — upstream source roles.
- `docs/ai/development_history_merged.md` — history of bugs and regressions to avoid.
- `docs/ai/REGRESSION_PREVENTION_CHECKLIST.md` — mandatory checklist before releases.

## Required phases

### Phase 1 - Repository and packaging cleanup
- Audit current release workflow.
- Define clean portable layout.
- Exclude logs/results/telemetry/state from releases.
- Exclude __MACOSX, .DS_Store, ._*.
- Ensure first run generates state/logs/reports.
- Add package inspection test.

### Phase 2 - Path resolver and runtime asset model
- Implement one canonical path resolver.
- Separate upstream cache from working runtime assets.
- Resolve user lists from DedZapretData/data/lists.
- Resolve fake assets from runtime fake dir, with controlled repair from upstream cache.
- Never create empty fake .bin files.
- Empty user list files are allowed.

### Phase 3 - Strategy import and validation
- Parse Flowseal/StressOzz inputs.
- Normalize strategy paths.
- Generate DedZapret strategy definitions.
- Validate every referenced fake/list/ipset file.
- Invalid strategies must not be runnable.
- Builtin strategies v3/v8 must be fixed or marked unavailable.

### Phase 4 - Menu simplification
- Keep main menu short.
- Move low-level actions into advanced/diagnostics.
- Show clear status summary at top.
- Do not remove functions; relocate or mark Future/Planned.
- Replace raw exceptions with user-facing errors.

### Phase 5 - sing-box pipeline stabilization
- Keep sing-box nodes separate from zapret strategies.
- Validate node import.
- Require active node before start.
- Build and validate config before launch.
- Stop/restart must tolerate stale PID.

### Phase 6 - Diagnostics and bug report
- Mask secrets.
- Include structured runtime summary.
- Include missing assets.
- Include active strategy/node/config status.
- Do not include raw personal local paths unless explicitly allowed.

### Phase 7 - Verification
- Unit tests.
- Release package tests.
- Strategy validation tests.
- Offline-safe tests.
- Windows smoke test.

## Priority order
1. Phase 1 (Release packaging cleanup)
2. Phase 2 (Path resolver and runtime assets)
3. Phase 3 (Strategy import and validation)
4. Phase 4 (Menu simplification)
5. Phase 5 (sing-box pipeline)
6. Phase 6 (Diagnostics and bug report)
7. Phase 7 (Verification)

## Current staged workflow
See: `docs/ai/workflows/README.md`.

Workflow stages 00-07 define the clean rebuild path.
Previous workflow stages 01-03 (stabilization, test engine, tray/UX) are superseded by the new phased approach.
Agents must read all workflow stages for context, but execute them **strictly in order**
unless the human explicitly overrides.

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

## Global Definition of Done

A stage is complete only when:
- implementation matches the workflow scope;
- docs are updated;
- targeted tests pass;
- workflow-required tests pass;
- agent-verify passes;
- full pytest passes when reasonable for the change scope;
- any remaining failures are explicitly listed and classified as unrelated known failures or blockers;
- ACCEPTANCE_CHECKLIST is updated honestly;
- BLOCKERS is updated if anything remains unresolved.

A next stage must not start while the current stage has untriaged failing tests.

## Final response expected from agent
When finishing a task, provide:
- what was implemented (high-level);
- files changed/created;
- how to test/verify the implementation;
- any remaining blockers.