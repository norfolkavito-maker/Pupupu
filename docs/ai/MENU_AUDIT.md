# MENU AUDIT

**Project**: DedZapret / ZapretManager for Windows
**Date**: 2025-01-13
**Phase**: 1 - MENU INVENTORY ONLY

---

## 1. Current Menu Tree

### Main Menu (run_main_menu in main_menu.py)

```
╔═══════════════════════════╗
║ DEDZAPRET (Windows)        ║
╚═══════════════════════════╝

Status summary (runtime, zapret, strategy, layers, DoH, QUIC, problem domains, sing-box)

1) Старт / Стоп
2) Быстрый статус
3) Стратегии
4) Тест стратегий
5) Ноды / sing-box
6) DNS / hosts / системные настройки
7) Диагностика и ремонт
8) Логи и bug report
9) Обновления
10) Настройки
11) Advanced / Dev tools
```

### Submenu Tree

```
1) Старт / Стоп
   - If running: stop_zapret()
   - If stopped: _ask_strategy_before_start() → start_zapret_interactive()
     - Option 1: Use recommended v9
     - Option 2: Open strategies menu
     - Option 3: Show available strategies

2) Быстрый статус
   → auto_setup_menu()
   - 1) Быстрая автонастройка «под ключ»
   - 2) Под ключ + полная проверка/подбор (мастер)
   - 3) Просмотр проблемных доменов
   - 4) Очистить проблемные домены

3) Стратегии
   → strategies_menu()
   Status: Base, Recommended, Engine mode, YouTube, Discord, RKN, Games, wssize
   
   Основное:
   - R) Выбрать Recommended
   - 1) Выбрать и установить стратегию v1-v9
   - 2) Выбрать и установить стратегию от Flowseal
   
   Профили / слои:
   - 3) Выбрать и установить стратегию для YouTube
   - 4) Выбрать и установить стратегию для игр
   
   Опции:
   - 5) Включить / Выключить обход по спискам РКН
   - 6) Обновить список исключений
   - 7) Добавить / Удалить блок с --wssize 1:6
   - C) Проверить конфликты текущих слоёв (MVP)

   Sub-submenus:
   - _pick_flowseal_base() → list Flowseal strategies
   - _pick_youtube_layer() → list Yv strategies
   - _games_menu() → Gv1-Gv4 profiles
   - _strategy_conflicts_menu() → conflict checker

4) Тест стратегий
   → test_menu()
   Speed: concurrency setting
   
   Основное:
   - T) Тест всех стратегий — рейтинг + прогресс
   - 4) Тест текущей стратегии — быстрый sanity-check
   - 0) Control test (без zapret) — базовая доступность
   - 9) Тест проблемных доменов / автоподбор — TOP-5 и применение
   - 8) Proof-of-effect test — baseline vs strategy
   
   Группы стратегий:
   - 1) Тестировать стратегии v
   - 2) Тестировать стратегии Flowseal
   - 3) Тестировать v и Flowseal стратегии
   - 5) Тестировать стратегии по домену
   - 6) YouTube auto-test (Yv)
   
   Результаты:
   - L) Последний рейтинг стратегий
   - R) Применить Recommended стратегию
   - P) Сохранить TOP-5
   - A) Результаты тестирования стратегий (if have results)
   - D) Удалить результаты тестирования (if have results)
   
   Настройки теста:
   - 7) Выбрать набор доменов
   - S) Настройки скорости теста
   - O) Подробный / компактный вывод

5) Ноды / sing-box
   → singbox_menu()
   Status: installed, nodes count, active, running, DNS mode
   
   - 1) Диагностика sing-box / Health check
   - 2) Status / diagnostics
   - 3) Import single link (vless/vmess/trojan/ss)
   - 4) Add subscription URL
   - 5) Update subscriptions
   - 6) List nodes
   - 7) Select active node
   - 8) Generate config preview
   - 9) Start local proxy
   - 10) Enable system proxy (explicit confirm)
   - 11) Restore system proxy
   - 12) Stop sing-box
   - 13) Restart sing-box

6) DNS / hosts / системные настройки
   → hosts_menu()
   - 0-9) Toggle category blocks
   - 10) Toggle all blocks
   - 11) Reset hosts

7) Диагностика и ремонт
   → diagnostics_menu() → _runtime_menu()
   Status: Runtime, Diagnostics
   
   - 1) Показать runtime diagnostics
   - 2) Запустить blockcheck
   - R) Repair runtime assets (lists + fake)
   - 3) Запустить blockcheck2
   - 4) Toggle Diagnostics (в config.yaml)

8) Логи и bug report
   → logs_menu()
   - PLACEHOLDER: "Пока не реализовано в этой версии. Записано в лог."

9) Обновления
   → updates_menu() → _upstreams_menu()
   - 1) Проверить обновления upstream
   - 2) Sync Flowseal
   - 3) Sync StressOzz
   - 4) Sync оба (Flowseal + StressOzz)
   - 5) Обновить exclude + RKN list

10) Настройки
    → settings_menu() → system_menu()
    - 1) Runtime / Blockcheck / Diagnostics
    - 2) Upstreams (обновления стратегий)
    - A) DedZapret App Update (самообновление)
    - 3) Network (QUIC / TCP timestamps / Flush DNS)
    - 4) Backup / Restore
    - 5) Системная информация
    - S) Support: Generate bug report
    - X) Support: Сформировать диагностические артефакты

    Sub-submenus:
    - _runtime_menu() (same as diagnostics_menu)
    - _upstreams_menu() (same as updates_menu)
    - _app_update_menu()
      - 1) Check app updates (latest release)
      - 2) Download & install latest portable release
      - 3) Открыть update.log
    - _network_menu()
      - 1) Вкл/выкл блокировку QUIC (UDP 443)
      - 2) TCP timestamps: enabled
      - 3) TCP timestamps: disabled
      - 4) Flush DNS
    - _backup_menu()
      - 1) Бэкап (zip)
      - 2) Восстановить из бэкапа (zip)
      - 3) Автонастройка «под ключ» (без переустановки)
      - 4) Под ключ + полная проверка/подбор (мастер)

11) Advanced / Dev tools
    → advanced_menu()
    - PLACEHOLDER: "Пока не реализовано в этой версии. Записано в лог."
```

