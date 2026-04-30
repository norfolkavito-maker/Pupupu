# AGENTS.md

## Mandatory startup rule
- Always read this file before starting implementation.

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