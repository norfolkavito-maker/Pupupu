# Current Console Menu Map

**Generated:** 2025-01-XX  
**Purpose:** Post-change audit documentation of the rebuilt console menu structure  
**Scope:** Main menu and all submenus as implemented in `app/zapret_manager/ui/main_menu.py` and `app/zapret_manager/ui/menus.py`

---

## 1. Main Menu Structure

**File:** `app/zapret_manager/ui/main_menu.py`  
**Function:** `run_main_menu(ctx: AppContext) -> int`

### Status Block (displayed before menu)

The menu displays a status summary before showing the menu options:
- Zapret running status (running/stopped)
- Current strategy
- YouTube layer
- Discord layer
- Game profile
- Sing-box/VPN status

### Main Menu Items (10-item grouped structure)

| # | Label (dynamic) | Handler | Description |
|---|-----------------|---------|-------------|
| 1 | **Запустить / Остановить** (dynamic color) | `start_zapret_interactive` / `stop_zapret` | Lifecycle control - green if stopped, red if running |
| 2 | **Мастер настройки (первичная настройка)** | `wizard_menu` | First-time setup wizard |
| 3 | **Стратегии (выбор base стратегии)** | `base_strategies_menu` | Base strategy selection and configuration |
| 4 | **Тестирование (проверка + blockcheck)** | `testing_menu` | All testing and verification options |
| 5 | **Списки / IPSet / Hostlist** | `lists_menu` | Domain/IP/list management |
| 6 | **Игры / GameFilter** | `games_menu` | Game profiles and filtering |
| 7 | **Discord / YouTube / Telegram** | `services_menu` | Service-specific modes and proxy |
| 8 | **VPN (серверы, подписки, локальный прокси)** | `vpn_menu` | VPN connection management (sing-box) |
| 9 | **Обслуживание / Repair** | `repair_menu` | Maintenance, self-check, backup, repair |
| 0 | **System / Advanced** | `system_advanced_menu` | Rare system-level settings and developer/debug operations |
| Enter | **выход** | return 0 | Exit the application |

### Dynamic Label Behavior

**Item 1 (Start/Stop):**
- If `ctx.state.zapret.running` is True: label = `Остановить` (red)
- If `ctx.state.zapret.running` is False: label = `Запустить` (green)

---

## 2. Submenu Structures

### 2.1 wizard_menu() - Мастер настройки

**File:** `app/zapret_manager/ui/menus.py`  
**Purpose:** First-time setup wizard for new users

| # | Label | Handler | Description |
|---|-------|---------|-------------|
| 1 | Быстрая автонастройка «под ключ» | `auto_setup_menu` | Quick auto-setup |
| 2 | Под ключ + полная проверка/подбор (мастер) | `auto_setup_menu` | Full setup with verification |
| 3 | Проверить runtime файлы | `detect_runtime_files` + `runtime_health` | Runtime file health check |
| 4 | Проверить WinDivert | `detect_runtime_files` + `runtime_health` | WinDivert health check |
| 5 | Выбрать базовую стратегию | `base_strategies_menu` | Strategy selection |
| 6 | Настроить VPN (если нужно) | `vpn_menu` | VPN configuration |
| 7 | Запустить быстрый тест | `test_strategy` | Quick strategy test |

---

### 2.2 base_strategies_menu() - Стратегии (base)

**File:** `app/zapret_manager/ui/menus.py`  
**Purpose:** Base/main zapret/winws strategies only

| # | Label | Handler | Description |
|---|-------|---------|-------------|
| R | Выбрать Recommended | `apply_recommended_strategy` | Apply recommended strategy |
| 1 | Выбрать и установить стратегию v1-v9 | `_set_base` | Select v-series strategy |
| 2 | Выбрать и установить стратегию от Flowseal | `_pick_flowseal_base` | Select Flowseal strategy |
| 3 | Показать текущую стратегию (dry-run) | `_load_selected_strategy` + `resolve_strategy_command` | Show current strategy preview |
| 4 | Сбросить на recommended/default | `apply_recommended_strategy` | Reset to recommended |
| 5 | Включить / Выключить обход по спискам РКН | `_toggle_rkn` | Toggle RKN bypass |
| 6 | Обновить список исключений | `update_exclude` | Update exclude list |
| 7 | Добавить / Удалить блок с --wssize 1:6 | state toggle + `_restart_if_running` | Toggle wssize block |
| C | Проверить конфликты текущих слоёв | `_strategy_conflicts_menu` | Check strategy conflicts |