### Tray Menu (tray_menu.py)

```
DedZapret
Статус: ACTIVE / OFF / ERROR

Основное
- Включить Recommended
- Отключить всё
- Перезапустить текущий режим

VPN
- Активировать VPN (local proxy)
- Отключить VPN
- Перезапустить VPN
- Выбрать локацию (submenu with nodes)
- Обновить подписку

Стратегии
- Recommended: <name>
- Текущая: <name>
- Выбрать стратегию... (в консоли) [disabled]
- Тест всех стратегий...
- Остановить тест/задачу

Диагностика
- Диагностика sing-box
- Починить runtime assets
- Создать отчёт об ошибке (bug report)
- Открыть логи

Настройки
- Автозапуск: (ещё не реализовано) [disabled]
- Запускать в трей: меняется в config.yaml [disabled]
- Runtime engine
  - Auto
  - winws
  - winws2
- Открыть полное меню (в консоли) [disabled]

Выход
```

---

## 2. Menu Item Inventory Table

| Current path | Label | Key | Handler/function | Module | Status | Notes |
|-------------|-------|-----|------------------|--------|--------|-------|
| Main | Старт / Стоп | 1 | run_main_menu() choice 1 | main_menu.py | KEEP | Core functionality |
| Main | Быстрый статус | 2 | auto_setup_menu() | menus.py | MOVE | Should be in Diagnostics or Settings |
| Main | Стратегии | 3 | strategies_menu() | menus.py | KEEP | Core functionality |
| Main | Тест стратегий | 4 | test_menu() | menus.py | KEEP | Core functionality |
| Main | Ноды / sing-box | 5 | singbox_menu() | singbox_menu.py | KEEP | VPN functionality |
| Main | DNS / hosts / системные настройки | 6 | hosts_menu() | menus.py | MOVE | Should be in Settings |
| Main | Диагностика и ремонт | 7 | diagnostics_menu() → _runtime_menu() | menus.py | KEEP | Core functionality |
| Main | Логи и bug report | 8 | logs_menu() | menus.py | BROKEN | Placeholder only |
| Main | Обновления | 9 | updates_menu() → _upstreams_menu() | menus.py | KEEP | Core functionality |
| Main | Настройки | 10 | settings_menu() → system_menu() | menus.py | KEEP | Core functionality |
| Main | Advanced / Dev tools | 11 | advanced_menu() | menus.py | BROKEN | Placeholder only |
| Auto Setup | Быстрая автонастройка «под ключ» | 1 | key_setup() | features/key_setup.py | KEEP | Core functionality |
| Auto Setup | Под ключ + полная проверка/подбор | 2 | key_setup_full_check() | features/key_setup.py | KEEP | Core functionality |
| Auto Setup | Просмотр проблемных доменов | 3 | _problem_domains_menu() | menus.py | MOVE | Should be in Test menu |
| Auto Setup | Очистить проблемные домены | 4 | clear_problem_domains() | features/problem_domains.py | MOVE | Should be in Test menu |
| Strategies | Выбрать Recommended | R | apply_recommended_strategy() | core/commands.py | KEEP | Core functionality |
| Strategies | Выбрать стратегию v1-v9 | 1 | _set_base() | menus.py | KEEP | Core functionality |
| Strategies | Выбрать стратегию Flowseal | 2 | _pick_flowseal_base() | menus.py | KEEP | Core functionality |
| Strategies | Выбрать стратегию YouTube | 3 | _pick_youtube_layer() | menus.py | KEEP | Core functionality |
| Strategies | Выбрать стратегию игр | 4 | _games_menu() | menus.py | KEEP | Core functionality |
| Strategies | Включить / Выключить РКН | 5 | _toggle_rkn() | menus.py | KEEP | Core functionality |
| Strategies | Обновить список исключений | 6 | update_exclude() | features/lists.py | KEEP | Core functionality |
| Strategies | Добавить / Удалить wssize | 7 | toggle wssize_enabled | menus.py | KEEP | Core functionality |
| Strategies | Проверить конфликты | C | _strategy_conflicts_menu() | menus.py | KEEP | Core functionality |
| Test | Тест всех стратегий | T | _test_all_strategies_menu() | menus.py | KEEP | Core functionality |
| Test | Тест текущей стратегии | 4 | _run_test_current() | menus.py | KEEP | Core functionality |
| Test | Control test | 0 | _run_control_test() | menus.py | KEEP | Core functionality |
| Test | Тест проблемных доменов | 9 | _problem_domains_menu() | menus.py | KEEP | Core functionality |
| Test | Proof-of-effect test | 8 | _run_proof_of_effect_test() | menus.py | KEEP | Core functionality |
| Test | Тестировать v | 1 | _run_test_group(group="v") | menus.py | KEEP | Core functionality |
| Test | Тестировать Flowseal | 2 | _run_test_group(group="flowseal") | menus.py | KEEP | Core functionality |
| Test | Тестировать v+Flowseal | 3 | _run_test_group(group="all") | menus.py | KEEP | Core functionality |
| Test | Тестировать по домену | 5 | _run_test_by_domain() | menus.py | KEEP | Core functionality |
| Test | YouTube auto-test | 6 | _youtube_auto_test() | menus.py | KEEP | Core functionality |
| Test | Последний рейтинг | L | _show_latest_ranking() | menus.py | KEEP | Core functionality |
| Test | Применить Recommended | R | apply_recommended_strategy() | core/commands.py | DUPLICATE | Duplicate of Strategies menu |
| Test | Сохранить TOP-5 | P | _save_top5() | menus.py | KEEP | Core functionality |
| Test | Результаты | A | _show_results() | menus.py | KEEP | Core functionality |
| Test | Удалить результаты | D | delete results files | menus.py | KEEP | Core functionality |
| Test | Выбрать набор доменов | 7 | _choose_domain_set() | menus.py | KEEP | Core functionality |
| Test | Настройки скорости | S | _speed_settings_menu() | menus.py | KEEP | Core functionality |
| Test | Подробный / компактный вывод | O | toggle detailed_console_output | menus.py | KEEP | Core functionality |
| Sing-box | Диагностика sing-box | 1 | _sb_health_check() | singbox_menu.py | KEEP | Core functionality |
| Sing-box | Status / diagnostics | 2 | _sb_status() | singbox_menu.py | KEEP | Core functionality |
| Sing-box | Import single link | 3 | _sb_import_link() | singbox_menu.py | KEEP | Core functionality |
| Sing-box | Add subscription URL | 4 | _sb_add_subscription() | singbox_menu.py | KEEP | Core functionality |
| Sing-box | Update subscriptions | 5 | _sb_update_subscriptions() | singbox_menu.py | KEEP | Core functionality |
| Sing-box | List nodes | 6 | _sb_list_nodes() | singbox_menu.py | KEEP | Core functionality |
| Sing-box | Select active node | 7 | _sb_select_node() | singbox_menu.py | KEEP | Core functionality |
| Sing-box | Generate config preview | 8 | _sb_preview_config() | singbox_menu.py | KEEP | Core functionality |
| Sing-box | Start local proxy | 9 | _sb_start() | singbox_menu.py | KEEP | Core functionality |
| Sing-box | Enable system proxy | 10 | _sb_enable_system_proxy() | singbox_menu.py | KEEP | Core functionality |
| Sing-box | Restore system proxy | 11 | _sb_restore_system_proxy() | singbox_menu.py | KEEP | Core functionality |
| Sing-box | Stop sing-box | 12 | _sb_stop() | singbox_menu.py | KEEP | Core functionality |
| Sing-box | Restart sing-box | 13 | _sb_restart() | singbox_menu.py | KEEP | Core functionality |
| Hosts | Toggle category blocks | 0-9 | set_block_enabled() | features/hosts.py | KEEP | Core functionality |
| Hosts | Toggle all blocks | 10 | toggle all | menus.py | KEEP | Core functionality |
| Hosts | Reset hosts | 11 | reset_hosts_windows() | features/hosts.py | KEEP | Core functionality |
| Runtime | Показать runtime diagnostics | 1 | runtime_diagnostics_text() | features/zapret_runtime.py | KEEP | Core functionality |
| Runtime | Запустить blockcheck | 2 | run_blockcheck() | features/blockcheck.py | KEEP | Core functionality |
| Runtime | Repair runtime assets | R | repair_runtime_assets() | features/runtime_assets.py | KEEP | Core functionality |
| Runtime | Запустить blockcheck2 | 3 | MISSING | menus.py | BROKEN | Handler not found |
| Runtime | Toggle Diagnostics | 4 | _toggle_diagnostics_in_config() | menus.py | KEEP | Core functionality |
| Upstreams | Проверить обновления | 1 | check_updates() | features/upstreams.py | KEEP | Core functionality |
| Upstreams | Sync Flowseal | 2 | sync_flowseal() | features/upstreams.py | KEEP | Core functionality |
| Upstreams | Sync StressOzz | 3 | sync_stressozz_strategies() | features/upstreams.py | KEEP | Core functionality |
| Upstreams | Sync оба | 4 | sync_flowseal + sync_stressozz | features/upstreams.py | KEEP | Core functionality |
| Upstreams | Обновить exclude + RKN | 5 | update_exclude + update_rkn | features/lists.py | KEEP | Core functionality |
| App Update | Check app updates | 1 | build_update_plan() | features/app_update.py | KEEP | Core functionality |
| App Update | Download & install | 2 | run_update() | features/app_update.py | KEEP | Core functionality |
| App Update | Открыть update.log | 3 | show log file | menus.py | KEEP | Core functionality |
| Network | Вкл/выкл QUIC | 1 | quic_block_enable/disable() | features/system.py | KEEP | Core functionality |
| Network | TCP timestamps enabled | 2 | tcp_timestamps_enable() | features/system.py | KEEP | Core functionality |
| Network | TCP timestamps disabled | 3 | tcp_timestamps_disable() | features/system.py | KEEP | Core functionality |
| Network | Flush DNS | 4 | flush_dns() | features/system.py | KEEP | Core functionality |
| Backup | Бэкап (zip) | 1 | backup() | features/system.py | KEEP | Core functionality |
| Backup | Восстановить из бэкапа | 2 | restore() | features/system.py | KEEP | Core functionality |
| Backup | Автонастройка «под ключ» | 3 | key_setup() | features/key_setup.py | DUPLICATE | Duplicate of Auto Setup |
| Backup | Под ключ + полная проверка | 4 | key_setup_full_check() | features/key_setup.py | DUPLICATE | Duplicate of Auto Setup |
| System | Системная информация | 5 | system_info_text() | features/sysinfo.py | KEEP | Core functionality |
| System | Generate bug report | S | _support_generate_bug_report() | menus.py | KEEP | Core functionality |
| System | Generate diagnostics artifacts | X | _support_generate_diagnostics_artifacts() | menus.py | KEEP | Core functionality |
| Logs | PLACEHOLDER | - | logs_menu() | menus.py | BROKEN | Not implemented |
| Advanced | PLACEHOLDER | - | advanced_menu() | menus.py | BROKEN | Not implemented |

