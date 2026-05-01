---
title: Project map after P1 (architecture snapshot)
scope: docs/audit
generated_at: 2026-05-01
note: "Facts are anchored to concrete files/functions. Unknowns are marked as UNKNOWN." 
---

# Project map after P1

Этот документ фиксирует текущее состояние архитектуры DedZapret (zapret_manager) **после P0/P1 фиксов** на момент `git commit 6ed438c` (см. `app/zapret_manager/__main__.py::_run_ci_smoke()` печатает версию/commit при CI).

Правила (самопроверка):
- каждое утверждение привязано к **конкретному файлу/функции**;
- если поведение неочевидно из кода — помечено **UNKNOWN**;
- документ не предполагает, что все тесты green: ниже явно отмечено, что `unittest discover` в текущем окружении показывает ошибки (см. раздел *Known technical debt*).

---

## 1. Executive summary

Система сейчас состоит из 3 крупных контуров:

1) **Zapret/winws runtime** (основной бекенд обхода DPI)
- запуск/остановка, сбор команды, preflight-валидация ассетов и автодобавление `--wf-*` фильтров;
- ядро: `app/zapret_manager/features/zapret_runtime.py`.

2) **sing-box local proxy (experimental)**
- хранение нод/подписок, генерация minimal конфигов, запуск/стоп detached процесса и (опционально) включение *system proxy* через registry;
- ядро: `app/zapret_manager/features/singbox_menu.py`, `app/zapret_manager/core/singbox/*`, `app/zapret_manager/core/process_supervisor.py`.

3) **Diagnostics / bug-report / artifacts**
- opt-in запись сессии (jsonl) + сбор masked zip-отчёта;
- best-effort summary artifacts в `DedZapretData/data/diagnostics`;
- ядро: `app/zapret_manager/core/diagnostics.py`, `app/zapret_manager/core/report.py`, `app/zapret_manager/features/diagnostics_artifacts.py`.

Ключевая идея хранения данных: **portable layout** → всё mutable хранится под `DedZapretData/` (см. `app/zapret_manager/core/paths.py::Paths.from_root`).

---

## 2. Current entrypoints

### Python entrypoint

- `app/zapret_manager/__main__.py`
  - CI smoke: `--ci-smoke` → `_run_ci_smoke()` (не требует админа/меню).
    - проверяет `AppContext.bootstrap()` (см. `app/zapret_manager/core/app_context.py::AppContext.bootstrap`)
    - проверяет runtime health: `app/zapret_manager/features/zapret_runtime.py::runtime_health`
    - проверяет sing-box binary: `app/zapret_manager/core/singbox/binary.py::detect_singbox_binary` (файл не читался в рамках этого аудита → детали UNKNOWN).
  - normal run:
    - ранняя настройка логов → `app/zapret_manager/core/log.py::setup_logging` (файл не читался → UNKNOWN)
    - admin gate: `app/zapret_manager/utils/platform.py::ensure_admin_or_relaunch`
    - UI: `app/zapret_manager/main.py::main()`.

### Main()

- `app/zapret_manager/main.py::main()`
  - создаёт `AppContext.bootstrap(argv)`
  - запускает текстовое меню: `app/zapret_manager/ui/main_menu.py::run_main_menu(ctx)`
  - в `finally` закрывает diagnostics session (`ctx.diagnostics.close(...)`) и **опционально** предлагает сформировать report и открыть GitHub Issues (`ctx.diagnostics.bundle_report_zip(...)`, `github_issue_url(...)`).

### Windows запуск / elevation

- `run.bat` присутствует (контент не анализировался → UNKNOWN).
- Elevation внутри Python:
  - `app/zapret_manager/utils/platform.py::ensure_admin_or_relaunch` + `relaunch_self_as_admin`.
  - В dev-режиме (не frozen) `relaunch_self_as_admin()` возвращает `False` (см. комментарий в `utils/platform.py`, строки 48–53) → **ожидается**, что elevation делается через bat.

---

## 3. Current menu structure

### Главный экран

