# MENU REBUILD PLAN

**Project**: DedZapret / ZapretManager for Windows
**Date**: 2025-01-13
**Phase**: 2 - PROPOSE NEW MENU STRUCTURE

---

## Target Top-Level Menu Structure

Based on the audit and the workflow 04_menu_simplification.md, the proposed new main menu structure is:

```
╔═══════════════════════════╗
║ DEDZAPRET (Windows)        ║
╚═══════════════════════════╝

Status summary (runtime, zapret, strategy, layers, DoH, QUIC, problem domains, sing-box)

1) Start / Stop
2) Connection
3) Nodes
4) Strategies
5) Games / Profiles
6) DNS
7) Diagnostics
8) Logs
9) Settings
10) Advanced
```

---

## Section Details

### 1. Start / Stop

**Purpose**: Core zapret control - start/stop the main bypass functionality

**Visible actions**:
- Start zapret with selected strategy
- Stop zapret
- Quick strategy selection (if not selected)

**Hidden/advanced actions**: None

**Required handlers**:
- `start_zapret_interactive()` - already implemented
- `stop_zapret()` - already implemented
- `_ask_strategy_before_start()` - already implemented

**Old menu items migrated**:
- Main → Старт / Стоп (KEEP)
- Strategies → Выбрать Recommended (moved here for quick access)

**Notes**: This is the primary action users need. Keep it simple and fast.

---

### 2. Connection

**Purpose**: VPN/sing-box local proxy control

**Visible actions**:
- Start VPN (sing-box local proxy)
- Stop VPN
- Restart VPN
- Select active node/location
- Update subscriptions

**Hidden/advanced actions**:
- Import single link (move to Advanced)
- Add subscription URL (move to Advanced)
- Generate config preview (move to Advanced)
- Enable/disable system proxy (move to Advanced)

**Required handlers**:
- `singbox_menu()` - already implemented
- `_sb_start()` - already implemented
- `_sb_stop()` - already implemented
- `_sb_restart()` - already implemented
- `_sb_select_node()` - already implemented
- `_sb_update_subscriptions()` - already implemented

**Old menu items migrated**:
- Main → Ноды / sing-box (KEEP)
- Sing-box → Start local proxy (KEEP)
- Sing-box → Stop sing-box (KEEP)
- Sing-box → Restart sing-box (KEEP)
- Sing-box → Select active node (KEEP)
- Sing-box → Update subscriptions (KEEP)
- Sing-box → List nodes (KEEP - for visibility)
- Sing-box → Import single link (MOVE to Advanced)
- Sing-box → Add subscription URL (MOVE to Advanced)
- Sing-box → Generate config preview (MOVE to Advanced)
- Sing-box → Enable system proxy (MOVE to Advanced)
- Sing-box → Restore system proxy (MOVE to Advanced)
- Sing-box → Health check (MOVE to Diagnostics)
- Sing-box → Status (MOVE to Diagnostics)

**Notes**: This section focuses on the VPN functionality. Advanced node management moves to Advanced.

---

### 3. Nodes

**Purpose**: Node management for VPN (sing-box)

**Visible actions**:
- List all nodes
- Select active node
- Import node from link
- Add subscription URL
- Update subscriptions

**Hidden/advanced actions**:
- Generate config preview (move to Advanced)
- System proxy control (move to Advanced)

**Required handlers**:
- `_sb_list_nodes()` - already implemented
- `_sb_select_node()` - already implemented
- `_sb_import_link()` - already implemented
- `_sb_add_subscription()` - already implemented
- `_sb_update_subscriptions()` - already implemented

**Old menu items migrated**:
- Sing-box → List nodes (KEEP)
- Sing-box → Select active node (KEEP)
- Sing-box → Import single link (KEEP)
- Sing-box → Add subscription URL (KEEP)
- Sing-box → Update subscriptions (KEEP)

**Notes**: This is a dedicated section for node management, separate from Connection control.