**Status Display:**
- Shows current strategy name (or "не выбрана" if none)

---

### 2.3 testing_menu() - Тестирование

**File:** `app/zapret_manager/ui/menus.py`  
**Purpose:** All checks and tests including blockcheck

| # | Label | Handler | Description |
|---|-------|---------|-------------|
| 1 | Супер-быстрый тест | `test_strategy` (mode=quick) | Quick test of current strategy |
| 2 | Полный тест всех стратегий | `_test_all_strategies_menu` | Sweep test all strategies |
| 3 | Тест текущей стратегии | `_run_test_current` | Test selected strategy |
| 4 | Control test (без zapret) | `_run_control_test` | Baseline control test |
| 5 | Blockcheck (диагностика) | `run_blockcheck` (variant=1) | Extended blockcheck diagnostics |
| 6 | Тест VPN | `_sb_health_check` | VPN health check |
| 7 | Тест DNS | socket DNS check | DNS resolution test |
| 8 | Тест Discord/YouTube/Telegram | `services_menu` | Service-specific tests |
| 9 | Тест GameFilter/профиля игр | `games_menu` | Game profile test |
| L | Последний рейтинг/отчёт | `_show_latest_ranking` | Show latest strategy ranking |

---

### 2.4 lists_menu() - Списки / IPSet / Hostlist

**File:** `app/zapret_manager/ui/menus.py`  
**Purpose:** Domain/IP/list management

| # | Label | Handler | Description |
|---|-------|---------|-------------|
| 1 | Обновить списки | `update_exclude` + `update_rkn` | Update all lists |
| 2 | Проверить списки | (status check) | Verify lists exist |
| 3 | Починить отсутствующие списки | `repair_runtime_assets` | Repair missing lists |
| 4 | Показать пути к спискам | (display paths) | Show list file paths |
| 5 | Режим списков (off/any/selected/custom) | (placeholder) | List mode selection |
| 6 | Hosts (блокировка категорий) | `hosts_menu` | Hosts file management |

**Status Display:**
- Hostlist: OK
- IPSet: OK
- Exclude list: OK

---

### 2.5 games_menu() - Игры / GameFilter

**File:** `app/zapret_manager/ui/menus.py`  
**Purpose:** Game profiles and filtering

| # | Label | Handler | Description |
|---|-------|---------|-------------|
| 1 | Режим GameFilter (off/any/selected/custom) | (placeholder) | GameFilter mode selection |
| 2 | Выбрать профиль игры | `_games_menu` | Select game profile |
| 3 | Тест текущего профиля | `test_strategy` | Test current game profile |
| 4 | Сбросить профиль | state toggle + `_restart_if_running` | Reset game profile |
| 5 | Запуск игры / программы | `game_launcher_menu` | Game launcher |

**Status Display:**
- Shows current game profile (or "не выбран" if none)

---

### 2.6 services_menu() - Discord / YouTube / Telegram

**File:** `app/zapret_manager/ui/menus.py`  
**Purpose:** Service-specific modes and proxy

| # | Label | Handler | Description |
|---|-------|---------|-------------|
| 1 | Discord настройки | `discord_menu` | Discord-specific settings |
| 2 | YouTube настройки | `_pick_youtube_layer` | YouTube layer selection |
| 3 | Telegram / proxy настройки | `tg_menu` | Telegram proxy settings |
| 4 | QUIC режим | `quic_rule_exists` + `quic_block_enable/disable` | QUIC block toggle |
| 5 | Проверка правил сервиса | (status check) | Verify service rules |

**Status Display:**
- YouTube: current layer or "off"
- Discord: current layer or "off"

---

### 2.7 vpn_menu() - VPN (серверы, подписки, локальный прокси)

**File:** `app/zapret_manager/ui/menus.py`  
**Purpose:** VPN connection management (sing-box)

| # | Label | Handler | Description |
|---|-------|---------|-------------|
| 1 | Запустить VPN | `_sb_start` | Start sing-box VPN |
| 2 | Остановить VPN | `_sb_stop` | Stop sing-box VPN |
| 3 | Перезапустить VPN | `_sb_restart` | Restart sing-box VPN |
| 4 | Выбрать сервер/локацию | `_sb_select_node` | Select active VPN node |
| 5 | Импортировать ссылку на сервер | `_sb_import_link` | Import single node link |
| 6 | Добавить подписку | `_sb_add_subscription` | Add subscription URL |
| 7 | Обновить подписки | `_sb_update_subscriptions` | Update subscriptions from URLs |
| 8 | Показать список серверов | `_sb_list_nodes` | List all available nodes |
| 9 | Тест VPN | `_sb_health_check` | VPN health check |

