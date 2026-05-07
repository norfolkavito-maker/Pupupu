# ACCEPTANCE_CHECKLIST

Отмечай чекбоксы по мере выполнения.

## Global
- [x] Прочитан `AGENTS.md`
- [x] Прочитан `LOCAL_AGENT_START_HERE.md`
- [x] Прочитан `docs/ai/MASTER_TASK.md`
- [x] `docs/ai/CONTEXT_MAP.md` был прочитан перед широким исследованием репозитория
- [x] `docs/ai/CONTEXT_MAP.md` был обновлён, если структура проекта изменилась
- [x] Прочитаны workflow-стадии `docs/ai/workflows/*` (для понимания общего плана)
- [x] Нет выдуманных фич/поведения вне требований (либо помечено как **Future / Planned**)
- [x] Нет нерелевантных рефакторингов/массового форматирования
- [x] Нет утечек секретов (токены/пароли/ключи/URL с кредами/персональные данные)
- [x] Активная workflow-стадия выполнялась по порядку (без пропуска стадий) либо было явное разрешение человека

## Agent rules & safety docs
- [x] `docs/ai/DEDZAPRET_AGENT_RULES.md` добавлен и содержит правила безопасности
- [x] `docs/ai/RUNTIME_SOURCE_POLICY.md` добавлен и описывает upstream-роли
- [x] `docs/ai/development_history_merged.md` добавлен с историей ошибок
- [x] `docs/ai/REGRESSION_PREVENTION_CHECKLIST.md` добавлен
- [x] `docs/ai/PRODUCT_OVERVIEW.md` добавлен с описанием продукта
- [x] `docs/ai/OPERATIONS_AND_QOL_SPEC.md` добавлен с QoL-спецификацией
- [x] `docs/ai/STRATEGY_COMPATIBILITY_WORKFLOW.md` добавлен
- [x] `docs/ai/STRATEGY_COMPATIBILITY_MATRIX.md` добавлен
- [x] `docs/ai/HISTORY_AUDIT_WORKFLOW.md` добавлен
- [x] `docs/ai/HISTORY_AUDIT.md` добавлен (шаблон)
- [x] `AGENTS.md` обновлён с DedZapret-specific safety, upstream source roles, audit logging
- [x] `.github/copilot-instructions.md` обновлён с новыми ссылками
- [x] `.windsurf/rules/agent-general.md` обновлён с новыми ссылками
- [x] `.windsurf/rules/project-local-workflow.md` обновлён с новыми ссылками

## Workflow stages
- [x] Stage 1 completed: `docs/ai/workflows/01_stabilization_fixes_test10.md`
- [x] Stage 2 completed: `docs/ai/workflows/02_test_engine_performance.md`
- [x] Stage 3 completed: `docs/ai/workflows/03_tray_and_menu_ux.md`

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

## Final
- [x] `docs/ai/PROGRESS.md` обновлён и содержит финальное резюме
- [x] `docs/ai/BLOCKERS.md` не содержит критических нерешённых блокеров
- [ ] Верификация прошла:
  - [ ] `./scripts/agent-verify.ps1` (Windows) или
  - [x] `bash scripts/agent-verify.sh` (non-Windows)
- [x] Все существующие тесты проходят