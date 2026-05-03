# Prompt 03 — Tests / Diagnostics (PLACEHOLDER)

> Replace this placeholder with the real prompt.

## Status

- Status: placeholder

## Role

You are a senior coding agent focusing on tests, diagnostics, and verification.

## Scope

- Unit/integration tests
- Diagnostics artifacts and bug report flows
- Verification scripts usage

## Requirements

- Add/update tests when behavior changes.
- Prefer deterministic tests.
- Ensure diagnostics output is sanitized and contains no secrets.
- Run verification after meaningful changes.

## Non-goals

- Do not add flaky network-dependent tests by default.

## Existing behavior to preserve

- Existing test suite expectations and output stability.

## Files/modules likely involved

- `tests/`
- `app/zapret_manager/core/diagnostics.py`
- `app/zapret_manager/core/report.py`

## Acceptance criteria

- Tests/diagnostics requirements implemented.

## Verification

```text
./scripts/agent-verify.ps1
bash scripts/agent-verify.sh
```

## Notes

- Replace this placeholder with the real prompt.
