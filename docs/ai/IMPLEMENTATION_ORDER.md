# Implementation Order

Этот документ описывает пошаговый порядок реализации DedZapret Manager в соответствии с PROGRAM_BLUEPRINT.md. Каждый этап завершает независимую часть и обеспечивает тесты.

---

## Stage 0: Документация и правила

**Цель:** Создать основу документации и правил перед началом разработки.

### Задачи:
- [x] Создать `PROGRAM_BLUEPRINT.md` (архитектурная карта продукта)
- [x] Обновить `MASTER_TASK.md` (fresh build vs migration)
- [ ] Создать `PRODUCT_OVERVIEW.md` (общее описание продукта для новых разработчиков)
- [ ] Создать `OPERATIONS_AND_QOL_SPEC.md` (спецификация операционных функций и удобства)
- [ ] Обновить `RUNTIME_SOURCE_POLICY.md` (роли upstream-источников)
- [ ] Обновить `DEDZAPRET_AGENT_RULES.md` (проектные правила безопасности)
- [ ] Создать `MODULE_CONTRACTS.md` (контракты между модулями)
- [ ] Создать `SECURITY_MODEL.md` (модель безопасности)
- [ ] Создать `STRATEGY_MODEL.md` (структура стратегий)

### Выход:
- Полная документационная база
- Четкие правила для агентов
- Архитектурные договоренности

---

## Stage 1: Characterization tests

**Цель:** Создать тесты для существующего поведения перед рефакторингом. Это защитит от регрессий.

### Задачи:
- [ ] Тесты для `config/state/current` моделей
- [ ] Тесты для `paths.py` (portable layout)
- [ ] Тесты для strategy loader (чтение YAML/JSON)
- [ ] Тесты для Flowseal импорта (парсинг .bat файлов)
- [ ] Тесты для StressOzz импорта (нормализация стратегий)
- [ ] Тесты для сборки команды winws2 (snapshot testing)
- [ ] Тесты для диагностики/отчёта
- [ ] Тесты для hosts/DNS dry-run (безопасные проверки)
- [ ] Тесты для sing-box конфигурации

### Техника:
- Использовать `pytest` с фикстурами
- Mock внешних зависимостей (winws2.exe, WinDivert)
- Snapshot testing для стратегий
- Characterization testing (поведение ≠ имплементация)

### Выход:
- Набор тестов, покрывающий текущее поведение
- Основа для безопасного рефакторинга

---

## Stage 2: Path/config/state foundation

**Цель:** Создать единый portable layout и модели конфигурации/состояния.

### Задачи:
- [ ] `paths.py` - portable paths (DedZapretData, config, state, runtime)
- [ ] `config.py` - модель конфигурации (yaml validation, schema)
- [ ] `state.py` - модель состояния (runtime state, profiles, strategies)
- [ ] `current_state.py` - текущее активное состояние (PID, active strategy, proxy)
- [ ] `atomic_write.py` - атомарные записи для критичных файлов
- [ ] `backup.py` - система backup/rollback для конфигурации
- [ ] `security.py` - проверки безопасности (admin rights, path validation)

### Требования:
- Все пути portable (без hardcoded C:\Users)
- Atomic writes для config/state/current.json
- Backup перед любыми изменениями конфигурации
- Валидация при загрузке/сохранении

### Выход:
- Надежная основа для всей системы
- Защита от потери данных

---

## Stage 3: winws2 runtime layer

**Цель:** Реализовать управление winws2 runtime с предпроверкой и безопасным запуском.

### Задачи:
- [ ] `detector.py` - поиск winws2.exe в разных locations
- [ ] `command_model.py` - модель аргументов winws2
- [ ] `asset_resolver.py` - resolution fake/list/hostlist файлов
- [ ] `preflight.py` - полная проверка перед запуском
- [ ] `process.py` - безопасный запуск/остановка процессов
- [ ] `health.py` - мониторинг работоспособности runtime
- [ ] `repair.py` - восстановление недостающих assets

### Требования:
- Без shell=True (только list argv)
- Admin preflight checks
- Atomic process management
- Audit logging всех действий
- Health monitoring в реальном времени

### Выход:
- Полноценный runtime manager с защитой

---

## Stage 4: Strategy registry

**Цель:** Реализовать единый registry стратегий с классификацией и валидацией.

### Задачи:
- [ ] `model.py` - модель стратегии (JSON schema)
- [ ] `registry.py` - центральный registry всех стратегий
- [ ] `loader.py` - загрузка из разных источников
- [ ] `validator.py` - проверка стратегий (placeholders, конфликты)
- [ ] `composer.py` - сборка стратегии из слоев (base + Yv + Dv + Gv)
- [ ] `classifier.py` - классификация по статусам
- [ ] `import_flowseal.py` - импорт и нормализация Flowseal
- [ ] `import_stressozz.py` - импорт и нормализация StressOzz
- [ ] `ranking.py` - ранжирование стратегий по тестам

### Требования:
- Все стратегии - объекты, а не файлы
- Классификация по матрице совместимости
- Валидация перед использованием
- Сохранение кастомных стратегий

### Выход:
- Система стратегий с полным контролем

---

## Stage 5: Test engine

**Цель:** Реализовать тестовый движок для подбора оптимальных стратегий.