---

### 4. Strategies

**Purpose**: Strategy selection and configuration for zapret bypass

**Visible actions**:
- Apply Recommended strategy
- Select base strategy (v1-v9)
- Select Flowseal strategy
- Select YouTube layer
- Select Games profile
- Toggle RKN bypass
- Update exclude list
- Toggle wssize
- Check strategy conflicts

**Hidden/advanced actions**: None

**Required handlers**:
- `strategies_menu()` - already implemented
- `apply_recommended_strategy()` - already implemented
- `_set_base()` - already implemented
- `_pick_flowseal_base()` - already implemented
- `_pick_youtube_layer()` - already implemented
- `_games_menu()` - already implemented
- `_toggle_rkn()` - already implemented
- `update_exclude()` - already implemented
- `_strategy_conflicts_menu()` - already implemented

**Old menu items migrated**:
- Main → Стратегии (KEEP)
- Strategies → All items (KEEP)
- Test → Применить Recommended (REMOVE - duplicate)

**Notes**: This is the core strategy configuration. All strategy-related actions stay here.

---

### 5. Games / Profiles

**Purpose**: Game launcher and profile management

**Visible actions**:
- Add game profile
- Remove game profile
- Generate .bat launcher
- Generate .lnk shortcut
- Run game with zapret

**Hidden/advanced actions**: None

**Required handlers**:
- `game_launcher_menu()` - already implemented
- `add_profile()` - already implemented
- `remove_profile()` - already implemented
- `generate_bat()` - already implemented
- `generate_shortcut()` - already implemented
- `run_profile()` - already implemented

**Old menu items migrated**:
- extras_menu → Запуск игры / программы (KEEP)
- Strategies → Выбрать стратегию для игр (MOVE here from Strategies)

**Notes**: This is a dedicated section for game launcher functionality, making it more prominent.

---

### 6. DNS

**Purpose**: DNS and hosts file management

**Visible actions**:
- DNS over HTTPS status
- Select DoH profile
- Configure DoH
- Disable DoH
- Flush DNS cache
- Reset hosts file
- Toggle category blocks (hosts)

**Hidden/advanced actions**: None

**Required handlers**:
- `doh_menu()` - already implemented
- `hosts_menu()` - already implemented
- `flush_dns()` - already implemented
- `reset_hosts_windows()` - already implemented
- `set_block_enabled()` - already implemented

**Old menu items migrated**:
- Main → DNS / hosts / системные настройки (KEEP - renamed to DNS)
- extras_menu → DNS over HTTPS (MOVE here from extras)
- extras_menu → Hosts (MOVE here from extras)
- System → Network (MOVE here - QUIC, TCP timestamps, Flush DNS)

**Notes**: Consolidates all DNS/hosts-related actions. Network settings (QUIC, TCP timestamps) also move here.

---

### 7. Diagnostics

**Purpose**: Diagnostics, repair, and troubleshooting

**Visible actions**:
- Runtime diagnostics
- Repair runtime assets
- System information
- Sing-box health check
- Sing-box status
- Generate bug report
- Generate diagnostics artifacts
- Auto-setup wizard (quick)
- Auto-setup wizard (full)

**Hidden/advanced actions**:
- blockcheck (move to Advanced)
- blockcheck2 (REMOVE - broken)
- Toggle diagnostics in config (move to Advanced)

**Required handlers**:
- `_runtime_menu()` - already implemented
- `runtime_diagnostics_text()` - already implemented
- `repair_runtime_assets()` - already implemented
- `system_info_text()` - already implemented
- `_sb_health_check()` - already implemented
- `_sb_status()` - already implemented
- `_support_generate_bug_report()` - already implemented
- `_support_generate_diagnostics_artifacts()` - already implemented
- `key_setup()` - already implemented
- `key_setup_full_check()` - already implemented