---

## 3. Handler Trace

### Main Menu Handlers

#### run_main_menu()
- **File**: `app/zapret_manager/ui/main_menu.py`
- **What it does**: Main menu loop with status display and 11-item menu
- **State files**: Reads `state.json`, `current.json`, `latest_strategy_ranking.json`
- **Runtime/system actions**: Starts/stops zapret, calls submenus
- **External processes**: winws.exe (via start_zapret_interactive)
- **Safe for normal user**: YES

#### _offer_repair_and_retry_start()
- **File**: `app/zapret_manager/ui/main_menu.py`
- **What it does**: Offers runtime repair and retry if winws fails to start
- **State files**: None
- **Runtime/system actions**: Calls repair_runtime_assets(), restarts winws
- **External processes**: None
- **Safe for normal user**: YES

#### _startup_baseline_prompt()
- **File**: `app/zapret_manager/ui/main_menu.py`
- **What it does**: On first run, offers baseline test without zapret
- **State files**: Reads problem_domains.json
- **Runtime/system actions**: Runs control_test_mode()
- **External processes**: None
- **Safe for normal user**: YES

#### _status_lines()
- **File**: `app/zapret_manager/ui/main_menu.py`
- **What it does**: Builds status summary for main menu display
- **State files**: Reads `state.json`, `current.json`, `problem_domains.json`
- **Runtime/system actions**: Calls runtime_health(), validate_strategy_assets()
- **External processes**: None
- **Safe for normal user**: YES

