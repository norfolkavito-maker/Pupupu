# PROGRAM BLUEPRINT

## Полная карта продукта, функций, слоёв, UX и целевой архитектуры DedZapret Manager

Этот документ описывает проект **DedZapret Manager** — портативную Windows‑утилиту для управления DPI‑desync программой `zapret/winws2`, стратегиями обхода, тестированием, proxy/VPN‑подключениями, автоматическим запуском, системным треем, профилями сценариев и диагностикой.  Важно понимать, что DedZapret Manager не является простым запускателем `.bat`‑файлов.  Это полноценный операционный менеджер для Flowseal winws2, который объединяет знания upstream‑проектов bol‑van/zapret и StressOzz/Zapret‑Manager и строит на их основе безопасный Windows‑продукт.

Документ структурирован в десять разделов.  Каждый раздел посвящён определённому слою приложения: от концептуальной модели до конкретных функций и требований к пользовательскому интерфейсу.  В конце приведён план реализации по этапам и общая формула, объединяющая все слои.

---

## 1. Продуктовая модель

### 1.1 Что это за программа

**DedZapret Manager** — портативная Windows 10/11 x64 утилита для управления DPI‑desync runtime (`zapret/winws2`), наборами обходных стратегий, тестами производительности, proxy/VPN‑подключениями, автозапуском, системным треем, профилями сценариев и диагностикой.  Приложение должно отвечать на вопросы пользователя:

* Что сейчас включено?
* Какая стратегия активна?
* Какой процесс запущен?
* Какие файлы runtime используются?
* Какая стратегия лучше работает на моей сети?
* Почему стратегия не стартует?
* Чего не хватает для запуска?
* Что сломалось после обновления?
* Как собрать отчёт без утечки секретов?
* Как вернуть рабочее состояние?

Пользователь не должен редактировать `.bat`‑файлы, искать отсутствующие fake‑файлы, угадывать `--hostlist`, завершать процессы через Диспетчер задач или вручную собирать логи.  Все эти операции должны быть встроены в DedZapret Manager.

### 1.2 Что это НЕ

DedZapret Manager не должен быть:

* простой запускалкой `.bat`;
* копией Flowseal;
* копией StressOzz;
* VPN‑клиентом;
* графической оболочкой sing‑box;
* архивом стратегий;
* хаотичной смесью чужих скриптов;
* программой, где стратегия применяется без проверки.

Правильная роль проекта:

> **DedZapret = нормализатор + менеджер + диагностический слой + безопасный Windows‑жизненный цикл.**

---

## 2. Upstream‑модель

DedZapret Manager опирается на три upstream‑проекта, каждый из которых имеет свою роль.

### 2.1 bol‑van/zapret — техническая конституция

Используется для:

* семантики desync‑параметров;
* модели hostlist/ipset/autohostlist;
* философии тестирования `blockcheck`;
* понимания fake‑пакетов;
* описания поведения `nfqws`, `tpws` и `winws`;
* валидации, что стратегия вообще имеет смысл.

Не используется как прямой Windows‑UI/runtime.  Линуксовые `init.d`, `iptables`, `nftables`, `/opt/zapret` не переносятся напрямую.

### 2.2 Flowseal/zapret‑discord‑youtube — Windows runtime base

Используется для:

* `winws2` в качестве основного runtime;
* layout WinDivert;
* структуру каталогов `bin/lists/utils/fake`;
* файлы `general*.bat` как примеры Windows‑стратегий;
* `service.bat` как справочник по жизненному циклу службы;
* поведение status/diagnostics/update;
* проверки Windows‑зависимостей: x64, права администратора, PowerShell, WinDivert.

Flowseal и DeepWiki описывают архитектуру с разделением UI‑слоя, service management, packet filtering и конфигурации данных.  DedZapret Manager должен сделать эту модель более структурированной и тестируемой.  Проверки x64, admin, PowerShell, WinDivert становятся частью модуля preflight.

### 2.3 StressOzz/Zapret‑Manager — manager/workflow reference

Используется для:

* структуры меню стратегий;
* логики Discord/YouTube/Games (`Dv`, `Yv`, `Gv`);
* Flowseal‑меню стратегий;
* обновления стратегий;
* тестирования v/Flowseal;
* поведения RKN/exclude/wssize;
* идей «под ключ» сценариев;
* UX: показать текущую стратегию, статус, доступные действия.