**Old menu items migrated**:
- Main → Диагностика и ремонт (KEEP)
- Main → Быстрый статус (MOVE here - rename to Auto-setup)
- Auto Setup → Быстрая автонастройка (KEEP)
- Auto Setup → Под ключ + полная проверка (KEEP)
- Runtime → Показать runtime diagnostics (KEEP)
- Runtime → Repair runtime assets (KEEP)
- Runtime → Запустить blockcheck (MOVE to Advanced)
- Runtime → Запустить blockcheck2 (REMOVE)
- Runtime → Toggle Diagnostics (MOVE to Advanced)
- System → Системная информация (KEEP)
- System → Generate bug report (KEEP)
- System → Generate diagnostics artifacts (KEEP)
- Sing-box → Health check (MOVE here)
- Sing-box → Status (MOVE here)

**Notes**: This consolidates all diagnostics and repair actions. Advanced technical diagnostics move to Advanced.

---

### 8. Logs

**Purpose**: Log viewing and bug reporting

**Visible actions**:
- View recent logs
- Open logs directory
- Generate bug report
- Generate diagnostics artifacts

**Hidden/advanced actions**: None

**Required handlers**:
- `logs_menu()` - NEEDS IMPLEMENTATION
- `_support_generate_bug_report()` - already implemented
- `_support_generate_diagnostics_artifacts()` - already implemented
- `open_logs_dir()` - already implemented (in commands.py)

**Old menu items migrated**:
- Main → Логи и bug report (KEEP - needs implementation)
- System → Generate bug report (MOVE here - keep in Diagnostics too for convenience)
- System → Generate diagnostics artifacts (MOVE here - keep in Diagnostics too for convenience)

**Notes**: Currently a placeholder. Needs implementation to show log files and provide log viewing capabilities.

---

### 9. Settings

**Purpose**: Application settings and configuration

**Visible actions**:
- Update strategies (sync Flowseal/StressOzz)
- Update exclude + RKN list
- Backup (zip)
- Restore from backup
- Network settings (QUIC, TCP timestamps)
- DNS/Hosts settings (moved from DNS section - keep both or consolidate)
- Engine mode selection (Auto/winws/winws2)
- Toggle diagnostics in config

**Hidden/advanced actions**: None

**Required handlers**:
- `_upstreams_menu()` - already implemented
- `update_exclude()` - already implemented
- `update_rkn()` - already implemented
- `backup()` - already implemented
- `restore()` - already implemented
- `_network_menu()` - already implemented
- `set_engine_mode()` - already implemented
- `_toggle_diagnostics_in_config()` - already implemented

**Old menu items migrated**:
- Main → Настройки (KEEP)
- Main → Обновления (MOVE here - rename to Settings)
- Upstreams → All items (KEEP)
- Network → All items (KEEP)
- Backup → Бэкап (zip) (KEEP)
- Backup → Восстановить из бэкапа (KEEP)
- Backup → Автонастройка «под ключ» (REMOVE - duplicate)
- Backup → Под ключ + полная проверка (REMOVE - duplicate)
- Runtime → Toggle Diagnostics (MOVE here)
- Tray → Runtime engine (MOVE here)

**Notes**: Consolidates all settings-related actions. Updates menu merges into Settings.

---

### 10. Advanced

**Purpose**: Advanced tools and developer options

**Visible actions**:
- blockcheck (advanced diagnostics)
- Import single node link
- Add subscription URL
- Generate config preview
- Enable/disable system proxy
- Restore system proxy
- Test settings (speed, domain sets, output mode)
- Test by domain
- Test specific groups (v/flowseal/all)
- YouTube auto-test
- Toggle diagnostics in config

**Hidden/advanced actions**: None

**Required handlers**:
- `run_blockcheck()` - already implemented
- `_sb_import_link()` - already implemented
- `_sb_add_subscription()` - already implemented
- `_sb_preview_config()` - already implemented
- `_sb_enable_system_proxy()` - already implemented
- `_sb_restore_system_proxy()` - already implemented
- `_speed_settings_menu()` - already implemented
- `_choose_domain_set()` - already implemented
- `_run_test_by_domain()` - already implemented
- `_run_test_group()` - already implemented
- `_youtube_auto_test()` - already implemented
- `_toggle_diagnostics_in_config()` - already implemented