- `app/zapret_manager/ui/main_menu.py::run_main_menu`
  - статус-строки: `_status_lines(ctx)`
    - runtime core: `runtime_health(ctx)`
    - zapret running pid + selected/base strategy из `ctx.state.zapret` (см. `app/zapret_manager/core/state.py::ZapretRunState`)
    - layers: youtube/discord_script/games_profile/rkn/wssize → поля `ctx.state.zapret.*`
    - DoH indicator: `ctx.state.doh.enabled/profile` (см. `state.py::DoHRunState`)
    - QUIC firewall indicator: `features/system.py::quic_rule_exists` (функция импортирована, но реализация не читалась → UNKNOWN)
    - sing-box indicator: читает `DedZapretData/data/state/current.json` через `core/current_state.py::load_current_state`.

  - пункты меню:
    1) Start/Stop Zapret → `start_zapret_interactive` / `stop_zapret`
    2) Auto setup wizard → `ui/menus.py::auto_setup_menu`
    3) Strategies → `ui/menus.py::strategies_menu`
    4) Tests and auto-pick → `ui/menus.py::test_menu`
    5) Extra modes → `ui/menus.py::extras_menu`
    6) Service/system → `ui/menus.py::service_menu` (проксирует в `system_menu`)
    7) sing-box menu → `features/singbox_menu.py::singbox_menu`

### Меню “Strategies”

- `app/zapret_manager/ui/menus.py::strategies_menu`
  - Base стратегии v1..v9: `_set_base(ctx, "vN")`.
  - Flowseal стратегии: `_pick_flowseal_base`.
  - YouTube pack (YvNN): `_pick_youtube_layer`.
  - Games профили: `_games_menu` переключает `ctx.state.zapret.games_profile` (Gv1..Gv4).
  - RKN toggle: `_toggle_rkn`.
  - `--wssize 1:6` toggle: `ctx.state.zapret.wssize_enabled = not ...`.

### Меню “Extras”

- `ui/menus.py::extras_menu`
  - Discord: `discord_menu(ctx)`
  - TG WS Proxy: `tg_menu(ctx)` (функция не читалась → UNKNOWN)
  - DoH: `doh_menu(ctx)` (функция не читалась → UNKNOWN)
  - Hosts: `hosts_menu(ctx)`
  - Game launcher: `game_launcher_menu(ctx)` (функция не читалась → UNKNOWN)

### Меню “Tests”

- `ui/menus.py::test_menu`
  - `0` baseline control test (без zapret): `_run_control_test`
  - `1-4` test группы или текущую стратегию
  - `5` test by domain
  - `6` YouTube auto-test
  - `7` выбрать доменный набор
  - `8` Proof-of-effect
  - `9` Problem domains menu
  - `T` test all strategies with progress + ranking

### Меню “System/Service”

- `ui/menus.py::service_menu` → вызывает `system_menu(ctx)`.
- `ui/menus.py::system_menu` (частично виден через `search_files`, структура полностью не снималась → UNKNOWN), но подтверждены пункты поддержки:
  - `S) Support: Generate bug report` → `_support_generate_bug_report`
  - `X) Support: Сформировать диагностические артефакты` → `_support_generate_diagnostics_artifacts`.

---

## 4. Runtime/process flow

### 4.1 winws (zapret)

**Базовый flow**:

1) UI вызывает `start_zapret_interactive(ctx, strategy)`
   - объявлен в `app/zapret_manager/features/zapret_runtime.py` (реализация не читалась в этой сессии полностью → частично UNKNOWN).

2) Команда строится через `features/zapret_runtime.py::build_command(ctx, strategy, ...)`:
   - берёт `winws.exe` или `winws2.exe` из `ctx.state.runtime.winws_path/winws2_path` либо ищет через `_find_first`.
   - берёт аргументы стратегии, применяет games overlay через `strategies/overlays.py::apply_overlays`.
   - нормализует args: `normalize_winws_args(args)` (функция не читалась → UNKNOWN).
   - резолвит плейсхолдеры/пути: `resolve_winws_args(ctx, exe_dir=exe.parent, args=args)`.
   - выполняет preflight wf inference: `_infer_wf_args_from_filters(resolved)` (не читалось → UNKNOWN), результат `wf_args` вставляется **в начало argv**.