Linux‑команды не переносятся напрямую: в Windows все выполняется через собственные модули и адаптеры.

---

## 3. Целевая архитектура

Структура исходников должна быть разделена на слои.  Ниже приведена схема каталогов.  Каждый модуль должен отвечать за свою часть и не содержать бизнес‑логики другого слоя.

```
app/zapret_manager/
  core/
    paths.py
    config.py
    state.py
    current_state.py
    logging.py
    audit.py
    diagnostics.py
    report.py
    commands.py
    errors.py
    security.py
  upstreams/
    bolvan_reference.py
    flowseal_sync.py
    stressozz_sync.py
    provenance.py
    source_policy.py
  runtime/
    winws2/
      detector.py
      command_model.py
      asset_resolver.py
      preflight.py
      process.py
      health.py
      repair.py
    windivert/
      detector.py
      health.py
  strategies/
    registry.py
    model.py
    loader.py
    validator.py
    composer.py
    classifier.py
    import_flowseal.py
    import_stressozz.py
    generated.py
    custom.py
    ranking.py
  tests_engine/
    domain_sets.py
    probes.py
    runner.py
    baseline.py
    strategy_sweep.py
    proof_of_effect.py
    problem_domains.py
    result_store.py
  connectivity/
    singbox/
      binary.py
      nodes.py
      subscriptions.py
      config_builder.py
      process.py
      health.py
      system_proxy.py
  windows_ops/
    admin.py
    autostart.py
    task_scheduler.py
    hosts.py
    dns.py
    doh.py
    firewall.py
    tcp_timestamps.py
    registry_proxy.py
  profiles/
    model.py
    store.py
    resolver.py
    watcher.py
  ui/
    console/
      dashboard.py
      main_menu.py
      strategies_menu.py
      tests_menu.py
      connectivity_menu.py
      diagnostics_menu.py
      settings_menu.py
    tray/
      tray_app.py
      tray_status.py
      tray_menu.py
      tray_worker.py
      tray_icons.py
  packaging/
    pyinstaller.py
    release_checks.py
```

Главный принцип: **слой UI (console/tray/GUI) не содержит бизнес‑логики**.  Все действия выполняются через функции `core.commands`, что облегчает написание тестов и замену интерфейсов.

---

## 4. Главный пользовательский flow

### 4.1 Первый запуск

При первом запуске (через `run.bat` или собранный исполимый файл) программа выполняет preflight‑проверку:

* Windows 10/11 x64?
* Есть ли права администратора?
* Доступен ли PowerShell?
* Путь установки не содержит кириллицы/спецсимволов?
* Создан ли каталог `DedZapretData`?
* Валиден ли `config.yaml`?
* Валидны ли `state.json` и `current.json`?
* Найден ли `winws2.exe`?
* Найден ли WinDivert?
* Найдены ли `fake/list` файлы?
* Есть ли хотя бы одна рабочая стратегия?

Пользователю показывается дружелюбная карточка состояния, например:

```
[OK] Windows x64
[OK] Admin rights
[WARNING] winws2.exe not found
[FIX] Download/update Flowseal runtime
```

Действия, предлагаемые в первом запуске:

1. Автонастройка;
2. Обновить runtime Flowseal;
3. Импортировать стратегии StressOzz;
4. Запустить диагностику;
5. Открыть настройки.

### 4.2 Обычный запуск

Главная панель показывает статус системы и основные параметры, например:

```
DedZapret Manager
Status: Active / Disabled / Error
Runtime: winws2 OK / Missing / Running PID 1234
Active profile: YouTube + Discord
Active strategy: general ALT5 + Yv3 + Dv12 + Gv2
Proxy/VPN: sing-box OFF / ON node_name
DNS: System / DoH ON
Hosts: clean / modified by manager
Autostart: ON / OFF
Tray: ON / OFF
Last test: 8/10 OK
Warnings: 2
```

Кнопки быстрых действий: Start, Stop, Restart, Test current, Auto-pick best, Create bug report, Open logs.

---

## 5. Функциональная карта по разделам