#### _all_strategies()
- **File**: `app/zapret_manager/ui/main_menu.py`
- **What it does**: Returns all strategies from builtin, generated, custom dirs
- **State files**: None
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _load_selected_strategy()
- **File**: `app/zapret_manager/ui/main_menu.py`
- **What it does**: Loads currently selected strategy from state
- **State files**: Reads `state.json`
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _find_strategy_by_name()
- **File**: `app/zapret_manager/ui/main_menu.py`
- **What it does**: Finds strategy by name (case-insensitive)
- **State files**: None
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _ask_strategy_before_start()
- **File**: `app/zapret_manager/ui/main_menu.py`
- **What it does**: Prompts user to select strategy before starting zapret
- **State files**: Writes `state.json`
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _hidden_888()
- **File**: `app/zapret_manager/ui/main_menu.py`
- **What it does**: Reserved hidden menu slot (not used)
- **State files**: None
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES (but hidden)

### Submenu Handlers (menus.py)

#### auto_setup_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Quick auto-setup wizard
- **State files**: Writes `state.json`, `problem_domains.json`
- **Runtime/system actions**: Calls key_setup(), key_setup_full_check()
- **External processes**: None
- **Safe for normal user**: YES

#### extras_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Extras menu (YouTube/Discord/Games/TG/DNS/Hosts/Launcher)
- **State files**: Writes `state.json`, `hosts/blocks.json`
- **Runtime/system actions**: Calls discord_menu(), tg_menu(), doh_menu(), hosts_menu(), game_launcher_menu()
- **External processes**: None
- **Safe for normal user**: YES

#### service_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Wrapper around system_menu()
- **State files**: None
- **Runtime/system actions**: Calls system_menu()
- **External processes**: None
- **Safe for normal user**: YES

#### strategies_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Strategy selection and configuration
- **State files**: Writes `state.json`
- **Runtime/system actions**: Calls _restart_if_running() which starts/stops winws
- **External processes**: winws.exe
- **Safe for normal user**: YES

#### _strategy_conflicts_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: MVP conflicts checker
- **State files**: None
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _set_base()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Sets base strategy and restarts if running
- **State files**: Writes `state.json`
- **Runtime/system actions**: Calls _restart_if_running()
- **External processes**: winws.exe
- **Safe for normal user**: YES

#### _pick_flowseal_base()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Picks Flowseal base strategy
- **State files**: Writes `state.json`
- **Runtime/system actions**: Calls _restart_if_running()
- **External processes**: winws.exe
- **Safe for normal user**: YES

#### _pick_youtube_layer()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Picks YouTube layer strategy
- **State files**: Writes `state.json`
- **Runtime/system actions**: Calls _restart_if_running()
- **External processes**: winws.exe
- **Safe for normal user**: YES

#### _games_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Games profile selection (Gv1-Gv4)
- **State files**: Writes `state.json`
- **Runtime/system actions**: Calls _restart_if_running()
- **External processes**: winws.exe
- **Safe for normal user**: YES

#### _toggle_rkn()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Toggles RKN list bypass
- **State files**: Writes `state.json`, updates rkn.txt
- **Runtime/system actions**: Calls _restart_if_running()
- **External processes**: winws.exe
- **Safe for normal user**: YES

#### discord_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Discord configuration (scripts, Finland hosts, Dv layer)
- **State files**: Writes `state.json`, `hosts/blocks.json`
- **Runtime/system actions**: Calls _restart_if_running(), flush_dns()
- **External processes**: winws.exe
- **Safe for normal user**: YES