3) `resolve_winws_args` выполняет подстановки:
   - `{BIN}` → `exe_dir`
   - `{FAKE}` → `runtime/zapret/files/fake` (через `_runtime_fake_dir(ctx)`)
   - `{LISTS}`/`{MGR_LISTS}` → `DedZapretData/data/lists` (через `_manager_lists_dir(ctx)`)
   - `{RT_LISTS}` → runtime lists (через `_rt_lists_dir(ctx)`)
   - `{FLOWSEAL_*}` → `DedZapretData/data/upstreams/flowseal/*` (важно: использует `ctx.paths.upstreams_dir`)
   - совместимость имён листов: `_resolve_list_path_compat(ctx, path_str)`.
   - удаляет `%GameFilterTCP%/%GameFilterUDP%` токены и/или разворачивает их в конкретные порты (см. `resolve_winws_args::_resolve_game_placeholders`).

4) Preflight diagnostics:
   - форматтер: `features/zapret_runtime.py::format_preflight_diagnostics_ru` (пишет user-friendly список missing binaries/lists/fake + masked preview).
   - исключение: `features/zapret_runtime.py::WinwsStartError`.

5) Runtime assets repair:
   - при WinwsStartError UI предлагает repair → `features/runtime_assets.py::repair_runtime_assets` (использует `ensure_base_lists` + `ensure_fake_assets`).

**Процессы/PID**:
- Детаченный запуск сделан через `utils/subprocessx.py::popen_detached`.
- Проверка PID: `features/zapret_runtime.py::is_pid_alive(pid)` (Windows: WinAPI OpenProcess/GetExitCodeProcess, fallback tasklist).

### 4.2 sing-box

**Структура**:
- UI: `features/singbox_menu.py::singbox_menu(ctx)`.
- Process layer: `core/singbox/process.py::SingBoxProcess` + `core/process_supervisor.py::ProcessSupervisor` + `core/current_state.py`.

**Хранение процесса**:
- `core/current_state.py::CurrentState.processes["singbox"]` хранит pid/running/started_utc/exit_code/last_error.
- запись состояния: `core/process_supervisor.py::ProcessSupervisor.set_process(...)`.

**Запуск**:
- `core/singbox/process.py::SingBoxProcess.start()`:
  - запускает `[sing-box.exe, run, -c generated_config.json]`.
  - stdout/stderr → общий log файл (см. параметры конструктора), stdin → DEVNULL.
  - Windows: `subprocess.CREATE_NEW_PROCESS_GROUP` best-effort.

**Health**:
- `core/singbox/health.py::singbox_health_summary(current_state_path)`:
  - читает `current.json` через `load_current_state`.
  - проверяет TCP 2080/2081 через `socket.create_connection`.

**System proxy (опционально)**:
- `core/singbox/system_proxy_win.py`:
  - `enable_local_proxy_with_backup(path, host, port)` → backup registry values + write ProxyEnable/ProxyServer/ProxyOverride.
  - `restore_system_proxy(path)`.
  - это вызывается в меню `features/singbox_menu.py::_sb_enable_system_proxy/_sb_restore_system_proxy`.

### 4.3 TG proxy

Есть два слоя реализации (важно для дальнейшей чистки):

1) Актуальный функционал меню использует **функции** из `features/tg_proxy.py`:
- install/uninstall/start/stop для Go-версии: `install_go`, `start_go`, `stop_go`, `uninstall_go`.
- install/uninstall/start/stop для Rust-версии: `install_rust`, `start_rust`, `stop_rust`, `uninstall_rust`.
- хранение pid/path/tag/sha256: `ctx.state.tg["go"|"rust"]` (см. `core/state.py::AppState.tg`).

2) В `features/system.py` присутствует класс `TgProxyManager` (строки ~207+), который:
- ищет бинарник по другому пути (`runtime_dir / "tg" / "tgws-proxy"`),
- запускает через `subprocess.Popen` и хранит `self.process`.

Статус: **дублирование дизайна**. Какой из путей используется UI сейчас — зависит от `ui/menus.py::tg_menu` (не читался → UNKNOWN). Факт наличия двух реализаций фиксируется как tech debt.

### 4.4 DoH

Также есть два разных слоя:

1) Реальная логика запуска cloudflared и подмены DNS:
- `features/doh.py::start_doh(ctx, profile)`:
  - требует admin: `ensure_admin_windows`.
  - определяет adapter: `detect_adapter(ctx)` (PowerShell Get-NetAdapter если config пуст).
  - читает текущие DNS: `_get_dns_state(adapter)`.
  - запускает `cloudflared.exe proxy-dns ...` через `popen_detached`.
  - меняет DNS на 127.0.0.1 через `netsh interface ip set dns ...`.
  - сохраняет предыдущее состояние в `ctx.state.doh.prev_dns`.
- `features/doh.py::stop_doh(ctx)`:
  - taskkill по pid,
  - восстанавливает DHCP/static DNS по `prev_dns`.

2) В `features/system.py` присутствует класс `DohManager` с PowerShell-командами вокруг DoH-политик.

Статус: **дублирование/конфликт источников истины**: UI использует `features/doh.py` (см. импорт в `ui/menus.py`: `from app.zapret_manager.features.doh import PROFILES, start_doh, stop_doh`).

---

## 5. Strategy system

### 5.1 Модель

- `strategies/model.py::Strategy`
  - `name`, `engine` (winws|winws2|bat), `args`.
  - метаданные: `source_file`, `upstream`, `kind`.
  - доп. поля (частично legacy/в развитии):
    - `winws_params` (List[str])
    - `discord_profile`, `games_profile`
    - `hostlist_exclude`, `wssize`.
  - `get_full_args()` сейчас просто `args + winws_params + (wssize block)`.
    - Примечание: основной запуск winws использует **strategy.args** + overlays/composer, а не `get_full_args()` напрямую (см. `features/zapret_runtime.py::build_command`).

### 5.2 Где лежат стратегии

Хранилища определяются `core/paths.py::Paths.from_root`:

- builtin: `DedZapretData/data/strategies/builtin` (`paths.strategies_builtin_dir`)
- generated: `DedZapretData/data/strategies/generated` (`paths.strategies_generated_dir`)
- custom: `DedZapretData/data/strategies/custom` (`paths.strategies_custom_dir`)

### 5.3 Загрузка/индексация

- простая загрузка файлов: `strategies/store.py::list_strategies(dir_path, kind)`
- сохранение: `strategies/store.py::save_strategy(dir_path, strategy)`.
- индексатор: `strategies/manager.py::StrategyManager`
  - пишет `index.json` в директорию стратегий.
  - `StrategyManager.rebuild_index()` сканирует `store.list_strategies`.
  - Используется в `core/app_context.py::AppContext.bootstrap` (создаёт менеджеры) и `AppContext.auto_sync()` (после upstream sync делает `strategies_generated.rebuild_index()`).

### 5.4 Компоновка стратегии (layers)

Есть **две** параллельные механики:

1) `strategies/composer.py::compose(...)` (основной компоновщик слоями):
- вход: base Strategy + youtube Strategy + discord Strategy + discord_script + games_profile + rkn_enabled + wssize_enabled.
- правила:
  - YouTube вставляется перед первым `--new` (см. `_insert_before_first_new`).
  - Discord слой заменяет "discord block" в base по эвристике `_is_discord_block`.
  - Discord script добавляет блоки `50-*` (см. `_discord_script_args`).
  - Games profile добавляет блоки из `strategies/overlays.py::games_profile_args`.
  - wssize добавляет `--new --filter-tcp=443 --wssize 1:6`.
  - rkn toggle заменяет hostlist args, используя `{MGR_LISTS}rkn.txt`.

2) `strategies/overlays.py::apply_overlays(base_args, discord_profile, games_profile)`
- сейчас фактически добавляет **только games** (комментарий: discord не используется здесь).
- используется в `features/zapret_runtime.py::build_command` до `resolve_winws_args`.

### 5.5 Flowseal стратегии

- upstream sync: `features/upstreams.py::sync_flowseal(ctx)`
  - скачивает repo zip через `upstreams/sync.py::sync_repo_zip` (файл не читался → UNKNOWN)
  - кладёт в `DedZapretData/data/upstreams/flowseal`
  - генерирует стратегии в generated dir: `strategies/flowseal_import.py::import_flowseal_strategies`.