Ниже перечислены основные разделы системы с описанием назначения, местонахождения кода, функций и требований к UX.

### 5.1 Dashboard / Главная

**Назначение:** предоставить одно место, где видно состояние программы.

**Где:** `ui/console/dashboard.py`, `core.commands.get_status_summary()`, `runtime/winws2/health.py`, `connectivity/singbox/health.py`, `windows_ops/{autostart,hosts,dns}.py`.

**Отображает:** общий статус; состояние runtime winws2; активный PID; активную стратегию; активный профиль; состояние proxy/VPN; DNS/hosts; результат последнего теста; предупреждения; версию программы и runtime; кнопки быстрых действий.

**UX:** вместо технических исключений пользователю предлагаются понятные сообщения и решения.  Например, если отсутствует fake‑файл: «Не хватает fake‑файла для QUIC: DedZapretData/runtime/zapret/files/fake/quic_initial_www_google_com.bin.  Что можно сделать: (1) Repair runtime assets, (2) Update Flowseal runtime, (3) Выбрать другую стратегию».  Ошибки отображаются в отдельном блоке с инструкциями.

### 5.2 Runtime Manager: Flowseal winws2

**Назначение:** управлять `winws2` как основным runtime.

**Где:** `runtime/winws2/{detector,command_model,asset_resolver,preflight,process,health,repair}.py`.

**Основные функции:**

* **`detect_winws2()`** ищет исполнимый файл `winws2.exe` в `DedZapretData/runtime/zapret/bin/`, `DedZapretData/data/upstreams/flowseal/bin/`, bundled runtime или пользовательском пути.  Возвращает структуру с флагом найден/не найден, путём, версией и предупреждениями.
* **`build_winws2_command(strategy, profile)`** формирует список аргументов для запуска `winws2.exe`, исходя из базовой стратегии, YouTube/Discord/Games/RKN/wssize слоёв, путей и выбранных fake/list assets.  Команда возвращается как list, а не строка.
* **`preflight_winws2_command()`** проверяет, что exe существует; WinDivert найден; все файлы `--hostlist`/`--ipset`/fake присутствуют; нет Linux‑путей; нет неизвестных placeholders; нет Unsupported engine; стратегия не пустая.
* **`start_runtime()`** корректно останавливает старый процесс, если нужно, запускает `winws2.exe` в детач режиме, записывает PID в `current.json`, пишет событие в аудит, проверяет, что процесс запущен, и возвращает user‑friendly результат.
* **`stop_runtime()`** останавливает PID, указанный в `current.json`, очищает `stale state`, не убивает чужие процессы, фиксирует событие в аудит.

**UX:** после успешного старта отображается PID, стратегия, режим и отсутствие предупреждений.  При ошибке пользователю показывается причина и доступные решения (repair/update/change strategy).

### 5.3 Strategy Registry

**Назначение:** все стратегии должны быть объектами в registry, а не простыми файлами.  Это позволяет валидировать, классифицировать, комбинировать и тестировать их.

**Где:** `strategies/{model,registry,loader,validator,composer,classifier,import_flowseal,import_stressozz,generated,custom,ranking}.py`.

**Модель стратегии:**

```json
{
  "id": "flowseal.general.alt5",
  "name": "general ALT5",
  "source": "flowseal",
  "source_ref": "commit/tag/date",
  "kind": "base",
  "runtime_target": "winws2",
  "original_engine": "bat/winws/winws2/unknown",
  "normalized_engine": "winws2",
  "args": [],
  "required_files": [],
  "tags": ["discord", "youtube", "recommended"],
  "status": "FLOWSEAL_WINWS2_READY",
  "warnings": [],
  "description_ru": "..."
}
```

**Классификации:**

```
FLOWSEAL_WINWS2_READY
STRESSOZZ_IMPORTED_NEEDS_NORMALIZATION
CUSTOM_NEEDS_VALIDATION
GENERATED_WINWS2_READY
LEGACY_WINWS_NEEDS_CONVERSION
INVALID_MISSING_ASSETS
INVALID_UNSUPPORTED_ENGINE
UNKNOWN_NEEDS_VERIFICATION
```

**Функции:**

