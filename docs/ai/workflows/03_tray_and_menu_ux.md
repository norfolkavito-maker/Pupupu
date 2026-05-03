# Agent Workflow: 03 — Tray and menu UX

# PROMPT 03 — Трей + причёсывание меню стратегий/тестов для людей

## Комментарий для пользователя

Давать после стабилизации и ускорения тестов. Это уже UX-слой: иконка в трее, быстрые действия, статусы, аккуратное группирование стратегий/тестов/диагностики внутри текущего вида. Полный GUI пока не делать.

## Правила для агента

- Tray должен вызывать `core/commands.py`.
- Tray не должен дублировать бизнес-логику.
- Tray должен быть optional.
- `pystray/Pillow` — только lazy imports.
- App должен запускаться без tray-зависимостей.
- Долгие действия из tray не должны фризить UI.
- User-facing text — на русском.
- Не логировать секреты.
- Не делать `winws2` дефолтом.
- Не менять оригинальные strategy-файлы.
- Не придумывать новые оригинальные стратегии.
- Не удалять advanced functionality.

---

<role>
You are a senior Windows desktop UX engineer, Python application engineer, and product designer.
The app is DedZapret / “ЗапретМенеджер на винду”.
Your task is to implement a proper system tray control layer and clean up strategy/test menus for humans.
</role>

<context>
The project already has:
- P0/P1 stabilization
- `commands.py` unified command layer
- strategy diagnostics
- sing-box health
- test all strategies
- problem domains
- diagnostics artifacts
- winws2 compatibility

The user now wants:
1) tray icon with important actions;
2) clearer strategy/test menus;
3) human-friendly UX without global GUI yet.
</context>

<main_goal>
Implement a proper tray icon and polish strategy/test menus while preserving the current console app and advanced functionality.

Do NOT build full GUI.
Do NOT remove advanced menus.
Do NOT make tray mandatory.
Do NOT redesign the entire app navigation from scratch.
Do make the current strategy/test sections understandable and pleasant for humans.
</main_goal>

<critical_rules>
- Tray must call `core/commands.py`.
- Tray must not duplicate business logic.
- Tray must be optional.
- `pystray/Pillow` must be lazy imports.
- App must run without tray dependencies.
- Long actions from tray must not freeze tray UI.
- User-facing text must be Russian.
- Do not log secrets.
- Do not make winws2 default.
- Do not modify original strategy files.
- Do not invent new original strategies.
- Keep current console app working.
</critical_rules>

<task_1 title="Audit existing tray files">
There is already:
- `app/zapret_manager/ui/tray.py`

Audit it first.

Decide:
1. move real tray implementation into `app/zapret_manager/tray/`;
2. keep `ui/tray.py` as compatibility wrapper if needed;
3. avoid duplicate independent tray implementations.

Also check:
- no mandatory `pystray/Pillow` import at app startup;
- no tray auto-start unless enabled;
- no broken imports on non-Windows/headless environment.
</task_1>

<task_2 title="Tray module structure">
Create or normalize:

app/zapret_manager/tray/
  __init__.py
  tray_app.py
  tray_menu.py
  tray_icons.py
  tray_status.py
  tray_worker.py

Responsibilities:
- `tray_app.py`: lifecycle/start/stop
- `tray_menu.py`: build context menu
- `tray_icons.py`: generate/load status icons
- `tray_status.py`: read status via `commands.get_status_summary()`
- `tray_worker.py`: run long commands without freezing UI
</task_2>

<task_3 title="Tray statuses and icons">
Implement tray statuses:

gray:
- everything disabled

green:
- zapret/winws active

blue:
- VPN/sing-box active

purple:
- test/sync/diagnostics running

yellow:
- warning:
  - missing assets
  - no active node
  - stale pid
  - problem domains exist

red:
- error:
  - start failed
  - invalid strategy
  - VPN failed
  - missing winws/winws2

Tooltip example:

DedZapret: ACTIVE
Стратегия: v7
VPN: OFF
Профиль: Default
Проблемные домены: 8
Последний тест: v7, 28/46
Ошибки: нет

For error:

DedZapret: ERROR
Причина: missing winws2.exe
Рекомендация: Runtime → Repair assets
</task_3>

<task_4 title="Tray menu">
Implement tray menu:

DedZapret
Статус: ACTIVE / OFF / ERROR

Основное
- Включить Recommended
- Отключить всё
- Перезапустить текущий режим

VPN
- Активировать VPN
- Отключить VPN
- Выбрать локацию
- Обновить подписку

Стратегии
- Recommended: v7
- Текущая: v7
- Выбрать стратегию...
- Тест всех стратегий...
- Остановить тест

Диагностика
- Проверка интернета
- Диагностика sing-box
- Починить runtime assets
- Создать отчёт об ошибке
- Открыть логи

Настройки
- Автозапуск: ON/OFF
- Запускать в трей: ON/OFF
- Runtime engine: Auto/winws/winws2
- Открыть полное меню
- Выход

Menu must use `commands.py`.

If some command is not implemented yet:
- show disabled menu item or friendly message:
  `Функция ещё не реализована`
</task_4>