- импорт Flowseal:
  - сканирует `flowseal_root/*.bat`.
  - фильтрует helper-скрипты по имени/эвристикам `_is_probably_strategy_bat`.
  - извлекает команду winws: `strategies/flowseal_parser.py::extract_winws_command` (файл не читался → детали UNKNOWN).
  - kind определяется по имени: `yv*` → youtube, `dv*` → discord, иначе base.

### 5.6 StressOzz стратегии

- sync: `features/upstreams.py::sync_stressozz_strategies(ctx)`
  - скачивает `Zapret-Manager.sh` в `DedZapretData/data/upstreams/stressozz/Zapret-Manager.sh`
  - импортит base vN: `strategies/stressozz_import.py::import_v_strategies_from_script`
  - импортит YouTube pack YvNN из `ListStrYou`: `import_liststryou`
  - импортит DvN: `import_dv_strategies_from_script`.

### 5.7 Asset resolver / placeholders

- `{LISTS}`/`{MGR_LISTS}`/`{RT_LISTS}`/`{FAKE}`/`{FLOWSEAL_*}` разрешаются в `features/zapret_runtime.py::resolve_winws_args`.
- совместимость имён файлов списков: `_resolve_list_path_compat`.
- repair lists/fake:
  - `features/runtime_assets.py::ensure_base_lists` создаёт/копирует базовые списки + алиасы + пустые user files.
  - `features/runtime_assets.py::ensure_fake_assets` ищет fake файлы по runtime tree и копирует в canonical fake dir (без создания пустых .bin).

### 5.8 Preflight

- validate referenced files:
  - `features/zapret_runtime.py::validate_strategy_assets(ctx, strategy)` (не читалось полностью → UNKNOWN)
  - `features/zapret_runtime.py::validate_winws_command(ctx, cmd, cwd)` (не читалось полностью → UNKNOWN)
- ошибки запуска winws должны подниматься как `WinwsStartError` и показываться пользователю (см. `ui/main_menu.py::_offer_repair_and_retry_start`).

---

## 6. sing-box system

### 6.1 Subscriptions

- модель: `core/singbox/subscriptions.py::SubscriptionRecord`.
- storage:
  - `load_subscriptions(path)` / `save_subscriptions(path, subs)`.
  - путь задаётся в `features/singbox_menu.py::_subscriptions_path(ctx)` → `DedZapretData/data/singbox/subscriptions.json`.

- parsing:
  - `parse_subscription_payload(text)` — plain or base64 list of links.
  - `parse_subscription_payload_detailed(text)` — расширенный best-effort:
    - sing-box JSON outbounds (`_parse_singbox_json_outbounds`)
    - Clash YAML subset (shadowsocks only) (`_parse_clash_yaml_shadowsocks`)
    - fallback plain/base64.

- download:
  - используется `download_subscription_text(url)` (импортируется в `features/singbox_menu.py`, но реализация не читалась → UNKNOWN).

### 6.2 Nodes

- модель: `core/singbox/nodes.py::SingBoxNode`.
- storage:
  - `load_nodes(path)` / `save_nodes(path, nodes)`.
  - raw link сохраняется masked (см. `save_nodes`: `"raw": mask_secrets_text(n.raw)`), но `uuid/password/method` сохраняются как есть локально.

- import:
  - `import_node_from_link(link)` поддерживает `vless/vmess/trojan/ss`.

### 6.3 Active node

- хранится в `core/current_state.py::CurrentState.active_singbox_node_id`.
- выбирается через `features/singbox_menu.py::_sb_select_node`.
- auto-select при update subscriptions: `features/singbox_menu.py::_sb_update_subscriptions` (если active пустой и imported>0 → выбрать nodes[0]).

### 6.4 Config

- builder: `core/singbox/config_builder.py::build_config(node, opt)`.
  - inbounds: socks 2080 + mixed 2081.
  - outbounds: proxy + direct + block.
  - DNS presets: `DNS_PRESETS` по `opt.dns_mode`.

- write: `core/singbox/config_builder.py::write_config(path, cfg)`.
- путь: `features/singbox_menu.py::_config_path(ctx)` → `DedZapretData/data/singbox/generated_config.json`.

### 6.5 Health

- core health: `core/singbox/health.py::singbox_health_summary(current_state_path)`.
- aggregated report: `features/singbox_health.py` (используется в `singbox_menu` и bug-report flow через menu_handler, но файл не читался в этом аудите → UNKNOWN детали).