* **`load_all_strategies()`** загружает все типы стратегий: встроенные, сгенерированные, кастомные, импортированные из Flowseal и StressOzz.  Некорректные файлы помечаются `BROKEN`, но не прерывают загрузку.
* **`validate_strategy()`** проверяет runtime target, необходимые файлы, placeholders, отсутствие Linux‑путей, конфликтующие фильтры, duplicate `--new`, отсутствие filter перед desync, опасные/неизвестные параметры.
* **`compose_profile_strategy()`** принимает базовую стратегию и слои (YouTube, Discord, Games, RKN, wssize), собирает один итоговый объект команды.

**UX:** в меню стратегий отображаются карточки с источником, статусом, тегами, результатами тестов и предупреждениями.  Пользователь видит, какие стратегии готовы, какие требуют нормализации, какие помечены как BROKEN.

### 5.4 Upstream Sync

**Назначение:** безопасно синхронизировать upstream‑источники: обновлять Flowseal runtime и импортировать логику из StressOzz.

**Где:** `upstreams/{flowseal_sync,stressozz_sync,bolvan_reference,provenance,source_policy}.py`.

**Flowseal Sync:**

1. Скачивает архив исходников/релиза.
2. Валидирует структуру.
3. Распаковывает в staging.
4. Находит `bin/lists/utils/fake/general*.bat`.
5. Проверяет `winws2.exe` и его версию.
6. Сравнивает с текущей версией.
7. Создаёт backup текущего runtime.
8. Атомарно заменяет runtime.
9. Обновляет импортированные стратегии.
10. Записывает provenance (источник, дата).

Запрещено скачивать и сразу выполнять, перезаписывать runtime без backup, автоматически активировать стратегии после sync, молча заменять кастомные файлы.

**StressOzz Sync:**

1. Скачивает `Zapret‑Manager.sh`.
2. Извлекает стратегии Dv/Yv/Gv/v.
3. Извлекает логику wssize/RKN/exclude как reference.
4. Нормализует эти стратегии под `winws2`.
5. Помечает спорные элементы `NEEDS_VERIFICATION`.
6. Не переносит напрямую Linux‑команды.

**bol‑van Reference Sync:**

Используется для составления справочников по параметрам, моделям hostlist/autohostlist и блокчек‑логике.  Не предполагает автоматического копирования кода.

### 5.5 Test Engine

**Назначение:** тестовый движок — сердце продукта.  Программа должна помочь подобрать рабочую стратегию под конкретные условия пользователя.

**Где:** `tests_engine/{domain_sets,probes,baseline,runner,strategy_sweep,proof_of_effect,problem_domains,result_store}.py` и `strategies/ranking.py`.

**Виды тестов:**

* Baseline without zapret;
* Quick test current strategy;
* Full test current strategy;
* Test selected strategy;
* Test all базовые стратегии;
* Test Flowseal‑импортированные;
* Test StressOzz‑импортированные;
* Test Discord (`Dv`) стратегии;
* Test YouTube (`Yv`) стратегии;
* Test Games (`Gv`) стратегии;
* Test custom domain;
* Test domain set;
* Problem domains retest;
* Proof‑of‑effect test.

**Проверяемые метрики:**

* DNS resolve;
* TCP connect на порты 80/443;
* UDP/QUIC reachability на порт 443;
* HTTP GET;
* HTTPS GET;
* latency;
* timeout;
* connection reset;
* process crash;
* missing assets;
* strategy invalid;
* изменилось ли состояние относительно baseline.

**Процесс `Test All`:**

1. Сохраняется текущий runtime‑state.
2. Запускается baseline.
3. Для каждой стратегии: валидируется, стартуется, ждёт warm‑up, тестирует домены, останавливается, собирает результат, помечает crashes/missing assets.
4. Восстанавливается прежнее состояние.
5. Результаты сохраняются в ranking.
6. Пользователю предлагается применить лучшую, либо закрепить Top‑5.
7. Проблемные домены добавляются в `problem_domains`.

**UX:** прогресс отображается (например, «Testing strategies: 12/84, Current: Flowseal general ALT5, Domains: 4/10, Status: OK 7, FAIL 2, TIMEOUT 1»).  После завершения показывается лучший результат, score, работа Discord/YouTube/Games, предупреждения, и действия: Apply best, Pin top 5, View details, Export report.

**Хранение результатов:**

