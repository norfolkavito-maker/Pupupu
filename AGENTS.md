# AGENTS.md

## Mandatory startup rule
- Always read this file before starting implementation.

Additional mandatory startup reads (before broad exploration or edits):
- `docs/ai/MASTER_TASK.md`
- `docs/ai/CONTEXT_MAP.md`
- `docs/ai/workflows/README.md`

## Planning / execution
- PLAN/READ-ONLY is required before major changes.
- If user explicitly enables ACT MODE after planning, proceed with implementation.
- Do not mix unrelated scope.
- Do not perform large refactors unless strictly required by the task.

## Validation honesty
- Never claim "verified" unless commands were actually run.

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
  - private keys.
- Diagnostic export must sanitize/redact secrets.

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
- If something is “логично” but not requested/implemented, mark it as
  **Future / Planned**.

## Preserve existing behavior
- Do not refactor or rewrite unrelated code.
- Avoid mass formatting changes.
- Preserve public interfaces and configuration semantics unless task explicitly
  requires changes.

## Safety rules
- Any risky Windows/system/network change must include:
  - explicit user confirmation;
  - backup/restore path;
  - clear rollback steps.
- Never enable system proxy / TUN silently.

## Verification rule
- After every meaningful change, run:
  - On Windows: `./scripts/agent-verify.ps1`
  - On non-Windows: `bash scripts/agent-verify.sh`
- Never claim “verified” unless commands were actually run and succeeded.

## Completion rule
- A task is complete only when:
  - Definition of Done from `docs/ai/MASTER_TASK.md` is satisfied;
  - `docs/ai/ACCEPTANCE_CHECKLIST.md` items are checked;
  - verification scripts pass.

## Blocker rule
- Use `docs/ai/BLOCKERS.md` only for **real blockers** that require human input.
- A blocker entry must contain exact command + exact error + suspected cause +
  proposed next step.

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
- Do not push directly to `main/master` unless explicitly instructed.
- Keep commits small and scoped.
- Include meaningful commit messages.

## Tests and quality
- Keep changes minimal and targeted.
- Add/update tests when behavior changes (when reasonable).
- Prefer deterministic tests and stable output.

## Documentation
- If user-visible behavior changes, update docs in the same milestone.
- Add "Future / Planned" notes rather than partially implementing.

## UI / UX rules for desktop apps
- User-facing Russian text should be clear and consistent.
- Dangerous actions must have confirmations and rollback.
- Keep UI responsive: long operations should show progress.

## Windows utility rules
- Paths: be explicit about portable/data dirs, avoid hardcoded local paths.
- Admin checks must be explicit and user-visible.
- Network changes (DNS, proxy, firewall) must be reversible.

## Final response expected from agent
When finishing a task, provide:
- what was implemented (high-level);
- files changed/created;
- verification commands run + results;
- any remaining "Future / Planned" items;
- any blockers (if present) with next steps.