#### _pick_dv()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Picks Discord Dv layer strategy
- **State files**: Writes `state.json`
- **Runtime/system actions**: Calls _restart_if_running()
- **External processes**: winws.exe
- **Safe for normal user**: YES

#### hosts_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Hosts file management
- **State files**: Reads/writes `hosts/blocks.json`, modifies Windows hosts file
- **Runtime/system actions**: Calls set_block_enabled(), flush_dns(), reset_hosts_windows()
- **External processes**: None (modifies Windows hosts file)
- **Safe for normal user**: YES (but modifies system file)

#### test_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Strategy testing menu
- **State files**: Reads/writes `state.json`, reads `latest_strategy_ranking.json`, writes results files
- **Runtime/system actions**: Calls various test functions, starts/stops winws
- **External processes**: winws.exe
- **Safe for normal user**: YES

#### _speed_settings_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Test speed settings configuration
- **State files**: Writes `state.json`
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _choose_test_mode()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Asks user for quick/full test mode
- **State files**: None
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _test_all_strategies_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Test all strategies with progress
- **State files**: Reads/writes `state.json`, writes `latest_strategy_ranking.json`, results files
- **Runtime/system actions**: Calls test_all_strategies_with_progress(), starts/stops winws
- **External processes**: winws.exe
- **Safe for normal user**: YES

#### _show_latest_ranking()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Shows latest strategy ranking
- **State files**: Reads `latest_strategy_ranking.json`
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _save_top5()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Saves TOP-5 strategies to file
- **State files**: Reads `latest_strategy_ranking.json`, writes `latest_strategy_top5.txt`
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _choose_domain_set()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Chooses domain set for testing
- **State files**: Writes `state.json`
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _run_control_test()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Runs control test (baseline without zapret)
- **State files**: Writes results file
- **Runtime/system actions**: Calls control_test_mode(), stops zapret
- **External processes**: winws.exe (stops it)
- **Safe for normal user**: YES

#### _run_test_group()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Tests a group of strategies (v/flowseal/all)
- **State files**: Writes `state.json`, results file
- **Runtime/system actions**: Calls test_session(), starts/stops winws
- **External processes**: winws.exe
- **Safe for normal user**: YES

#### _run_test_current()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Tests current strategy
- **State files**: None
- **Runtime/system actions**: Calls test_strategy()
- **External processes**: None
- **Safe for normal user**: YES

#### _run_test_by_domain()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Tests strategies by specific domains
- **State files**: None
- **Runtime/system actions**: Calls test_strategy()
- **External processes**: None
- **Safe for normal user**: YES

#### _youtube_auto_test()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Auto-tests YouTube strategies
- **State files**: Writes `state.json`
- **Runtime/system actions**: Calls test_strategy(), sync_stressozz_strategies()
- **External processes**: None
- **Safe for normal user**: YES

#### _show_results()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Shows test results file
- **State files**: None
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _run_proof_of_effect_test()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Runs proof-of-effect test (baseline vs strategy)
- **State files**: None
- **Runtime/system actions**: Calls proof_of_effect(), starts/stops winws
- **External processes**: winws.exe
- **Safe for normal user**: YES

#### tg_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: TG WS Proxy menu (Go/Rust)
- **State files**: Writes `state.json`
- **Runtime/system actions**: Calls install/uninstall/start/stop functions
- **External processes**: go.exe, rust.exe
- **Safe for normal user**: YES

#### system_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: System menu (runtime, upstreams, updates, network, backup, diagnostics)
- **State files**: Varies by submenu
- **Runtime/system actions**: Varies by submenu
- **External processes**: Varies by submenu
- **Safe for normal user**: YES

#### _support_generate_bug_report()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Generates masked bug report zip
- **State files**: Reads `state.json`, `current.json`, `config.yaml`, logs
- **Runtime/system actions**: Creates zip file
- **External processes**: None
- **Safe for normal user**: YES

#### _support_generate_diagnostics_artifacts()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Creates diagnostics artifacts
- **State files**: Reads various state files
- **Runtime/system actions**: Creates summary files
- **External processes**: None
- **Safe for normal user**: YES

#### _app_update_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: DedZapret app update menu
- **State files**: Reads `config.yaml`, writes `update.log`
- **Runtime/system actions**: Downloads and installs update
- **External processes**: updater.bat
- **Safe for normal user**: YES (but updates app)

#### _runtime_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Runtime diagnostics and repair
- **State files**: Reads `config.yaml`
- **Runtime/system actions**: Calls runtime_diagnostics_text(), run_blockcheck(), repair_runtime_assets()
- **External processes**: blockcheck.exe
- **Safe for normal user**: YES

#### _upstreams_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Upstream updates (sync strategies)
- **State files**: Writes strategy JSON files, updates list files
- **Runtime/system actions**: Downloads from GitHub
- **External processes**: None
- **Safe for normal user**: YES

#### _network_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Network settings (QUIC, TCP timestamps, DNS)
- **State files**: None
- **Runtime/system actions**: Modifies Windows firewall, registry, DNS cache
- **External processes**: None (modifies system)
- **Safe for normal user**: YES (but modifies system)

#### _backup_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Backup/restore menu
- **State files**: Reads/writes zip files
- **Runtime/system actions**: Calls backup(), restore(), key_setup()
- **External processes**: None
- **Safe for normal user**: YES

#### _toggle_diagnostics_in_config()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Toggles diagnostics.enabled in config.yaml
- **State files**: Writes `config.yaml`
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _restart_if_running()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Restarts zapret if running
- **State files**: Reads/writes `state.json`
- **Runtime/system actions**: Calls stop_zapret(), start_zapret_interactive()
- **External processes**: winws.exe
- **Safe for normal user**: YES