**Old menu items migrated**:
- Main → Advanced / Dev tools (KEEP - needs implementation)
- Runtime → Запустить blockcheck (MOVE here)
- Runtime → Toggle Diagnostics (MOVE here)
- Sing-box → Import single link (MOVE here)
- Sing-box → Add subscription URL (MOVE here)
- Sing-box → Generate config preview (MOVE here)
- Sing-box → Enable system proxy (MOVE here)
- Sing-box → Restore system proxy (MOVE here)
- Test → Настройки скорости (MOVE here)
- Test → Выбрать набор доменов (MOVE here)
- Test → Подробный / компактный вывод (MOVE here)
- Test → Тестировать по домену (MOVE here)
- Test → Тестировать v (MOVE here)
- Test → Тестировать Flowseal (MOVE here)
- Test → Тестировать v+Flowseal (MOVE here)
- Test → YouTube auto-test (MOVE here)

**Notes**: This section consolidates all advanced/technical actions. Currently a placeholder, needs implementation.

---

## Implementation Plan

### Phase 1: Implement Placeholders

**Priority**: HIGH

**Tasks**:
1. Implement `logs_menu()` to show log files and provide log viewing
2. Implement `advanced_menu()` to consolidate advanced actions
3. Remove broken "blockcheck2" handler

**Files to modify**:
- `app/zapret_manager/ui/menus.py` - implement logs_menu(), advanced_menu()

**Acceptance criteria**:
- logs_menu() shows list of log files
- logs_menu() can open log files for viewing
- logs_menu() can open logs directory
- advanced_menu() shows all advanced actions
- blockcheck2 is removed from _runtime_menu()

---

### Phase 2: Restructure Main Menu

**Priority**: HIGH

**Tasks**:
1. Update main_menu.py to use new 10-item structure
2. Update menu item labels to match new structure
3. Update routing to new submenu functions

**Files to modify**:
- `app/zapret_manager/ui/main_menu.py` - update run_main_menu()

**Acceptance criteria**:
- Main menu shows 10 items as specified
- All menu items route to correct handlers
- No functionality is lost

---

### Phase 3: Reorganize Submenus

**Priority**: MEDIUM

**Tasks**:
1. Create new `connection_menu()` for VPN control
2. Create new `nodes_menu()` for node management
3. Create new `games_menu()` for game launcher (rename from game_launcher_menu)
4. Create new `dns_menu()` consolidating DNS/hosts/network
5. Update `diagnostics_menu()` to include all diagnostics actions
6. Update `settings_menu()` to include all settings actions
7. Update `advanced_menu()` to include all advanced actions
8. Remove duplicate actions from old locations

**Files to modify**:
- `app/zapret_manager/ui/menus.py` - create new menu functions, reorganize existing

**Acceptance criteria**:
- All actions are accessible from new locations
- No duplicate actions remain
- Old menu functions are removed or deprecated

---

### Phase 4: Update Tray Menu

**Priority**: LOW

**Tasks**:
1. Update tray menu to match new structure
2. Ensure tray menu calls correct handlers
3. Add missing tray actions if needed

**Files to modify**:
- `app/zapret_manager/tray/tray_menu.py` - update build_tray_menu_spec()

**Acceptance criteria**:
- Tray menu structure matches new main menu
- All tray actions work correctly

---

### Phase 5: Add Explanatory Hints

**Priority**: LOW

**Tasks**:
1. Add explanatory hints for technical terms (QUIC, TCP timestamps, wssize, blockcheck)
2. Add hints for complex actions (proof-of-effect, control test)
3. Ensure hints are concise and user-friendly

**Files to modify**:
- `app/zapret_manager/ui/menus.py` - add hints to menu items

