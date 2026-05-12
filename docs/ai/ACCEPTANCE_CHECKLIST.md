# ACCEPTANCE_CHECKLIST - Clean rebuild

Отмечай чекбоксы по мере выполнения.

## Release package
- [ ] Portable archive contains DedZapret.exe.
- [ ] Portable archive contains DedZapretData.
- [ ] Portable archive contains required runtime binaries.
- [x] Portable archive does not contain test logs.
- [x] Portable archive does not contain session jsonl files.
- [x] Portable archive does not contain reports from developer machine.
- [x] Portable archive does not contain telemetry/results from developer machine.
- [x] Portable archive does not contain __MACOSX, .DS_Store, or ._*.
- [x] Portable archive does not contain absolute C:\Users\... paths.
- [ ] Fresh package starts with clean state.

## Runtime assets
- [ ] All required fake assets are present or strategies referencing them are disabled.
- [ ] User list files resolve from data/lists.
- [ ] Upstream cache is not used as writable user storage.
- [ ] Empty user exclude/list/ipset files are accepted.
- [ ] No empty fake .bin files are generated.

## Strategies
- [x] All visible runnable strategies pass preflight.
- [x] Invalid strategies are clearly marked and not runnable.
- [x] Flowseal strategies are normalized.
- [x] StressOzz strategies are normalized or marked pending.
- [x] Builtin v3/v8 are fixed or hidden as invalid.

## Menu
- [x] Main menu is short and understandable.
- [x] Advanced actions are moved to submenus.
- [x] User-facing errors are readable Russian messages.
- [x] Tracebacks go to logs/reports, not normal UI.

## sing-box
- [ ] Start is blocked if no active node exists.
- [ ] Single imported node can be auto-selected if safe.
- [ ] Config generation is validated before launch.
- [ ] Stop/restart is idempotent for stale PID.

## Diagnostics
- [ ] Bug report masks secrets.
- [ ] Bug report includes runtime summary.
- [ ] Bug report includes missing assets.
- [ ] Bug report does not leak node UUIDs/passwords/subscription tokens.

## DedZapret / Windows runtime safety
- [ ] Нет использования `shell=True` в коде
- [ ] Нет прямого `ZipFile.extractall()` (используется safe_extract)
- [ ] Скачивания staged + verified
- [ ] User files не перезаписываются без backup
- [ ] Critical writes atomic (config/state/current/nodes)
- [ ] Перед destructive changes есть backup
- [ ] Admin-проверки есть для hosts/DNS/firewall/WinDivert
- [ ] hosts/DNS/firewall/system proxy имеют rollback
- [ ] Секреты маскируются в логах/diagnostics/bug reports
- [ ] winws2 остаётся целевым runtime (нет silent fallback на winws.exe)
- [ ] Действия логируются (audit log)
- [ ] Меню/функции не удалены, а помечены как Future/Planned, если не реализованы

## Workflow stages
- [ ] Stage 00 completed: `docs/ai/workflows/00_clean_rebuild_overview.md`
- [x] Stage 01 completed: `docs/ai/workflows/01_release_packaging_cleanup.md`
- [x] Stage 02 completed: `docs/ai/workflows/02_path_resolver_runtime_assets.md`
- [x] Stage 03 completed: `docs/ai/workflows/03_strategy_import_validation.md`
- [ ] Stage 04 completed: `docs/ai/workflows/04_menu_simplification.md`
- [ ] Stage 05 completed: `docs/ai/workflows/05_singbox_pipeline.md`
- [ ] Stage 06 completed: `docs/ai/workflows/06_diagnostics_bug_report.md`
- [ ] Stage 07 completed: `docs/ai/workflows/07_release_verification.md`

## QA gate / stage completion
- [ ] Targeted tests passed.
- [ ] Workflow-required tests passed.
- [ ] agent-verify passed.
- [ ] Full pytest passed, or remaining failures are documented as unrelated known failures/blockers.
- [ ] Failure table created for any failing tests.
- [ ] Masking/privacy/security tests pass if diagnostics or reports are touched.
- [ ] Release preflight passed if packaging/release is touched.
- [ ] Stage readiness is not marked YES while failures are untriaged.
- [ ] PROGRESS updated honestly.
- [ ] BLOCKERS updated if any failure remains.
- [ ] agent_worklog updated with exact verification results.

## Final
- [x] `docs/ai/PROGRESS.md` обновлён и содержит финальное резюме
- [ ] `docs/ai/BLOCKERS.md` не содержит критических нерешённых блокеров
- [ ] Верификация прошла:
  - [ ] `./scripts/agent-verify.ps1` (Windows) или
  - [x] `bash scripts/agent-verify.sh` (non-Windows)
- [ ] Все существующие тесты проходят