#### game_launcher_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Game/program launcher with profiles
- **State files**: Reads/writes profile files
- **Runtime/system actions**: Generates .bat/.lnk files, launches executables
- **External processes**: User-selected games/programs
- **Safe for normal user**: YES

#### doh_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: DNS over HTTPS configuration
- **State files**: Writes `state.json`
- **Runtime/system actions**: Modifies Windows DNS settings
- **External processes**: None (modifies system)
- **Safe for normal user**: YES (but modifies system)

#### _problem_domains_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Problem domains auto-tuning menu
- **State files**: Reads/writes `problem_domains.json`
- **Runtime/system actions**: Runs strategy tests on problem domains
- **External processes**: winws.exe
- **Safe for normal user**: YES

#### _auto_tune_by_problem_domains()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Auto-tunes strategy by problem domains
- **State files**: Reads `problem_domains.json`
- **Runtime/system actions**: Calls proof_of_effect()
- **External processes**: winws.exe
- **Safe for normal user**: YES

#### _auto_tune_top5_by_problem_domains()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Sweep strategies on problem domains, show TOP-5
- **State files**: Reads/writes `problem_domains.json`, writes results file
- **Runtime/system actions**: Calls test_session(), starts/stops winws
- **External processes**: winws.exe
- **Safe for normal user**: YES

#### settings_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Settings menu (routes to system_menu)
- **State files**: None
- **Runtime/system actions**: Calls system_menu()
- **External processes**: None
- **Safe for normal user**: YES

#### diagnostics_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Diagnostics menu (routes to _runtime_menu)
- **State files**: None
- **Runtime/system actions**: Calls _runtime_menu()
- **External processes**: None
- **Safe for normal user**: YES

#### logs_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Logs and bug report menu (placeholder)
- **State files**: None
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES (but not implemented)

#### advanced_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Advanced / Dev tools menu (placeholder)
- **State files**: None
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES (but not implemented)

#### updates_menu()
- **File**: `app/zapret_manager/ui/menus.py`
- **What it does**: Updates menu (routes to _upstreams_menu)
- **State files**: None
- **Runtime/system actions**: Calls _upstreams_menu()
- **External processes**: None
- **Safe for normal user**: YES

### Sing-box Menu Handlers (singbox_menu.py)

#### singbox_menu()
- **File**: `app/zapret_manager/features/singbox_menu.py`
- **What it does**: Sing-box local proxy menu
- **State files**: Reads/writes `current.json`, `nodes.json`, `subscriptions.json`
- **Runtime/system actions**: Starts/stops sing-box, enables/disables system proxy
- **External processes**: sing-box.exe
- **Safe for normal user**: YES

#### _sb_health_check()
- **File**: `app/zapret_manager/features/singbox_menu.py`
- **What it does**: Sing-box health check
- **State files**: Reads `current.json`
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _sb_status()
- **File**: `app/zapret_manager/features/singbox_menu.py`
- **What it does**: Sing-box status display
- **State files**: Reads `current.json`
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _sb_import_link()
- **File**: `app/zapret_manager/features/singbox_menu.py`
- **What it does**: Import single node link
- **State files**: Writes `nodes.json`
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _sb_add_subscription()
- **File**: `app/zapret_manager/features/singbox_menu.py`
- **What it does**: Add subscription URL
- **State files**: Writes `subscriptions.json`
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _sb_update_subscriptions()
- **File**: `app/zapret_manager/features/singbox_menu.py`
- **What it does**: Update subscriptions from URLs
- **State files**: Reads/writes `subscriptions.json`, `nodes.json`, `current.json`
- **Runtime/system actions**: Downloads from URLs
- **External processes**: None
- **Safe for normal user**: YES

#### _sb_list_nodes()
- **File**: `app/zapret_manager/features/singbox_menu.py`
- **What it does**: List all nodes
- **State files**: Reads `nodes.json`
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _sb_select_node()
- **File**: `app/zapret_manager/features/singbox_menu.py`
- **What it does**: Select active node
- **State files**: Writes `current.json`
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _sb_preview_config()
- **File**: `app/zapret_manager/features/singbox_menu.py`
- **What it does**: Generate config preview
- **State files**: Reads `current.json`, `nodes.json`
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### _sb_start()
- **File**: `app/zapret_manager/features/singbox_menu.py`
- **What it does**: Start sing-box local proxy
- **State files**: Writes `current.json`, writes `generated_config.json`
- **Runtime/system actions**: Starts sing-box.exe
- **External processes**: sing-box.exe
- **Safe for normal user**: YES

#### _sb_stop()
- **File**: `app/zapret_manager/features/singbox_menu.py`
- **What it does**: Stop sing-box local proxy
- **State files**: Writes `current.json`
- **Runtime/system actions**: Stops sing-box.exe, restores system proxy
- **External processes**: sing-box.exe
- **Safe for normal user**: YES

#### _sb_restart()
- **File**: `app/zapret_manager/features/singbox_menu.py`
- **What it does**: Restart sing-box local proxy
- **State files**: Writes `current.json`
- **Runtime/system actions**: Stops and starts sing-box.exe
- **External processes**: sing-box.exe
- **Safe for normal user**: YES

#### _sb_enable_system_proxy()
- **File**: `app/zapret_manager/features/singbox_menu.py`
- **What it does**: Enable Windows system proxy
- **State files**: Writes `system_proxy_backup.json`
- **Runtime/system actions**: Modifies Windows proxy settings
- **External processes**: None (modifies system)
- **Safe for normal user**: YES (but modifies system)