* `DedZapretData/data/telemetry/strategy_runs.jsonl` — сырые результаты тестов;
* `DedZapretData/data/telemetry/latest_strategy_ranking.json` — последний рейтинг;
* `DedZapretData/data/problem_domains.json` — проблемные домены;
* `DedZapretData/logs/session_*.jsonl` — телеметрия тестов.

### 5.6 VPN / Proxy / sing‑box Layer

**Назначение:** обеспечить необязательный proxy/VPN‑режим.  Этот слой не должен смешиваться с `winws2`.

**Где:** `connectivity/singbox/{binary,nodes,subscriptions,config_builder,process,health,system_proxy}.py`.

**Режимы:**

* `winws2` only;
* proxy only;
* `winws2` + proxy (combined);
* disabled;
* error state.

**Функции:**

* **`import_node()`** — поддерживает форматы `vless://`, `vmess://`, `trojan://`, `ss://`, `sing‑box` json, подмножество `clash` yaml, base64‑subscription, plain subscription.
* **`preview_subscription()`** — скачивает subscription, парсит, показывает список узлов, не активируя его, показывает ошибки.
* **`update_subscription()`** — скачивает, сравнивает с существующими узлами, добавляет/обновляет узлы, не меняет active node без явного правила, записывает audit.
* **`build_singbox_config()`** — строит конфигурацию по active node, локальным портам (socks/mixed), DNS‑режиму, маршрутам и outbound.
* **`start_proxy()`** — валидирует binary и active node, строит конфигурацию, запускает процесс, записывает `current.json`, проверяет порты, при необходимости включает system proxy.

**UX:** не следует называть режим «VPN», если включён только локальный socks‑proxy.  Следует отображать: «Proxy mode: ON, Engine: sing‑box, Local SOCKS: 127.0.0.1:2080, Mixed: 127.0.0.1:2081, System proxy: OFF, Active node: Netherlands‑1».

### 5.7 Profiles

**Назначение:** профиль — это сценарий пользователя, а не просто набор параметров.  Профиль может включать базовую стратегию, слои YouTube/Discord/Games, режим RKN/wssize, настройки proxy, DNS/hosts, правила автозапуска и даже процесс‑watcher.

**Где:** `profiles/{model,store,resolver,watcher}.py`.

**Модель профиля** (пример):

```json
{
  "id": "discord_youtube_safe",
  "name": "Discord + YouTube Safe",
  "description": "Для Discord и YouTube без игровых оверлеев",
  "winws2": {
    "enabled": true,
    "base_strategy": "flowseal.general.alt5",
    "youtube_layer": "Yv3",
    "discord_layer": "Dv12",
    "games_profile": "",
    "rkn": false,
    "wssize": false
  },
  "proxy": {
    "enabled": false,
    "active_node_id": ""
  },
  "network": {
    "doh": "system",
    "hosts_blocks": [],
    "quic_block": false,
    "tcp_timestamps": "unchanged"
  },
  "autostart": {
    "start_with_windows": false,
    "start_minimized": true
  },
  "watch": {
    "processes": ["Discord.exe"],
    "auto_start": true,
    "auto_stop": false
  }
}
```

**Встроенные профили:** Default Safe; YouTube; Discord; YouTube + Discord; Games Gv1–Gv4; Proxy only; Combined winws2 + proxy; Custom.

**UX:** вместо сырых указаний «включить Dv12 + Yv3 + Gv2» пользователь выбирает профиль «Discord + YouTube», видит его описание, используемые стратегии и слои, и может запустить, протестировать или отредактировать профиль.

### 5.8 Autostart / Service / Tray

**Назначение:** сделать программу нормальной Windows‑утилитой, которая может стартовать с системой, жить в трее и управляться без командной строки.

**Где:** `windows_ops/{autostart,task_scheduler}.py`, `ui/tray/{tray_app,tray_status,tray_menu,tray_worker}.py`, `core.commands`.

**Функции автозапуска:**

* `enable_autostart()` — создаёт задачу в Task Scheduler, запускающую программу от имени пользователя с нужными параметрами;
* `disable_autostart()` — удаляет задачу;
* `repair_autostart()` — проверяет, что задача существует и работает, и восстанавливает её при повреждении;
* `get_autostart_status()` — возвращает текущий статус и параметры;
* `set_start_minimized()` — включает режим «запускать в трее»;
* `set_restore_last_profile()` — восстанавливает последнюю активную стратегию/профиль при старте.

