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

## Workflow stages

- [x] Stage 1 completed: `docs/ai/workflows/01_stabilization_fixes_test10.md`
- [x] Stage 2 completed: `docs/ai/workflows/02_test_engine_performance.md`
- [x] Stage 3 completed: `docs/ai/workflows/03_tray_and_menu_ux.md`

## Final
- [x] `docs/ai/PROGRESS.md` обновлён и содержит финальное резюме
- [x] `docs/ai/BLOCKERS.md` не содержит критических нерешённых блокеров
- [x] Верификация прошла:
  - [ ] `./scripts/agent-verify.ps1` (Windows) или
  - [x] `bash scripts/agent-verify.sh` (non-Windows)
- [x] Все существующие тесты проходят