#### _sb_restore_system_proxy()
- **File**: `app/zapret_manager/features/singbox_menu.py`
- **What it does**: Restore Windows system proxy
- **State files**: Reads `system_proxy_backup.json`
- **Runtime/system actions**: Modifies Windows proxy settings
- **External processes**: None (modifies system)
- **Safe for normal user**: YES (but modifies system)

### Tray Menu Handlers (tray_menu.py)

#### build_tray_menu_spec()
- **File**: `app/zapret_manager/tray/tray_menu.py`
- **What it does**: Builds tray menu spec based on status
- **State files**: Reads `current.json`, `nodes.json`
- **Runtime/system actions**: None
- **External processes**: None
- **Safe for normal user**: YES

#### handle_menu_action()
- **File**: `app/zapret_manager/tray/tray_menu.py`
- **What it does**: Executes tray menu action
- **State files**: Varies by action
- **Runtime/system actions**: Varies by action
- **External processes**: Varies by action
- **Safe for normal user**: YES

---

## 4. Duplicates and Clutter

### Duplicate Actions

1. **"Apply Recommended"** appears in:
   - Strategies menu (R key)
   - Test menu (R key)
   - Tray menu (Основное section)
   - **Recommendation**: Keep in Strategies menu, remove from Test menu, keep in Tray

2. **"Auto-setup «под ключ»"** appears in:
   - Auto Setup menu (item 1)
   - Backup menu (item 3)
   - **Recommendation**: Keep in Auto Setup, remove from Backup

3. **"Под ключ + полная проверка"** appears in:
   - Auto Setup menu (item 2)
   - Backup menu (item 4)
   - **Recommendation**: Keep in Auto Setup, remove from Backup

4. **"Runtime / Blockcheck / Diagnostics"** appears in:
   - System menu (item 1)
   - Diagnostics menu (routes to same)
   - **Recommendation**: Keep in Diagnostics, remove from System

5. **"Upstreams (обновления)"** appears in:
   - System menu (item 2)
   - Updates menu (routes to same)
   - **Recommendation**: Keep in Updates, remove from System

6. **"Generate bug report"** appears in:
   - System menu (S key)
   - Tray menu (Диагностика section)
   - **Recommendation**: Keep in both (convenience)

### Repeated Buttons

1. **"Sync Flowseal"** and **"Sync StressOzz"** appear separately and as "Sync оба"
   - **Recommendation**: Keep all three for convenience

2. **"TCP timestamps: enabled"** and **"TCP timestamps: disabled"** as separate items
   - **Recommendation**: Merge into single toggle

3. **"Start local proxy"** and **"Stop sing-box"** and **"Restart sing-box"** in sing-box menu
   - **Recommendation**: Keep all three (different use cases)

### Buttons with Unclear Names

1. **"Быстрый статус"** (Quick status) - unclear what it does
   - **Recommendation**: Rename to "Автонастройка" or move to Diagnostics

2. **"wssize"** toggle - technical term not understood by users
   - **Recommendation**: Add explanatory hint or rename

3. **"blockcheck"** and **"blockcheck2"** - unclear difference
   - **Recommendation**: Add explanatory hints or merge

4. **"QUIC block"** - technical term
   - **Recommendation**: Add explanatory hint

5. **"TCP timestamps"** - technical term
   - **Recommendation**: Add explanatory hint

### Buttons Exposing Internals Unnecessarily

1. **"Engine mode: Auto/winws/winws2"** - exposes internal engine selection
   - **Recommendation**: Move to Advanced/Settings

2. **"Runtime diagnostics"** - exposes internal runtime details
   - **Recommendation**: Keep in Diagnostics (appropriate location)

3. **"System information"** - exposes internal system details
   - **Recommendation**: Keep in Diagnostics (appropriate location)

4. **"Generate diagnostics artifacts"** - exposes internal diagnostics
   - **Recommendation**: Keep in Diagnostics (appropriate location)

### Buttons That Should Be Moved to Diagnostics

1. **"Быстрый статус"** (Quick status) - currently in main menu
   - **Recommendation**: Move to Diagnostics or rename to "Автонастройка"

2. **"Системная информация"** (System info) - currently in System menu
   - **Recommendation**: Keep in Diagnostics (already appropriate)

3. **"Runtime diagnostics"** - currently in System menu
   - **Recommendation**: Keep in Diagnostics (already appropriate)

### Buttons That Should Be Moved to Advanced

1. **"Engine mode: Auto/winws/winws2"** - currently in Tray settings
   - **Recommendation**: Move to Advanced/Settings

2. **"blockcheck"** and **"blockcheck2"** - currently in Runtime menu
   - **Recommendation**: Move to Advanced (technical diagnostics)

3. **"Toggle Diagnostics (в config.yaml)"** - currently in Runtime menu
   - **Recommendation**: Move to Advanced/Settings

### Buttons That Should Be Hidden Unless Debug Mode

1. **"blockcheck2"** - appears to be a technical variant
   - **Recommendation**: Hide or add explanatory hint

2. **"Toggle Diagnostics"** - technical config toggle
   - **Recommendation**: Keep in Advanced/Settings

---

## 5. Broken Routing

### Menu Items Pointing to Missing Handlers

1. **"Запустить blockcheck2"** in _runtime_menu()
   - **Handler**: Missing (not implemented)
   - **Status**: BROKEN
   - **Action**: Remove or implement

### Handlers That Cannot Be Imported

None found - all imports are successful.

### Handlers That Crash on Import

None found - all imports are successful.

### Handlers That Are Stubs/Placeholders