**Реализация:** использовать Windows Task Scheduler, а не Startup folder; опция «highest privileges»; логировать путь и имя задачи; иметь возможность восстановить задачу.

**Tray:** в системном трее должно отображаться состояние (серый — выключено; зелёный — winws2 активен; синий — proxy only; жёлтый — предупреждение; красный — ошибка; фиолетовый — идёт тест/операция).  Меню в трее должно позволять: Start current profile, Stop all, Restart, Profiles >, Strategies >, Tests >, Proxy/VPN >, Diagnostics >, Open logs, Create bug report, Settings, Exit safely.  Tooltip показывает текущее состояние: активный профиль, PID, proxy, последний тест, количество предупреждений.  Tray вызывает только `core.commands`.

### 5.9 DNS / Hosts / Network Operations

**Назначение:** централизованно управлять опасными изменениями в Windows — hosts, DNS, firewall, TCP timestamps, registry‑proxy.  Всё должно иметь обратный откат.

**Где:** `windows_ops/{hosts,dns,doh,firewall,tcp_timestamps,registry_proxy}.py`, `core.audit`.

**Hosts:**

* `add_manager_block()` — добавляет записи hosts, помечая свои строки;
* `remove_manager_block()` — убирает только свои записи;
* `clear_manager_blocks()` — убирает все свои блоки;
* `backup_hosts()` и `restore_hosts_backup()` — делают резервную копию;
* `get_hosts_status()` — возвращает состояние hosts (чистый, изменённый, backup exists).

Правило: программа должна помечать свои строки комментариями, не трогать чужие записи и всегда создавать backup перед изменением.

**DNS/DoH:**

* `get_dns_status()` — показывает, какие DNS‑серверы используются и в каком интерфейсе;
* `enable_doh_profile()` — включает указанный профиль DoH;
* `disable_doh()` — возвращает системный режим;
* `restore_previous_dns()` — откатывает изменения;
* `test_dns()` — проверяет, что DNS отвечает.

Правило: всегда сохранять предыдущее состояние; не менять DNS без проверки прав администратора; показывать имя адаптера.

**QUIC / TCP timestamps:**

* `enable_quic_block()`, `disable_quic_block()`, `get_quic_status()`;
* `enable_tcp_timestamps()`, `disable_tcp_timestamps()`, `show_tcp_timestamps_status()`.

UX: при необходимости изменить TCP timestamps показывать предупреждение и объяснять последствия.

### 5.10 Diagnostics / Logs / Bug Reports

**Назначение:** встроенная поддержка диагностики и создания bug‑reports.

**Где:** `core/{diagnostics,report,logging,mask}.py`, `features/diagnostics_artifacts.py`, `core.audit`.

**Логи:** `app.log` (общий), `runtime.log` (winws2), `session_*.jsonl` (тесты), `audit.jsonl` (действия), `crash.log`, `strategy_runs.jsonl`, `singbox.log`.

**Diagnostics:** выполняет серию проверок: Windows/admin/path, config/state/current, наличие winws2, WinDivert, fake/list, состояние registry, активный профиль, runtime‑процесс, порты, DNS, hosts, proxy, autostart, tray, результаты последнего теста.  Выводит отчёт и подсказки по устранению.

**Bug report ZIP:**

* содержимое: meta.json, замаскированные config/state/current, маскированные логи, состояние runtime, summary registry, latest ranking, problem domains, `tree.txt` (структура данных);
* исключает: raw proxy links, UUID/password/token, subscription URL secrets, private node passwords, unmasked registry/proxy credentials;
* UX: после генерации выводит путь (`DedZapretData/reports/report_YYYY-MM-DD_HH-mm.zip`), сообщает, что секреты замаскированы, можно приложить к GitHub‑issue.

### 5.11 Updates / Repair / Backup

**Назначение:** пользователь должен иметь возможность безопасно обновить runtime, импортировать стратегии, восстановить недостающие файлы и сделать резервные копии.

