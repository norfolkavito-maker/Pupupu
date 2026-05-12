# AGENTS.md

## Mandatory startup rule
- Always read this file before starting implementation.

Additional mandatory startup reads (before broad exploration or edits):
- `docs/ai/MASTER_TASK.md`
- `docs/ai/CONTEXT_MAP.md`
- `docs/ai/workflows/README.md`
- `docs/ai/DEDZAPRET_AGENT_RULES.md`
- `docs/ai/RUNTIME_SOURCE_POLICY.md`
- `docs/ai/development_history_merged.md` (if present)

## Planning / execution
- PLAN/READ-ONLY is required before major changes.
- If user explicitly enables ACT MODE after planning, proceed with implementation.
- Do not mix unrelated scope.
- Do not perform large refactors unless strictly required by the task.

## Validation honesty
- Never claim "verified" unless commands were actually run.

## Test completion and QA gate rules

A task or stage is **NOT DONE** if relevant tests fail.

An agent may only mark a task/stage complete when:
- all required targeted tests pass;
- all tests required by the workflow pass;
- agent-verify passes;
- full pytest passes when reasonable for the change scope;
- OR every remaining failure is explicitly listed, reproduced, classified, and documented as an unrelated known failure with evidence.

The agent must **never** write:
- "complete" or "done";
- "ready for next stage";
- "Stage readiness: YES";
- "fully verified";
if relevant tests are failing or untriaged.

If tests fail, the agent must:
1. Stop progression to the next stage.
2. Capture exact failing tests.
3. Create a failure table:
   - test file;
   - test name;
   - exact error;
   - likely cause;
   - related to current changes: YES/NO/UNKNOWN;
   - action: fix now / document blocker / known unrelated failure.
4. Fix failures related to current changes.
5. Re-run verification.
6. Update PROGRESS, BLOCKERS, ACCEPTANCE_CHECKLIST, and agent_worklog honestly.

"Agent verification passed" is **not enough** if relevant pytest failures remain.

Targeted tests passing is **not enough** if full pytest reveals failures caused by the current change.

Masking/security/privacy tests are **relevant** to diagnostics and bug reports and must not be dismissed as unrelated without evidence.

**Never hide, summarize away, or hand-wave failing tests.**

## Test editing safety and anti-loop rules

Agents must not repeatedly delete/recreate the same test file while trying to fix failures.

If a test edit fails twice, stop and switch to a deterministic approach:
1. Read the current file.
2. Identify the exact failing assertion or syntax error.
3. Make one minimal patch.
4. Run `python3 -m py_compile <file>` for Python files.
5. Run the smallest relevant pytest command.
6. If still failing, report the exact blocker instead of looping.

Forbidden behavior:
- repeatedly creating files named `*_old.py`, `*_broken.py`, `*_fixed.py`, `*_corrected.py`;
- deleting and recreating the same test file multiple times without verifying syntax;
- writing invalid Python string literals;
- changing test expectations without understanding the product decision;
- weakening tests only to make them pass;
- claiming success while pytest collection fails;
- moving to the next stage while a test file has a syntax error.

Required behavior after editing any Python test file:
- run `python3 -m py_compile <changed_test_file>`;
- run targeted pytest for that file;
- only then run broader test suites.

If an agent gets stuck in an edit loop, it must stop, document the failure, and ask for a concrete decision or provide a minimal patch plan.

## Anti-loop and repeated-action rules

Agents must not repeat the same failed action indefinitely.

Hard limits:
- Do not run the exact same failing terminal command more than 2 times.
- Do not apply the same failed patch more than 2 times.
- Do not delete/recreate the same file more than 1 time in a single task.
- Do not repeat a diagnostic command after the result is already known.
- Do not keep running a command with a known syntax error.

If the same command or edit fails twice, the agent must stop and switch strategy:
1. State the repeated failure.
2. State the exact known fact from the failure.
3. Inspect the source file or test directly.
4. Make one minimal patch.
5. Run py_compile for changed Python files.
6. Run the smallest relevant pytest.
7. If still failing, report a blocker instead of looping.

Forbidden behavior:
- repeating the same python -c command while expecting a different result;
- repeating a command with unchanged input after unchanged output;
- repeatedly creating/removing *_old.py, *_broken.py, *_fixed.py, *_corrected.py files;
- deleting and recreating the same test file multiple times without verifying syntax;
- writing invalid Python string literals;
- changing test expectations without understanding the product decision;
- weakening tests only to make them pass;
- claiming success while pytest collection fails;
- moving to the next stage while a test file has a syntax error.

Required behavior after editing any Python test file:
- run python3 -m py_compile <changed_test_file>;
- run targeted pytest for that file;
- only then run broader test suites.