---

## 7. Test system

### 7.1 Single strategy test

- ядро тестов: `features/strategy_test.py`.
- главный тип результата: `features/strategy_test.py::TestResult` (status=ok|invalid).
- probes:
  - quick: `_fetch_one_quick` (HTTP GET + Range)
  - full: `_fetch_one_detail` (DNS/TCP/PING/UDP443 + HTTP GET)

Запуск стратегии в тесте:
- `features/strategy_test.py::test_strategy(ctx, base_strategy, domains, ...)` (реализация не читалась до конца → UNKNOWN детали), но импортирует:
  - `features/zapret_runtime.py::start_zapret_interactive` / `stop_zapret`
  - `features/zapret_runtime.py::WinwsStartError`
  - `features/zapret_runtime.py::is_pid_alive`.

### 7.2 Test all strategies

- UI: `ui/menus.py::_test_all_strategies_menu`.
- engine: `features/strategy_test.py::test_all_strategies_with_progress` (импорт в `ui/menus.py`, реализация не читалась полностью → UNKNOWN детали).
- outputs:
  - telemetry jsonl: `DedZapretData/data/telemetry/strategy_runs.jsonl` (см. вывод в `_test_all_strategies_menu`).
  - ranking json: `DedZapretData/data/telemetry/latest_strategy_ranking.json`.
  - pinned top-N стратегии сохраняются в `custom` (см. `TestSessionSummary.pinned` в `features/strategy_test.py`).

### 7.3 Domain sets

- модель: `features/test_sets.py::DomainSet`.
- файлы: `DedZapretData/data/tests/domains_*.txt` (см. `DomainSet.rel_path`).
- bootstrap создаёт default наборы: `features/test_sets.py::ensure_domain_sets(ctx)` вызывается из `core/app_context.py::AppContext.bootstrap`.
- чтение: `read_domain_set_file(path)`.
- combine: `combine_domain_sets(ctx, keys)`.

### 7.4 Problem domains

- canonical storage v2: `features/problem_domains.py::load_problem_domains(ctx)` / `save_problem_domains(ctx, data)`.
- файл: `DedZapretData/data/problem_domains.json` (см. `_problem_domains_path`).
- миграции/коррупция:
  - делает backup копию и сбрасывает на пустой v2 (`_backup_copy`, `atomic_write_json`).

- test all strategies интеграция:
  - после свипа UI предлагает добавить fail-домены в problem domains:
    - `ui/menus.py::_test_all_strategies_menu` вызывает `add_problem_domains_from_results` (импорт внутри блока; реализация в `problem_domains.py` не проверена в этом аудите → UNKNOWN).
  - также пытается обновить summary artifacts: `write_problem_domains_summary_artifacts(ctx)`.

---

## 8. Diagnostics/report system

### 8.1 Bug report (core/report.py)

- `core/report.py::generate_bug_report_zip(out_dir, logs_dir, state_file, current_state_file, config_file, extra_files=None)`
  - пишет `meta.json` + masked copies:
    - `config_masked.yaml`
    - `state_masked.json`
    - `current_masked.json`
  - добавляет `tree.txt` (дерево DedZapretData)
  - добавляет `logs/*.log` и `logs/*.jsonl`
  - добавляет `results/results_*.txt` если есть
  - `extra/*` — дополнительные файлы, тоже проходят `mask_secrets`.

### 8.2 Diagnostics session recorder (core/diagnostics.py)

- `core/diagnostics.py::SessionRecorder`
  - хранит `meta` (session_id, started_utc, version, git_commit, os, python)
  - пишет события jsonl: `session_<sid>.jsonl`
  - управляющий API: `diag_log(category, component, payload)`.

- wired in bootstrap:
  - `core/app_context.py::AppContext.bootstrap` создаёт `SessionRecorder` независимо от enabled.

### 8.3 Masking

- `core/mask.py::mask_secrets_text` + `mask_secrets(obj)`.
- применяется в:
  - `core/report.py` (mask config/state/logs/extra)
  - `features/diagnostics_artifacts.py::_write_text` (mask при записи artifacts)
  - `core/menu_actions.py::menu_handler` user-facing error msg.

### 8.4 Diagnostics artifacts