### Задачи:
- [ ] `domain_sets.py` - наборы доменов для тестов
- [ ] `probes.py` - сетевые пробы (DNS, TCP, UDP, HTTP)
- [ ] `baseline.py` - baseline измерения без zapret
- [ ] `runner.py` - execution engine для тестов
- [ ] `strategy_sweep.py` - тест всех стратегий
- [ ] `proof_of_effect.py` - доказательство эффекта zapret
- [ ] `problem_domains.py` - отслеживание проблемных доменов
- [ ] `result_store.py` - хранение результатов тестов

### Требования:
- Неблокирующие тесты с прогрессом
- Масштабируемость (100+ стратегий)
- Crash detection
- Problem domains tracking
- Secret masking в логах тестов

### Выход:
- Мощный test engine для автоподбора стратегий

---

## Stage 6: Connectivity layer

**Цель:** Реализовать поддержку sing-box proxy/VPN nodes.

### Задачи:
- [ ] `binary.py` - detection и version sing-box
- [ ] `nodes.py` - модель узлов и управление
- [ ] `subscriptions.py` - импорт/обновление подписок
- [ ] `config_builder.py` - генерация конфигурации sing-box
- [ ] `process.py` - запуск/остановка proxy
- [ ] `health.py` - мониторинг proxy health
- [ ] `system_proxy.py` - управление system proxy

### Требования:
- Поддержка multiple formats (vless, vmess, trojan, ss, clash)
- Preview без активации
- Safe subscription updates
- System proxy integration

### Выход:
- Полноценный proxy/VPN管理层

---

## Stage 7: Windows operations

**Цель:** Реализовать безопасные Windows операции с rollback.

### Задачи:
- [ ] `admin.py` - проверка прав администратора
- [ ] `autostart.py` - управление автозапуском через Task Scheduler
- [ ] `task_scheduler.py` - управление задачами планировщика
- [ ] `hosts.py` - безопасное управление hosts с backup
- [ ] `dns.py` - управление DNS/DoH с rollback
- [ ] `firewall.py` - правила firewall для proxy
- [ ] `tcp_timestamps.py` - управление TCP timestamps
- [ ] `registry_proxy.py` - registry proxy settings

### Требования:
- Admin preflight для всех операций
- Backup перед любыми изменениями
- Rollback capability
- Audit logging
- User-friendly сообщения об ошибках

### Выход:
- Безопасный слой Windows операций

---

## Stage 8: Profiles

**Цель:** Реализовать систему профилей как сценариев пользователя.

### Задачи:
- [ ] `model.py` - модель профиля (сложная структура)
- [ ] `store.py` - хранение и загрузка профилей
- [ ] `resolver.py` - resolution профиля в активные настройки
- [ ] `watcher.py` - process watcher для автозапуска/остановки

### Требования:
- Профили включают winws2 + proxy + network + autostart
- Last working profile recovery
- Process watcher для автоматического старта
- Validation профилей

### Выход:
- Система профилей для разных сценариев использования

---

## Stage 9: Console UI rebuild

**Цель:** Реализовать дружелюбный console интерфейс.

### Задачи:
- [ ] `dashboard.py` - главная панель статуса
- [ ] `main_menu.py` - основной menu framework
- [ ] `strategies_menu.py` - меню стратегий с карточками
- [ ] `tests_menu.py` - меню тестов с прогрессом
- [ ] `connectivity_menu.py` - меню proxy/VPN
- [ ] `diagnostics_menu.py` - меню диагностики
- [ ] `settings_menu.py` - меню настроек

### Требования:
- User-friendly сообщения вместо ошибок
- Progress indicators для долгих операций
- Novice/Advanced режимы
- Integration с core.commands

### Выход:
- Полноценный console UI

---

## Stage 10: Tray

**Цель:** Реализовать системный трей для быстрого доступа.

### Задачи:
- [ ] `tray_app.py` - основное tray приложение
- [ ] `tray_status.py` - status icons и colors
- [ ] `tray_menu.py` - context menu с действиями
- [ ] `tray_worker.py` - background worker для операций
- [ ] `tray_icons.py` - иконки для разных состояний

### Требования:
- Status visualization (colors, tooltips)
- Quick actions (Start/Stop/Restart/Test)
- Safe exit с cleanup
- Integration с core.commands

### Выход:
- Полноценный tray интерфейс

---

## Stage 11: Cleanup and finalization

**Цель:** Очистка кода и подготовка к релизу.

### Задачи:
- [ ] Удаление дубликатов модулей
- [ ] Объединение старых модулей
- [ ] Удаление мертвого кода
- [ ] PyInstaller packaging
- [ ] Release checks
- [ ] Документация обновлена
- [ ] Финальные тесты

### Требования:
- Code review для качества
- Performance testing
- Memory leak checking
- Release notes generation

### Выход:
- Готовый к релизу продукт

---

## Критические точки

### Риски:
1. **Windows-specific operations** - нужны тесты на реальной Windows машине
2. **winws2.exe dependency** - mock для development, real integration для testing
3. **Large test suite** - incremental testing, avoid test explosion
4. **UI complexity** - iterative development, start with basic console UI

### Защита:
- History audit из `development_history_merged.md`
- Regression prevention checklist перед каждым релизом
- Secret masking во всех отчетах
- Backup/rollback для всех опасных операций

---

## Success Metrics

Каждый этап считается завершенным когда:
- Все задачи выполнены
- Тесты проходят (100%成功率)
- Нет новых блокеров в BLOCKERS.md
- Документация обновлена
- Verification скрипты проходят

Это обеспечивает пошаговое построение качественного продукта с минимальными рисками.