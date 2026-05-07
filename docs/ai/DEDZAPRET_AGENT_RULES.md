# DedZapret Agent Rules

These rules apply to any work on DedZapret Manager or related Windows zapret/winws2 tooling.

## Project identity

DedZapret Manager is a Windows operations manager for Flowseal `winws2`, zapret strategies, testing, sing-box proxy/VPN, DNS/hosts/network operations, autostart/tray, profiles, diagnostics, updates, repair and bug reports.

It is not a simple `.bat` launcher.

## Mandatory read order

Before work begins, read:

1. `AGENTS.md`
2. `docs/ai/MASTER_TASK.md`
3. `docs/ai/RUNTIME_SOURCE_POLICY.md`
4. `docs/ai/REGRESSION_PREVENTION_CHECKLIST.md`
5. `docs/ai/STRATEGY_COMPATIBILITY_WORKFLOW.md`
6. `docs/ai/development_history_merged.md` if present
7. Relevant files under `docs/ai/prompts/`

## Work discipline

- Write a short plan in `docs/ai/PROGRESS.md` before editing code.
- Work one milestone at a time.
- Run verification after each meaningful milestone.
- Update `PROGRESS.md` after each milestone.
- Use `BLOCKERS.md` only for blockers that cannot be solved locally.
- Do not stop until DoD is complete or a real blocker is documented.

## Safety constraints

- No unsafe `shell=True`.
- No direct unsafe `ZipFile.extractall()`.
- No destructive updates without backup.
- No critical state writes without atomic replace.
- No Windows system operations without admin/preflight checks.
- No unverified downloads or execution of staged binaries.
- No secret leakage in logs, diagnostics or reports.
- No silent fallback from `winws2.exe` to `winws.exe`.

## Strategy constraints

- Every strategy must have source provenance.
- Every strategy must have compatibility status.
- Flowseal is the preferred Windows `winws2` runtime source.
- StressOzz is a workflow/strategy source that requires normalization.
- bol-van is the technical semantics reference.
- Do not auto-activate newly imported strategies.
- Experimental or risky strategies require confirmation.

## Logging constraints

Every meaningful runtime, updater, network, proxy, strategy, diagnostic or state-changing action must be audit-logged with masked sensitive values.

## Documentation constraints

If user-visible behavior changes, update docs. If architecture changes, update context maps. If a historical bug is addressed, mention the corresponding P-code/TASK item in `PROGRESS.md` or `CHANGELOG.md`.