- `features/diagnostics_artifacts.py::write_all_diagnostics_artifacts(ctx)` создаёт:
  - `latest_strategy_ranking.txt` (из `data/telemetry/latest_strategy_ranking.json`)
  - `runtime_asset_report.json/.txt`
  - `flowseal_asset_report.json/.txt`
  - output dir: `DedZapretData/data/diagnostics` (см. `diagnostics_dir`).

- интеграции:
  - System menu: `ui/menus.py` пункт `X) Support: Сформировать диагностические артефакты`.
  - Bug report menu: `ui/menus.py::_support_generate_bug_report` вызывает artifacts best-effort и добавляет их в `extra/`.

---

## 9. State/storage

### 9.1 state.json (AppState)

- файл: `DedZapretData/data/state/state.json` (см. `core/paths.py::Paths.state_file`).
- модель/loader:
  - `core/state.py::AppState` + `load_state(path)` + `save_state(path, state)`.
- ключевые поля:
  - `runtime` (installed/runtime_path/winws_path/winws2_path)
  - `zapret` (running/pid/base_strategy/selected_strategy + layers/toggles)
  - `doh` (enabled/profile/pid/prev_dns)
  - `hosts.blocks` (dict[str,bool])
  - `tg` (dict[str,Any]) — используется и для tg proxy state, и для `domain_set` выбора в тестах (`ui/menus.py::_domains_for_current_set`).

### 9.2 current.json (CurrentState)

- файл: `DedZapretData/data/state/current.json`.
- модель:
  - `core/current_state.py::CurrentState`.
- процессы:
  - `processes["singbox"]` managed через `ProcessSupervisor`.

### 9.3 nodes/subscriptions

- nodes: `DedZapretData/data/singbox/nodes.json` (`features/singbox_menu.py::_nodes_path`).
- subscriptions: `DedZapretData/data/singbox/subscriptions.json` (`_subscriptions_path`).

### 9.4 problem_domains.json

- файл: `DedZapretData/data/problem_domains.json` (`features/problem_domains.py::_problem_domains_path`).

### 9.5 telemetry/diagnostics

- telemetry:
  - `DedZapretData/data/telemetry/strategy_runs.jsonl`
  - `DedZapretData/data/telemetry/latest_strategy_ranking.json`

- diagnostics artifacts:
  - `DedZapretData/data/diagnostics/latest_strategy_ranking.txt`
  - `DedZapretData/data/diagnostics/runtime_asset_report.{json,txt}`
  - `DedZapretData/data/diagnostics/flowseal_asset_report.{json,txt}`

---

## 10. Known technical debt

### 10.1 unittest discover не green в текущем окружении

Запуск:

```bash
python3 -m unittest discover -s tests -p 'test_*_unittest.py' -v
```

показывает ошибки вида:

```
AttributeError: 'types.SimpleNamespace' object has no attribute 'upstreams_dir'
```

Источник:
- `features/zapret_runtime.py::resolve_winws_args` использует `ctx.paths.upstreams_dir` (строка ~642),
- тесты `tests/test_lists_resolution_unittest.py` и `tests/test_wf_inference_unittest.py` создают ctx как `SimpleNamespace(paths=SimpleNamespace(...))`, где `upstreams_dir` отсутствует.

Это не “долг” runtime-логики, но **долг совместимости API тестовых фикстур** с текущим интерфейсом `Paths`.

### 10.2 Дублирование менеджеров (system.py vs features/*)

- DoH:
  - “реальный” flow: `features/doh.py::start_doh/stop_doh` (cloudflared + netsh)
  - параллельный класс: `features/system.py::DohManager` (PowerShell политика/скрипты)

- TG proxy:
  - “реальный” flow: `features/tg_proxy.py::*` (download assets + detached run + state)
  - параллельный класс: `features/system.py::TgProxyManager`.

Риск: разные пути хранения/статуса и разные ожидания layout.

### 10.3 Смешение ответственности state.tg

- `core/state.py::AppState.tg` используется одновременно:
  - для состояния tg proxy (go/rust)
  - для хранения `domain_set` выбора тестов (`ui/menus.py::_domains_for_current_set`).

Это затруднит дальнейшее разделение доменов данных.

