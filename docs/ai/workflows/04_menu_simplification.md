# Workflow 04 — Menu simplification

## Scope
Simplify the main menu to a short, product-like interface while preserving all existing functionality by relocating low-level engineering actions into submenus.

## Tasks

### 4.1 Define target main menu
Main menu must be short and understandable:

1. Старт / Стоп
2. Быстрый статус
3. Стратегии
4. Тест стратегий
5. Ноды / sing-box
6. DNS / hosts / системные настройки
7. Диагностика и ремонт
8. Логи и bug report
9. Обновления
10. Настройки

### 4.2 Status-first UI
Main screen must show:
- overall status;
- active strategy;
- runtime status;
- winws status;
- sing-box status;
- local proxy status;
- recent warnings;
- clear next actions.

### 4.3 Relocate low-level actions
Move engineering functions into submenus:
- Расширенное
- Диагностика
- Dev tools
- Advanced settings
- Maintenance

### 4.4 Preserve functions
- Do not remove existing functions.
- Relocate or mark Future/Planned.
- Preserve existing menu IDs so that menu_actions can still route to them.

### 4.5 User-facing errors
Replace raw Python tracebacks with clear Russian messages:
- "Ресурс не найден: ..."
- "Стратегия невалидна: ..."
- "Активный узел не выбран"
- "Сеть недоступна"
- "Требуются права администратора"
- etc.

Tracebacks go to logs and bug reports only.

## Acceptance criteria
- [ ] Main menu is short and understandable.
- [ ] Status summary is shown on main screen.
- [ ] Advanced actions are moved to submenus.
- [ ] No functions are deleted — only relocated or marked Future/Planned.
- [ ] User-facing errors are readable Russian messages.
- [ ] Tracebacks go to logs/reports, not normal UI.