**Где:** `upstreams/flowseal_sync.py`, `upstreams/stressozz_sync.py`, `runtime/winws2/repair.py`, `core/backup.py`, `core.commands`.

**Update runtime:** проверяет источник Flowseal, скачивает в staging, валидирует, делает backup текущей версии, заменяет атомарно, перестраивает registry и запускает health‑check.  Не запускает runtime автоматически.

**Update strategies:** синхронизирует StressOzz, импортирует Flowseal bat‑стратегии, нормализует и классифицирует, записывает сгенерированные стратегии, сохраняет кастомные, показывает diff summary.

**Repair runtime:** копирует отсутствующие fake assets из upstream, копирует отсутствующие lists, создаёт пустые user‑файлы только при необходимости, никогда не создаёт fake `.bin` placeholders, объясняет, что было исправлено.

**Backup:** делает копии config/state/current, кастомных стратегий, профилей, hosts перед модификацией, runtime перед обновлением.

---

## 6. Структура Console UI

Console‑интерфейс имитирует вкладки: сверху всегда показан dashboard, ниже — горизонтальные вкладки.  Предлагается 11 вкладок:

1. **Главная** — Start/Stop, текущий статус, предупреждения, быстрые действия, недавние события.
2. **Подключение** — статус winws2, статус процесса, пути runtime, start/stop/restart, repair runtime, открыть папку runtime.
3. **Стратегии** — списки base/Flowseal/StressOzz/Yv/Dv/Gv/RKN/wssize, проверка конфликтов, применение, валидация.
4. **Тесты** — baseline, quick current, full current, test all, domain set, custom domain, proof‑of‑effect, ranking, pin top 5, problem domains.
5. **Профили** — список профилей, запуск, тестирование, создание/редактирование/удаление, установка по умолчанию, watcher.
6. **VPN / Proxy** — статус sing‑box, узлы, подписки, preview/update subscription, активный узел, start/stop proxy, system proxy toggle.
7. **DNS / Hosts** — статус DNS, DoH, блокировки hosts, режимы RKN/exclude, блокировка QUIC, TCP timestamps, rollback.
8. **Автозапуск / Tray** — статус автозапуска, enable/disable/repair task, start minimized, restore last profile, статус трея.
9. **Диагностика** — запуск диагностики, health runtime, health стратегии, health proxy, health Windows, создание bug report.
10. **Логи** — просмотр логов, фильтрация по типу (info/warn/error/audit), экспорт, очистка, маскирование.
11. **Настройки** — portable paths, runtime path, расположение config/state, язык, тема, расширенные настройки, сброс.

В продвинутом режиме доступны подробные сведения (raw args, registry, asset resolver, JSON тестов, детали процесса runtime).

---

## 7. Command/Service Layer

Все действия выполняются через `core.commands`, чтобы UI оставался тонким.  Примеры функций:

```python
get_status_summary()
start_current()
stop_all()
restart_current()
start_profile(profile_id)
test_current(mode)
test_all(scope)
apply_strategy(strategy_id)
apply_recommended_strategy()
update_flowseal_runtime()
update_stressozz_strategies()
repair_runtime()
create_bug_report()
enable_autostart()
disable_autostart()
start_proxy()
stop_proxy()
enable_doh()
disable_doh()
```

Каждая команда возвращает объект примерно такого вида:

```json
{
  "ok": true,
  "message": "Runtime started",
  "details": {},
  "warnings": [],
  "errors": [],
  "next_actions": []
}
```

Это обеспечивает единый контракт между логикой и UI.

---

## 8. User‑friendly требования

Для удобства пользователя нужно соблюдать несколько правил:

1. **Всегда показывать состояние.** Пользователь должен видеть, включено ли что‑то, какой PID запущен, готова ли стратегия, включён ли proxy, изменён ли DNS, изменён ли hosts.

2. **Ошибка = причина + действие.** Вместо «FileNotFoundError» показывать: «Не найден winws2.exe.  Возможные причины: runtime Flowseal не скачан; файл удалён антивирусом; путь изменён.  Что сделать: (1) Update Flowseal runtime; (2) Repair runtime; (3) Указать путь вручную.»

3. **Никаких скрытых side‑effects.** Перед изменением hosts/DNS/proxy/autostart перечислять, что будет сделано, и дать возможность отменить.