1. **logs_menu()** in menus.py
   - **Status**: PLACEHOLDER
   - **Message**: "Пока не реализовано в этой версии. Записано в лог."
   - **Action**: Implement or remove

2. **advanced_menu()** in menus.py
   - **Status**: PLACEHOLDER
   - **Message**: "Пока не реализовано в этой версии. Записано в лог."
   - **Action**: Implement or remove

### Handlers That Do Not Update State Correctly

None found - all handlers that should update state do so correctly.

---

## 6. Keep Map

| Old menu item | New location proposal |
|-------------|----------------------|
| Main → Старт / Стоп | KEEP (Start / Stop) |
| Main → Быстрый статус | MOVE to Diagnostics as "Автонастройка" |
| Main → Стратегии | KEEP (Strategies) |
| Main → Тест стратегий | KEEP (Test) |
| Main → Ноды / sing-box | KEEP (Nodes / VPN) |
| Main → DNS / hosts / системные настройки | MOVE to Settings (DNS / Hosts) |
| Main → Диагностика и ремонт | KEEP (Diagnostics) |
| Main → Логи и bug report | KEEP (Logs) - needs implementation |
| Main → Обновления | KEEP (Updates) |
| Main → Настройки | KEEP (Settings) |
| Main → Advanced / Dev tools | KEEP (Advanced) - needs implementation |
| Auto Setup → Быстрая автонастройка | KEEP in Diagnostics (Auto Setup) |
| Auto Setup → Под ключ + полная проверка | KEEP in Diagnostics (Auto Setup) |
| Auto Setup → Просмотр проблемных доменов | MOVE to Test (Problem Domains) |
| Auto Setup → Очистить проблемные домены | MOVE to Test (Problem Domains) |
| Strategies → Выбрать Recommended | KEEP (Strategies) |
| Strategies → Выбрать стратегию v1-v9 | KEEP (Strategies) |
| Strategies → Выбрать стратегию Flowseal | KEEP (Strategies) |
| Strategies → Выбрать стратегию YouTube | KEEP (Strategies) |
| Strategies → Выбрать стратегию игр | KEEP (Strategies) |
| Strategies → Включить / Выключить РКН | KEEP (Strategies) |
| Strategies → Обновить список исключений | KEEP (Strategies) |
| Strategies → Добавить / Удалить wssize | KEEP (Strategies) |
| Strategies → Проверить конфликты | KEEP (Strategies) |
| Test → Тест всех стратегий | KEEP (Test) |
| Test → Тест текущей стратегии | KEEP (Test) |
| Test → Control test | KEEP (Test) |
| Test → Тест проблемных доменов | KEEP (Test) |
| Test → Proof-of-effect test | KEEP (Test) |
| Test → Тестировать v | KEEP (Test - Advanced) |
| Test → Тестировать Flowseal | KEEP (Test - Advanced) |
| Test → Тестировать v+Flowseal | KEEP (Test - Advanced) |
| Test → Тестировать по домену | KEEP (Test - Advanced) |
| Test → YouTube auto-test | KEEP (Test - Advanced) |
| Test → Последний рейтинг | KEEP (Test) |
| Test → Применить Recommended | REMOVE (duplicate) |
| Test → Сохранить TOP-5 | KEEP (Test) |
| Test → Результаты | KEEP (Test) |
| Test → Удалить результаты | KEEP (Test) |
| Test → Выбрать набор доменов | KEEP (Test - Settings) |
| Test → Настройки скорости | KEEP (Test - Settings) |
| Test → Подробный / компактный вывод | KEEP (Test - Settings) |
| Sing-box → All items | KEEP (Nodes / VPN) |
| Hosts → All items | MOVE to Settings (DNS / Hosts) |
| Runtime → Показать runtime diagnostics | KEEP (Diagnostics) |
| Runtime → Запустить blockcheck | MOVE to Advanced (Diagnostics) |
| Runtime → Repair runtime assets | KEEP (Diagnostics) |
| Runtime → Запустить blockcheck2 | REMOVE (broken) |
| Runtime → Toggle Diagnostics | MOVE to Advanced (Settings) |
| Upstreams → All items | KEEP (Updates) |
| App Update → All items | KEEP (Updates) |
| Network → All items | MOVE to Settings (Network) |
| Backup → Бэкап (zip) | KEEP (Settings - Backup) |
| Backup → Восстановить из бэкапа | KEEP (Settings - Backup) |
| Backup → Автонастройка «под ключ» | REMOVE (duplicate) |
| Backup → Под ключ + полная проверка | REMOVE (duplicate) |
| System → Системная информация | KEEP (Diagnostics) |
| System → Generate bug report | KEEP (Diagnostics) |
| System → Generate diagnostics artifacts | KEEP (Diagnostics) |
| Logs → PLACEHOLDER | KEEP (Logs) - needs implementation |
| Advanced → PLACEHOLDER | KEEP (Advanced) - needs implementation |
| Tray → All items | KEEP (Tray) |

---

## Summary

- **Files inspected**: 7
- **Menu files found**: 5 (main_menu.py, menus.py, singbox_menu.py, tray_menu.py, menu_actions.py)
- **Menu items found**: 80+ visible items across all menus
- **Handlers found**: 60+ handler functions
- **Broken handlers**: 2 (logs_menu, advanced_menu - placeholders)
- **Duplicate items**: 6 pairs of duplicates
- **Items with unclear names**: 5
- **Items exposing internals unnecessarily**: 4
- **Items that should be moved to Diagnostics**: 3
- **Items that should be moved to Advanced**: 3
- **Items that should be hidden unless debug mode**: 2