**Status Display:**
- VPN status: running (pid=X) or stopped
- Active server: node name or "не выбран"

**Note:** Uses user-facing terminology "VPN" instead of internal "sing-box" terminology.

---

### 2.8 repair_menu() - Обслуживание / Repair

**File:** `app/zapret_manager/ui/menus.py`  
**Purpose:** Maintenance, self-check, backup, repair

| # | Label | Handler | Description |
|---|-------|---------|-------------|
| 1 | Обновить стратегии (sync Flowseal/StressOzz) | `_upstreams_menu` | Sync strategy upstreams |
| 2 | Создать бэкап (zip) | `backup` | Create backup archive |
| 3 | Восстановить из бэкапа (zip) | `restore` | Restore from backup |
| 4 | Проверить целостность репозитория | (status check) | Verify repository integrity |
| 5 | Проверить требуемые файлы/активы | `repair_runtime_assets` | Check required assets |
| 6 | Проверить runtime файлы | `detect_runtime_files` + `runtime_health` | Runtime file health check |
| 7 | Проверить структуру DedZapretData | (status check) | Verify data directory structure |
| 8 | Восстановить базовое состояние | (placeholder with confirmation) | Reset to default state |
| 9 | Очистить временные файлы/кэш | (placeholder) | Clear temporary files |

---

### 2.9 system_advanced_menu() - System / Advanced

**File:** `app/zapret_manager/ui/menus.py`  
**Purpose:** Rare system-level settings and developer/debug operations

| # | Label | Handler | Description |
|---|-------|---------|-------------|
| 1 | Автозапуск | (Future / Planned) | Autostart configuration |
| 2 | Запуск через ярлык игры | `game_launcher_menu` | Game launcher shortcut |
| 3 | Режим отслеживания процесса игры | (Future / Planned) | Game process tracking mode |
| 4 | Пути portable данных | (display paths) | Show portable data paths |
| 5 | Системная / окружение информация | `system_info_text` | System information display |
| 6 | Raw runtime/service controls | `_runtime_menu` | Direct runtime controls |
| 7 | Developer/debug checks | `advanced_menu` | Advanced developer tools |
| 8 | Опасные очистка/сброс с подтверждением | (placeholder with safety) | Dangerous operations with confirmation |
| 9 | Advanced menu (blockcheck, test settings, etc.) | `advanced_menu` | Advanced tools submenu |

---

### 2.10 advanced_menu() - Advanced / Dev tools

**File:** `app/zapret_manager/ui/menus.py`  
**Purpose:** Blockcheck, test settings, system proxy, config toggles

| # | Label | Handler | Description |
|---|-------|---------|-------------|
| 1 | Blockcheck (расширенная диагностика) | `run_blockcheck` (variant=1) | Extended blockcheck diagnostics |
| 2 | Настройки скорости теста | `_speed_settings_menu` | Test speed settings |
| 3 | Выбор набора доменов для тестов | `_choose_domain_set` | Select test domain set |
| 4 | Подробный / компактный вывод тестов | state toggle | Toggle detailed console output |
| 5 | Тест по конкретному домену | `_run_test_by_domain` | Test specific domains |
| 6 | Тест группы стратегий (v/flowseal/all) | `_run_test_group` | Test strategy groups |
| 7 | YouTube auto-test | `_youtube_auto_test` | YouTube layer auto-test |
| 8 | Toggle Diagnostics (в config.yaml) | `_toggle_diagnostics_in_config` | Toggle diagnostics in config |
| 9 | Engine mode (Auto/winws/winws2) | `set_engine_mode` | Set engine mode |
| A | System proxy: enable (sing-box) | `_sb_enable_system_proxy` | Enable Windows system proxy |
| B | System proxy: restore | `_sb_restore_system_proxy` | Restore Windows system proxy |

---

### 2.11 logs_menu() - Логи и bug report

**File:** `app/zapret_manager/ui/menus.py`  
**Purpose:** View logs and generate reports