<task_5 title="Tray background jobs">
Long actions must not block tray UI:
- Test all strategies
- Update subscriptions
- Repair runtime assets
- Bug report
- Diagnostics artifacts

Implement a simple job state:
- idle
- running
- cancel_requested
- done
- error

Tray status should show:
- `Идёт тест...`
- `Идёт обновление подписки...`
- `Создаётся отчёт...`

Add `Остановить тест` if test job is running.

Use safe threading/worker.
Do not start multiple long jobs at once.
If user starts another job:
`Уже выполняется задача: ...`
</task_5>

<task_6 title="Tray config">
Add/extend config with backward compatibility:

tray:
  enabled: false
  start_minimized: false
  close_to_tray: false
  show_notifications: true
  refresh_interval_ms: 1500

Behavior:
- `enabled=false`: no tray.
- `start_minimized=true`: start tray without opening full console if supported.
- `close_to_tray=true`: closing app minimizes to tray where possible.
- app must still work without tray.
</task_6>

<task_7 title="Clean strategy menu">
Polish the existing strategy menu without global redesign.

Add top description:

`Стратегия — это технический набор параметров winws. Профиль — это пользовательский сценарий, например Discord или Games.`

Show status block:
- active strategy
- recommended strategy
- runtime engine
- invalid strategy count

Group actions:

Основное:
1) Выбрать Recommended
2) Выбрать стратегию вручную
3) Показать оригинальные стратегии
4) Показать Flowseal стратегии
5) Показать custom/generated

Проверка:
6) Проверить выбранную стратегию
7) Тест всех стратегий
8) Последний рейтинг

Конфликты:
9) Проверить конфликты выбранных стратегий

Runtime:
10) Engine mode: Auto / winws / winws2

Do not delete old actions. Move advanced/raw actions under existing advanced section if possible.
</task_7>

<task_8 title="Clean test menu">
Polish existing test menu.

Add top description:

`Здесь проверяется, какие стратегии реально работают в вашей сети. Для первого подбора используйте “Тест всех стратегий”. Для проверки без обхода используйте “Контрольный тест”.`

Group actions:

Основное:
1) Тест всех стратегий
2) Тест текущей стратегии
3) Контрольный тест без обхода
4) Тест проблемных доменов

Результаты:
5) Последний рейтинг стратегий
6) Recommended strategy
7) Сохранить TOP-5

Настройки теста:
8) Настройки скорости теста
9) Выбор набора доменов
10) Подробный / компактный вывод

Расширенное:
11) Blockcheck
12) Flowseal tests
13) Raw diagnostics

Do not remove existing test capabilities.
</task_8>

<task_9 title="Strategy conflict validator UX">
Add first conflict validator UI.

When conflict detected:

Конфликт настроек
-----------------
Вы выбрали Gaming Gv1 и ALT9.

Обе стратегии меняют:
- UDP/443
- fake QUIC

Обычно рекомендуется выбрать только одну.

Что сделать?
1) Оставить Gv1
2) Оставить ALT9
3) Попробовать безопасно объединить
4) Продолжить всё равно
5) Отмена

Rules:
- combining allowed only if strategies affect different protocols/ports/lists;
- original strategy files must not be modified;
- if unsafe, show warning and require confirmation.
</task_9>

<task_10 title="Human-readable labels and hints">
Add short hints for strategy/test menu items.

Examples:
- Тест всех стратегий:
  `Проверяет все доступные стратегии и строит рейтинг.`
- Контрольный тест:
  `Проверяет домены без обхода, чтобы понять базовую доступность.`
- Problem Domains:
  `Домены, которые ранее не прошли проверку.`
- Blockcheck:
  `Расширенный подбор параметров. Может идти долго.`
- Runtime engine:
  `Auto — использовать engine из стратегии. winws2 не включается по умолчанию.`

Keep hints concise.
</task_10>

<tests>
Add/update tests:

Tray:
- app imports without `pystray/Pillow` installed;
- tray status mapping works;
- tray menu can be built from fake `CommandResult/status`;
- long job lock prevents two jobs at once;
- tray disabled by config does not start.

Commands integration:
- tray actions call `commands.py`, not feature internals.

Menus:
- strategy menu renders grouped sections;
- test menu renders grouped sections;
- hints are present;
- advanced actions still reachable.

Conflict validator:
- detects UDP443/fake QUIC conflict;
- safe combine allowed only for non-overlapping capabilities;
- original strategy file is not modified.

No real network.
No real tray UI in unit tests; mock `pystray/Pillow`.
</tests>

<commit_plan>
Use small commits:
1. `feat(tray): add optional tray app and status menu`
2. `feat(tray): add background job handling and notifications`
3. `ux(menu): polish strategy and test menus`
4. `feat(strategies): add conflict validator UX`
5. `test(tray): cover optional tray and menu rendering`
</commit_plan>

<expected_final_response>
Report in Russian:
1. Commits created.
2. Files changed.
3. Tray behavior.
4. Tray menu structure.
5. Config keys added.
6. Strategy/test menu changes.
7. Conflict validator behavior.
8. Tests added and exact commands/results.
9. Windows manual checklist.
10. Known limitations.
</expected_final_response>