### 10.4 Strategy model содержит частично “неиспользуемые” поля

- `Strategy.winws_params`, `Strategy.wssize`, `get_full_args()`.
- Основной runtime builder (`features/zapret_runtime.py::build_command`) использует `strategy.args` + overlays + resolve_winws_args + wf inference.

Риск: два источника истины о том, какие args реально уйдут в winws.

### 10.5 menu_actions wrapper и ручная обработка исключений

- Часть меню функций использует `@menu_handler(...)` (см. `core/menu_actions.py`).
- Другая часть оборачивает try/except локально (см. `ui/menus.py` многочисленные `except Exception as e:`).

Риск: неоднородный UX и разные политики логирования.

---

## 11. Safe next refactor plan

Ниже — минимально рискованный план следующего слоя, чтобы не строить “поверх мусора”.

### 11.1 commands.py

Цель: единый слой “действий”, который UI вызывает без знания деталей.

Безопасные шаги:
1) Вынести из `ui/menus.py` чистые side-effect функции в `features/commands.py` (новый модуль) — только thin wrappers.
2) Переиспользовать `core/menu_actions.py::menu_handler` как единую точку audit/diag.
3) Оставить `ui/menus.py` только как routing + вывод.

### 11.2 profiles.py

Цель: централизовать профили запуска (games/programs) и layers.

Шаги:
1) Разделить `AppState.tg` на:
   - `AppState.tg_proxy` (структура)
   - `AppState.ui_prefs` (например domain_set)
   - или отдельный storage файл.
2) `features/game_launcher.py` перевести на отдельный storage (не править config.yaml напрямую в runtime) — **только после** согласования UX.

### 11.3 telemetry foundation

Цель: сделать единый модуль записи результатов тестов/ранжирования.

Шаги:
1) Явно описать schema telemetry JSON/JSONL рядом с writer (например `features/telemetry.py`).
2) Изолировать генерацию `latest_strategy_ranking.json` от UI.

### 11.4 autostart / watcher / tray

Цель: добавить background режим без ломания текущей CLI.

Шаги:
1) Сначала определить single source of truth процессов: расширить `CurrentState.processes` для zapret/tg/doh.
2) Process watcher должен читать `current.json` и проверять PID/port status.
3) Tray/GUI должны **только отображать** и вызывать commands layer.

### 11.5 compact mode

Цель: стабилизировать модель “layers” и отображение статусов.

Шаги:
1) Явно перечислить активные слои в одном месте (например `features/zapret_runtime.py` или новый `features/zapret_profile.py`).
2) Стандартизировать отображение в `_status_lines(ctx)`.

---

## Appendix: Files referenced

Основные файлы, использованные в этом аудите (не полный список):

- Entry/UI: `app/zapret_manager/__main__.py`, `app/zapret_manager/main.py`, `app/zapret_manager/ui/main_menu.py`, `app/zapret_manager/ui/menus.py`
- Context/config/paths/state: `app/zapret_manager/core/app_context.py`, `app/zapret_manager/core/paths.py`, `app/zapret_manager/core/config.py`, `app/zapret_manager/core/state.py`, `app/zapret_manager/core/current_state.py`
- Runtime zapret: `app/zapret_manager/features/zapret_runtime.py`, `app/zapret_manager/features/runtime_assets.py`, `app/zapret_manager/strategies/composer.py`, `app/zapret_manager/strategies/overlays.py`, `app/zapret_manager/strategies/store.py`, `app/zapret_manager/strategies/manager.py`
- Upstreams: `app/zapret_manager/features/upstreams.py`, `app/zapret_manager/strategies/flowseal_import.py`, `app/zapret_manager/strategies/stressozz_import.py`
- sing-box: `app/zapret_manager/features/singbox_menu.py`, `app/zapret_manager/core/singbox/*`, `app/zapret_manager/core/process_supervisor.py`
- Tests: `app/zapret_manager/features/strategy_test.py`, `app/zapret_manager/features/test_sets.py`, `app/zapret_manager/features/problem_domains.py`
- Diagnostics: `app/zapret_manager/core/diagnostics.py`, `app/zapret_manager/core/report.py`, `app/zapret_manager/features/diagnostics_artifacts.py`, `app/zapret_manager/core/mask.py`