4. **Безопасные значения по умолчанию.** По умолчанию не включать system proxy, не менять DNS, не активировать subscription после preview, не удалять custom‑стратегии, не запускать invalid‑strategy, не fallback‑аться с winws2 на winws молча.

5. **«Вернуть как было».** Для каждого опасного действия — кнопка отмены: restore previous DNS; restore hosts backup; disable autostart; stop all; restore last working strategy; rollback runtime update.

6. **Режим новичка и продвинутого пользователя.** Новичок видит основные кнопки (Start, Stop, Auto‑pick best, Fix problems, Bug report), продвинутый может раскрыть подробности (raw args, registry, asset resolver, тесты JSON, детали процесса runtime).

---

## 9. Приоритеты реализации

План разработки делится на этапы.  Каждый этап завершает независимую часть и обеспечивает тесты.

1. **Stage 0 — Документация и правила.** Создать основные документы: `PRODUCT_OVERVIEW.md`, `PROGRAM_BLUEPRINT.md`, `OPERATIONS_AND_QOL_SPEC.md`, `RUNTIME_SOURCE_POLICY.md`, `DEDZAPRET_AGENT_RULES.md`.

2. **Stage 1 — Characterization tests.** Перед рефакторингом создать тесты для config/state/current, paths, strategy loader, Flowseal import, StressOzz import, snapshot сборки команды winws2, диагностики/отчёта, hosts/DNS dry‑run, sing‑box config.

3. **Stage 2 — Path/config/state foundation.** Создать единый portable layout, строгие модели `config/state/current`, atomic‑записи, backup перед мутациями.

4. **Stage 3 — winws2 runtime layer.** Реализовать detector, asset resolver, command model, preflight, процесс‑manager, health для winws2.

5. **Stage 4 — Strategy registry.** Реализовать единый registry, provenance, импортеры Flowseal/StressOzz, validation, classification.

6. **Stage 5 — Test engine.** Реализовать baseline, тест текущей стратегии, тест всех, ранжирование, problem domains, proof‑of‑effect.

7. **Stage 6 — Connectivity layer.** Реализовать поддержу sing‑box: nodes, subscriptions, builder, process, system proxy optional.

8. **Stage 7 — Windows operations.** Реализовать hosts, DNS/DoH, QUIC, TCP timestamps, autostart, task scheduler, safe rollback.

9. **Stage 8 — Profiles.** Реализовать сценарные профили, last working profile, watcher и тесты профилей.

10. **Stage 9 — Console UI rebuild.** Реализовать dashboard, вкладки, дружелюбные ошибки, быстрые действия, advanced details.

11. **Stage 10 — Tray.** Реализовать status icon, quick actions, switch profiles/strategies, bug report, test current, safe exit.

12. **Stage 11 — Cleanup.** После прохождения тестов удалить дубликаты, объединить старые модули, удалить проверенный мёртвый код, обновить документацию.

---

## 10. Главная архитектурная формула

Формула, определяющая DedZapret Manager:

```
DedZapret Manager
  = Flowseal winws2 runtime base
  + bol-van zapret semantics
  + StressOzz strategy/workflow logic
  + Windows-safe operations layer
  + test/ranking engine
  + proxy/VPN connectivity layer
  + profiles/autostart/tray QoL
  + diagnostics/reporting
  + user-friendly console/GUI-ready command layer
```

**Самое важное правило:** не упрощать программу до запускалки winws2.  Тесты, VPN/proxy, автозапуск, трей, профили, диагностика, обновления, repair, backup и rollback — это не вторичные хотелки, а полноценные продуктовые функции DedZapret Manager.

---

## Build Mode

This is a **fresh build**, not an in-place migration.
The old repository is reference material only:
- useful behavior;
- bugs to avoid;
- strategy logic;
- UI/UX lessons;
- tests and diagnostics lessons.
Do not preserve old architecture if it is messy.
Preserve useful behavior and requirements, not accidental code structure.
Extract intent, write clean modules, cover with tests.

---

Этот документ является руководством для архитекторов и разработчиков.  Он описывает желаемую структуру, функции и UX.  Любые изменения должны следовать этим принципам, а тесты и документация должны поддерживаться в актуальном состоянии.