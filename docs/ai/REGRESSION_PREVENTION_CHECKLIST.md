# Regression Prevention Checklist

Use this checklist before implementing or reviewing runtime, updater, strategy, tests, diagnostics, proxy, DNS, hosts, firewall, autostart or packaging changes.

## Critical historical problems

- [ ] P-001: No unsafe ZIP extraction / path traversal risk.
- [ ] P-002: Runtime update does not overwrite user configs, lists or custom strategies.
- [ ] P-003: No unsafe `shell=True` with user input, paths, URLs, strategies or domains.
- [ ] P-004: Uninstall/cleanup removes only app-owned files.
- [ ] P-005: Downloads and binaries are verified by checksum or explicit approval.
- [ ] P-006: Admin rights are checked before system operations.
- [ ] P-007: config/state/current writes are atomic and backed up.
- [ ] P-008: Menu input validation cannot cause endless spam/loops.
- [ ] P-010: Runtime update checks and stops running winws/winws2 processes safely.
- [ ] P-014: Logs, diagnostics and bug reports mask secrets.

## Required product tasks

- [ ] TASK 1: Baseline test without zapret exists.
- [ ] TASK 2-3: Quick and full test modes exist and explain DNS/TCP/HTTP failure reason.
- [ ] TASK 4: Problem domains are stored with metadata.
- [ ] TASK 5: Auto-tune/test-all produces ranked strategies and does not auto-apply risky options.
- [ ] TASK 6: Repair runtime checks structure, downloads safely, verifies hashes and preserves user files.
- [ ] TASK 8-9: Diagnostics and bug report ZIP include enough data and mask secrets.
- [ ] TASK 10: Updater handles self-update, stops processes, backs up, verifies and preserves user data.
- [ ] TASK 11: sing-box proxy layer supports import, preview, active node, health, config and ports.

## UX requirements

- [ ] Menus include short explanations.
- [ ] Long tests show progress and can be cancelled safely.
- [ ] Tray has quick actions and status.
- [ ] Discord repair/test flow exists or is marked Future / Planned.
- [ ] Not implemented menu items are preserved and clearly labeled.

## Development-agent risks

- [ ] Agent read actual files before search/replace.
- [ ] No empty SEARCH blocks or blind replace.
- [ ] Syntax/compile check was run after changes.
- [ ] Verification script passed or blocker was documented.