| # | Label | Handler | Description |
|---|-------|---------|-------------|
| 1 | Просмотреть лог-файл | (file read) | View log file content (last 100 lines) |
| 2 | Открыть папку с логами | subprocess (explorer/open/xdg-open) | Open logs directory in file manager |
| 3 | Создать bug report (zip с маскировкой секретов) | `_support_generate_bug_report` | Generate bug report with secret masking |
| 4 | Сформировать диагностические артефакты | `_support_generate_diagnostics_artifacts` | Generate diagnostic artifacts |

**Status Display:**
- Lists last 10 log files with size and modification time

---

## 3. Legacy Menus (Routed Through New Structure)

The following legacy menus still exist and are routed through the new structure:

### 3.1 _runtime_menu() - Runtime / Blockcheck / Diagnostics

**File:** `app/zapret_manager/ui/menus.py`  
**Accessed via:** `diagnostics_menu()` (item 9) and `system_advanced_menu()` (item 6)

**Changes:**
- **Removed:** "Запустить blockcheck2" (was broken, no handler)

**Remaining items:**
- Показать runtime diagnostics
- Запустить blockcheck
- Repair runtime assets
- Toggle Diagnostics

---

### 3.2 _upstreams_menu() - Upstreams (обновления)

**File:** `app/zapret_manager/ui/menus.py`  
**Accessed via:** `updates_menu()` (item 9) and `repair_menu()` (item 1)

**Items:**
- Sync Flowseal
- Sync StressOzz
- Sync оба

---

### 3.3 system_menu() - System Settings

**File:** `app/zapret_manager/ui/menus.py`  
**Accessed via:** `settings_menu()` (routes to system_menu)

**Items:**
- Runtime / Blockcheck / Diagnostics (now routes to diagnostics_menu)
- Upstreams (обновления) (now routes to updates_menu)
- Network
- Backup
- System information
- Generate bug report
- Generate diagnostics artifacts

---

## 4. Menu Routing Summary

### Main Menu → Submenu Mapping

```
run_main_menu()
├── 1) Start/Stop → start_zapret_interactive() / stop_zapret()
├── 2) Мастер настройки → wizard_menu()
├── 3) Стратегии → base_strategies_menu()
├── 4) Тестирование → testing_menu()
├── 5) Списки / IPSet / Hostlist → lists_menu()
├── 6) Игры / GameFilter → games_menu()
├── 7) Discord / YouTube / Telegram → services_menu()
├── 8) VPN → vpn_menu()
├── 9) Обслуживание / Repair → repair_menu()
├── 0) System / Advanced → system_advanced_menu()
└── Enter) exit → return 0
```

### Submenu → Legacy Menu Mapping

```
wizard_menu()
├── 1,2) → auto_setup_menu()
├── 5) → base_strategies_menu()
├── 6) → vpn_menu()
└── 7) → test_strategy()

base_strategies_menu()
├── 1) → _set_base()
├── 2) → _pick_flowseal_base()
└── 5) → _toggle_rkn()

testing_menu()
├── 8) → services_menu()
├── 9) → games_menu()
└── 5) → run_blockcheck()

lists_menu()
└── 6) → hosts_menu()

games_menu()
└── 2) → _games_menu()
└── 5) → game_launcher_menu()

services_menu()
├── 1) → discord_menu()
├── 2) → _pick_youtube_layer()
└── 3) → tg_menu()

vpn_menu()
└── All items → singbox_menu helpers (_sb_*)
    └── from app.zapret_manager.features.singbox_menu

repair_menu()
├── 1) → _upstreams_menu()
├── 2) → backup()
├── 3) → restore()
└── 5) → repair_runtime_assets()

system_advanced_menu()
├── 2) → game_launcher_menu()
├── 5) → system_info_text()
├── 6) → _runtime_menu()
└── 7,9) → advanced_menu()

advanced_menu()
├── 1) → run_blockcheck()
├── 2) → _speed_settings_menu()
├── 3) → _choose_domain_set()
├── 5) → _run_test_by_domain()
├── 6) → _run_test_group()
├── 7) → _youtube_auto_test()
├── 8) → _toggle_diagnostics_in_config()
├── 9) → set_engine_mode()
└── A,B) → singbox_menu helpers (_sb_enable_system_proxy, _sb_restore_system_proxy)

logs_menu()
├── 3) → _support_generate_bug_report()
└── 4) → _support_generate_diagnostics_artifacts()

diagnostics_menu() → _runtime_menu()
updates_menu() → _upstreams_menu()
settings_menu() → system_menu()
```