If an agent gets stuck in a loop, it must stop, summarize the failure, and ask for a concrete decision or provide a minimal patch plan.

## Worklog discipline
- After each completed phase, append an entry to `docs/agent_worklog.md` including:
  - timestamp;
  - task;
  - scope;
  - files changed;
  - commands run;
  - results;
  - not verified;
  - next step.

## Safety / rollback
- Windows/system/network changes must include rollback path.

## Secrets handling
- Never log secrets:
  - GitHub tokens;
  - subscription URLs with tokens;
  - proxy passwords;
  - cookies;
  - Authorization headers;
  - API keys;
  - private keys;
  - node UUIDs;
  - personal data.
- Diagnostic export must sanitize/redact secrets.
- Mask secrets in logs, diagnostics, crash reports and bug report ZIPs.

## Console output
- For Russian UI output in risk paths, use `safe_print` instead of raw `print`.

## zapret/winws guardrails
- Mark working only when PID/alive is confirmed.
- INVALID runtime/preflight must not be treated as domain failure for problem domains.
- Never create empty fake `.bin` files.

## sing-box guardrails
- sing-box nodes are separate from zapret strategies.
- Never enable system proxy or TUN silently.
- Backup system proxy before enabling app-controlled proxy.
- On stop/rollback, restore proxy/routes/DNS.
- TUN requires admin check, warning, and rollback path.

## Updater guardrails
- Old DedZapret.exe must not directly replace/run new exe in-place.
- Run updater script from TEMP.
- Backup before replacement.
- Never create nested `DedZapret/DedZapret.exe` layout.

---

# Universal coding-agent rules (repository-wide)

This section is intended as **universal instructions** for any AI coding agent
working in this repository.

## Source of truth
- The repository content (code + docs) is the primary source of truth.
- Task files under `docs/ai/` are also source of truth for the current task.
- If a requirement is missing/unclear, document it as **Future / Planned** or a
  **Blocker** (see below) instead of inventing behavior.

## Working mode
- Start in PLAN/READ-ONLY for non-trivial changes.
- Work in **small milestones**.
- After each milestone: update `docs/ai/PROGRESS.md` and run verification.

## No invented features
- Do not invent features, flags, settings, menu entries, network behavior, or
  file formats not explicitly described by task files or existing code.
- If something is "логично" but not requested/implemented, mark it as
  **Future / Planned**.

## Preserve existing behavior
- Do not refactor or rewrite unrelated code.
- Avoid mass formatting changes.
- Preserve public interfaces and configuration semantics unless task explicitly
  requires changes.

## Safety rules (general)
- Any risky Windows/system/network change must include:
  - explicit user confirmation;
  - backup/restore path;
  - clear rollback steps.
- Never enable system proxy / TUN silently.
- Use atomic writes for `config.yaml`, `state.json`, `current.json`, `nodes.json`,
  strategy index files and other critical state.

## Verification rule
- After every meaningful change, run:
  - On Windows: `./scripts/agent-verify.ps1`
  - On non-Windows: `bash scripts/agent-verify.sh`
- Never claim "verified" unless commands were actually run and succeeded.

## Completion rule
- A task is complete only when:
  - Definition of Done from `docs/ai/MASTER_TASK.md` is satisfied;
  - `docs/ai/ACCEPTANCE_CHECKLIST.md` items are checked;
  - verification scripts pass.
  - No secrets are exposed in logs, fixtures, reports, screenshots, or generated files.

## Blocker rule
- Use `docs/ai/BLOCKERS.md` only for **real blockers** that require human input.
- A blocker entry must contain exact command + exact error + suspected cause +
  proposed next step.
- Do not stop at the first error. At least one reasonable fix must be attempted first.

## Progress log rule
- Update `docs/ai/PROGRESS.md` after each milestone.
- Keep entries concise but actionable: what changed, where, how verified.

## Context map rule
- Before broad repository exploration, read `docs/ai/CONTEXT_MAP.md`.
- Use `CONTEXT_MAP.md` to locate likely files before scanning the whole repository.
- Update `CONTEXT_MAP.md` when project structure, entry points, important modules,
  commands, paths, or workflows change.
- Do not use `CONTEXT_MAP.md` as a progress log.
- Track completed work in `docs/ai/PROGRESS.md`.
- Track acceptance status in `docs/ai/ACCEPTANCE_CHECKLIST.md`.
- Track blockers in `docs/ai/BLOCKERS.md`.
- Do not delete completed tasks from checklists; mark them checked and keep the history.

## Workflows (staged) rule
- Before starting feature work, read `docs/ai/workflows/README.md`.
- Read all workflow stages for context.
- Execute stages strictly in order unless the human explicitly overrides.

