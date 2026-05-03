# ACCEPTANCE_CHECKLIST

Отмечай чекбоксы по мере выполнения.

## Global
- [ ] Прочитан `AGENTS.md`
- [ ] Прочитан `LOCAL_AGENT_START_HERE.md`
- [ ] Прочитан `docs/ai/MASTER_TASK.md`
- [ ] `docs/ai/CONTEXT_MAP.md` был прочитан перед широким исследованием репозитория
- [ ] `docs/ai/CONTEXT_MAP.md` был обновлён, если структура проекта изменилась
- [ ] Прочитаны workflow-стадии `docs/ai/workflows/*` (для понимания общего плана)
- [ ] Нет выдуманных фич/поведения вне требований (либо помечено как **Future / Planned**)
- [ ] Нет нерелевантных рефакторингов/массового форматирования
- [ ] Нет утечек секретов (токены/пароли/ключи/URL с кредами/персональные данные)
- [ ] Активная workflow-стадия выполнялась по порядку (без пропуска стадий) либо было явное разрешение человека

## Workflow stages

- [ ] Stage 1 completed: `docs/ai/workflows/01_stabilization_fixes_test10.md`
- [ ] Stage 2 completed: `docs/ai/workflows/02_test_engine_performance.md`
- [ ] Stage 3 completed: `docs/ai/workflows/03_tray_and_menu_ux.md`

## Final
- [ ] `docs/ai/PROGRESS.md` обновлён и содержит финальное резюме
- [ ] `docs/ai/BLOCKERS.md` не содержит критических нерешённых блокеров
- [ ] Верификация прошла:
  - [ ] `./scripts/agent-verify.ps1` (Windows) или
  - [ ] `bash scripts/agent-verify.sh` (non-Windows)
- [ ] Все существующие тесты проходят