---

## 5. Key Design Decisions

### 5.1 User-Facing Terminology

**VPN vs sing-box:**
- Main menu item 8 uses "VPN (серверы, подписки, локальный прокси)"
- Submenu title uses "VPN (серверы, подписки, локальный прокси)"
- Internal implementation uses sing-box functions from `app.zapret_manager.features.singbox_menu`
- No exposure of "sing-box" or "nodes" terminology in main menu labels

### 5.2 Dynamic Lifecycle Label

**Item 1 (Start/Stop):**
- Label changes based on `ctx.state.zapret.running`
- Color changes: green for "Запустить", red for "Остановить"
- Hint text: "(lifecycle)" to indicate this is a lifecycle control

### 5.3 Grouped Structure

The new menu groups related functionality:
- **Lifecycle:** Item 1 (Start/Stop)
- **Setup:** Item 2 (Wizard)
- **Core:** Items 3-4 (Strategies, Testing)
- **Lists/Games/Services:** Items 5-7
- **VPN:** Item 8
- **Maintenance:** Item 9 (Repair)
- **Advanced:** Item 0 (System/Advanced)

### 5.4 Status-First UI

- Status block displayed before menu options
- Each submenu shows relevant status information
- Current strategy, VPN status, service modes displayed prominently

---

## 6. Removed Items

### 6.1 Broken Handler Removed

**Item:** "Запустить blockcheck2" in `_runtime_menu()`
- **Reason:** No handler implementation (broken routing)
- **Action:** Removed from menu options
- **Documented in:** MENU_AUDIT.md and MENU_IMPLEMENTATION_REPORT.md

---

## 7. Future / Planned Items

The following items are marked as "Future / Planned" in the implementation:

1. **system_advanced_menu() item 1:** Автозапуск
2. **system_advanced_menu() item 3:** Режим отслеживания процесса игры
3. **lists_menu() item 5:** Режим списков (off/any/selected/custom) - placeholder
4. **games_menu() item 1:** Режим GameFilter (off/any/selected/custom) - placeholder
5. **repair_menu() item 8:** Восстановить базового состояния - placeholder with confirmation
6. **repair_menu() item 9:** Очистить временные файлы/кэш - placeholder

---

## 8. Import Dependencies

### Main Module Imports

**File:** `app/zapret_manager/ui/main_menu.py`
```python
from app.zapret_manager.ui.menus import (
    wizard_menu,
    base_strategies_menu,
    testing_menu,
    lists_menu,
    games_menu,
    services_menu,
    vpn_menu,
    repair_menu,
    system_advanced_menu,
)
```

### Submenu Module Imports

**File:** `app/zapret_manager/ui/menus.py`
- Core commands: `from app.zapret_manager.core.commands import ...`
- Strategy test: `from app.zapret_manager.features.strategy_test import ...`
- Blockcheck: `from app.zapret_manager.features.blockcheck import ...`
- Sing-box: `from app.zapret_manager.features.singbox_menu import ...`
- Lists: `from app.zapret_manager.features.lists import ...`
- Runtime assets: `from app.zapret_manager.features.runtime_assets import ...`
- System: `from app.zapret_manager.features.system import ...`
- Sysinfo: `from app.zapret_manager.features.sysinfo import ...`
- Problem domains: `from app.zapret_manager.features.problem_domains import ...`

---

## 9. Test Coverage

**File:** `tests/test_main_menu_unittest.py`

**Tests:**
1. `test_status_summary_shows_key_fields` - Verifies status block fields
2. `test_main_menu_shows_grouped_structure` - Verifies new 10-item menu structure
3. `test_menu_routing_maps_to_correct_handlers` - Verifies routing to new submenu functions

---

## Summary

- **Main menu items:** 10 (plus dynamic Start/Stop)
- **Submenus:** 11 new structured submenus
- **Legacy menus:** 3 (routed through new structure)
- **Removed items:** 1 (blockcheck2 - broken handler)
- **Future/Planned items:** 6
- **User-facing VPN terminology:** Yes (no internal "sing-box" in main menu)
- **Dynamic lifecycle label:** Yes (Start/Stop with color)
- **Status-first UI:** Yes (status block before menu)
- **Grouped structure:** Yes (related functionality grouped)