## Git rules
- Unless explicitly told otherwise:
  - do not push directly to `main` or `master`;
  - prefer a feature branch;
  - keep changes reviewable;
  - do not mix unrelated tasks;
  - do not rewrite unrelated files;
  - do not reformat the entire project unless required.

## Tests and quality
- When behavior changes, add or update tests.
- Prefer deterministic tests.
- Avoid tests that depend on:
  - real network access;
  - real user secrets;
  - local absolute paths;
  - machine-specific state.
- If external binaries are required, mock or gate tests safely.

## Documentation
- If user-visible behavior changes, update docs in the same milestone.
- Add "Future / Planned" notes rather than partially implementing.
- Do not leave stale documentation that contradicts the code.

## UI / UX rules for desktop apps
- User-facing Russian text should be clear and consistent.
- Dangerous actions must have confirmations and rollback.
- Keep UI responsive: long operations should show progress.
- Do not hide critical errors.
- Distinguish existing features from `Future / Planned`.
- Show diagnostics and logs in copyable form.
- Avoid technical jargon in user-facing Russian text unless necessary.

## Windows utility rules
- Paths: be explicit about portable/data dirs, avoid hardcoded local paths.
- Admin checks must be explicit and user-visible.
- Network changes (DNS, proxy, firewall) must be reversible.
- Use safe paths.
- Keep logs and state under the app data root defined by the project.
- Do not write to system directories without explicit requirement.
- Do not break non-admin launch if the app currently supports it.

## Upstream source roles

- `bol-van/zapret` is the canonical technical source for zapret semantics:
  desync methods, hostlist/ipset/autohostlist, fake packets, blockcheck logic
  and low-level option meaning.
- `Flowseal/zapret-discord-youtube` is the Windows runtime source: `winws2`,
  WinDivert layout, `bin/lists/fake/utils`, Windows BAT strategy examples
  and service lifecycle.
- `StressOzz/Zapret-Manager` is the workflow and strategy reference: strategy
  menu logic, Flowseal strategy selection, `Dv/Yv/Gv`, RKN/exclude/wssize
  and test flow ideas.
- DedZapret Manager is the product layer: it normalizes, validates, tests,
  runs and diagnoses these sources safely on Windows.

Do not copy upstream scripts blindly. Extract intent, normalize to DedZapret
models, validate, then apply through safe Windows adapters.

## DedZapret-specific safety rules

Mandatory safety rules for this project:

- Do not use `shell=True` for subprocess calls. Pass process arguments as arrays/lists.
- Do not use `ZipFile.extractall()` directly. Use safe extraction with path traversal validation.
- Do not overwrite user files, custom strategies, user lists, nodes, profiles, config or state without backup.
- Do not start downloaded binaries until source, path and hash/checksum are verified or explicitly approved.
- Do not modify hosts/DNS/firewall/system proxy without an audit log event and rollback path.
- Do not log secrets, proxy links, subscription URLs with credentials, node UUIDs, passwords, tokens, private keys or personal data.
- Do not silently fallback from `winws2.exe` to `winws.exe`.
- Do not auto-activate newly imported Flowseal or StressOzz strategies.
- Do not remove menu items. If not implemented, keep the item and mark it as `Future / Planned` or `Not implemented`.
- Check administrator rights before hosts, DNS, firewall, WinDivert, Task Scheduler, service, driver or registry operations.
- If administrator rights are missing, fail clearly and do not pretend the operation succeeded.

## Runtime audit logging rule

Every meaningful application action must produce a structured audit event.

Must log:
- app start / app exit;
- preflight start / result;
- runtime start / stop / restart;
- strategy selected / applied / rejected;
- strategy import / normalization / validation;
- test started / cancelled / completed;
- Flowseal sync / StressOzz sync;
- repair runtime;
- config/state/current write;
- backup / restore;
- hosts change;
- DNS change / restore;
- firewall change;
- system proxy change;
- autostart enable / disable / repair;
- tray action;
- bug report creation;
- crash / handled error.

Audit events must include timestamp, action, component, success/failure,
user-facing message, files touched, process id if relevant, strategy/profile id
if relevant, and masked sensitive values.

## History and regression prevention

Before rebuilding risky areas, read `docs/ai/development_history_merged.md`
if present. Use it as a regression checklist for P-codes, TASK items, UX
complaints and DEV issues. Do not reintroduce old defects such as unsafe unzip,
`shell=True`, config/state corruption, user file overwrite, silent admin
failure, missing checksums, file-in-use update errors or secret leakage.

If `development_history_merged.md` is missing, proceed using
`docs/ai/REGRESSION_PREVENTION_CHECKLIST.md`.

## Final response expected from agent
When finishing a task, provide:
- what was implemented (high-level);
- files changed/created;
- verification commands run + results;
- any remaining "Future / Planned" items;
- any blockers (if present) with next steps.