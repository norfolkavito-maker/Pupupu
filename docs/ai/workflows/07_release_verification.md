# Workflow 07 — Release verification

## Scope
Ensure that before releasing, all tests pass, the package is clean, strategies are validated, and no raw tracebacks appear in normal user flows.

## Tasks

### 7.1 Unit tests
- Run `python3 -m pytest -q`.
- Run `python3 -m unittest discover -s tests -p '*_unittest.py' -v`.
- All tests must pass. No failing or skipped tests without documented reason.

### 7.2 Release package tests
- Inspect release archive for prohibited content:
  - No logs, sessions, reports from developer machine.
  - No __MACOSX, .DS_Store, ._* files.
  - No absolute local paths (C:\Users\...).
- Verify first run generates state/logs/reports automatically.
- Verify empty user list files are accepted.

### 7.3 Strategy validation tests
- Every visible runnable strategy must pass preflight validation.
- Invalid strategies must be hidden or clearly marked.

### 7.4 Offline-safe tests
- All unit tests must work offline (no real network calls).
- Use mocks for GitHub/upstream downloads.

### 7.5 Windows smoke test (manual)
- Test on Windows 10/11 x64:
  - First run: clean state generation.
  - Strategy selection and validation.
  - winws start/stop.
  - sing-box start/stop.
  - Diagnostics and bug report creation.
  - Update check (if applicable).
  - Tray feature (if enabled).

### 7.6 No raw traceback rule
- Normal menu flows must not show raw Python tracebacks.
- All user-facing errors must be clean Russian status messages.
- Tracebacks go to logs and bug reports only.

## Acceptance criteria
- [ ] All unit tests pass.
- [ ] Release package is clean.
- [ ] All runnable strategies pass validation.
- [ ] Tests are offline-safe.
- [ ] Windows smoke test passes (manual).
- [ ] No raw tracebacks in normal user flows.
- [ ] Release artifact is shippable.