**Acceptance criteria**:
- All technical terms have explanatory hints
- Hints are shown in menu
- Hints are in Russian

---

### Phase 6: Update Tests

**Priority**: MEDIUM

**Tasks**:
1. Update existing menu tests to match new structure
2. Add tests for new menu functions
3. Add tests for logs_menu() and advanced_menu()

**Files to modify**:
- `tests/test_main_menu_unittest.py` - update tests
- `tests/test_menu_dependencies_unittest.py` - update tests

**Acceptance criteria**:
- All menu tests pass
- New menu functions are tested
- No regressions in menu functionality

---

### Phase 7: Update Documentation

**Priority**: LOW

**Tasks**:
1. Update README.md with new menu structure
2. Update workflow documentation
3. Update menu_parity.md

**Files to modify**:
- `README.md` - update menu documentation
- `docs/ai/workflows/04_menu_simplification.md` - mark as completed
- `docs/menu_parity.md` - update with new structure

**Acceptance criteria**:
- Documentation matches new menu structure
- All changes are documented

---

## Migration Summary

### Items to Remove

1. **blockcheck2** - broken handler, not implemented
2. **Duplicate "Apply Recommended"** in Test menu
3. **Duplicate "Auto-setup «под ключ»"** in Backup menu
4. **Duplicate "Под ключ + полная проверка"** in Backup menu

### Items to Move

1. **Быстрый статус** → Diagnostics (rename to Auto-setup)
2. **Просмотр проблемных доменов** → Test (Problem Domains)
3. **Очистить проблемных доменов** → Test (Problem Domains)
4. **DNS / hosts / системные настройки** → Settings (DNS)
5. **Обновления** → Settings (merge)
6. **Runtime / Blockcheck / Diagnostics** → Diagnostics (keep)
7. **blockcheck** → Advanced
8. **Toggle Diagnostics** → Advanced
9. **Engine mode** → Advanced
10. **Import single link** → Advanced
11. **Add subscription URL** → Advanced
12. **Generate config preview** → Advanced
13. **Enable/disable system proxy** → Advanced
14. **Test settings** → Advanced
15. **Test by domain** → Advanced
16. **Test specific groups** → Advanced
17. **YouTube auto-test** → Advanced

### Items to Implement

1. **logs_menu()** - currently a placeholder
2. **advanced_menu()** - currently a placeholder

### Items to Keep in Place

1. **Start / Stop** - core functionality
2. **Strategies** - core functionality
3. **Test strategies** - core functionality
4. **All strategy actions** - core functionality
5. **All sing-box basic actions** - core functionality
6. **All diagnostic actions** - core functionality
7. **All settings actions** - core functionality

---

## Risk Assessment

### Low Risk

- Renaming menu items
- Reorganizing menu structure
- Moving actions between menus
- Adding explanatory hints

### Medium Risk

- Implementing logs_menu() - new functionality
- Implementing advanced_menu() - new functionality
- Updating tests - may reveal bugs

### High Risk

- Removing duplicate actions - ensure no functionality is lost
- Changing menu routing - ensure all actions still work
- Updating tray menu - may affect users who rely on tray

---

## Rollback Plan

If issues arise after implementation:

1. **Revert main_menu.py** to previous version
2. **Revert menus.py** to previous version
3. **Revert tray_menu.py** to previous version
4. **Revert tests** to previous version
5. **Restore documentation** to previous version

All changes are in menu structure only, no business logic is changed, so rollback is safe.

---

## Success Criteria

- [ ] Main menu shows 10 items as specified
- [ ] All actions are accessible from new locations
- [ ] No duplicate actions remain
- [ ] logs_menu() is implemented and working
- [ ] advanced_menu() is implemented and working
- [ ] All tests pass
- [ ] Tray menu matches new structure
- [ ] Documentation is updated
- [ ] No functionality is lost
- [ ] No regressions in menu functionality
