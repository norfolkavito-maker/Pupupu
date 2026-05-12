from __future__ import annotations

import logging
from pathlib import Path

import yaml

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.state import save_state
from app.zapret_manager.ui.colors import C
from app.zapret_manager.features.blockcheck import run_blockcheck
from app.zapret_manager.features.key_setup import key_setup, key_setup_full_check
from app.zapret_manager.features.lists import update_exclude, update_rkn
from app.zapret_manager.features.selection import find_strategy, list_bases, list_layers
from app.zapret_manager.features.strategy_test import (
    DEFAULT_TEST_DOMAINS,
    get_speed_settings,
    set_speed_settings,
    TestResult,
    ProofResult,
    control_test,
    control_test_mode,
    test_strategy,
    test_session,
    proof_of_effect,
    write_results,
    test_all_strategies_with_progress,
)
from app.zapret_manager.features.test_sets import DOMAIN_SETS, read_domain_set_file, combine_domain_sets
from app.zapret_manager.features.sysinfo import system_info_text
from app.zapret_manager.features.system import (
    backup,
    flush_dns,
    quic_block_disable,
    quic_block_enable,
    quic_rule_exists,
    restore,
    tcp_timestamps_disable,
    tcp_timestamps_enable,
    show_tcp_timestamp_status,
)
from app.zapret_manager.features.tg_proxy import (
    install_go,
    install_rust,
    start_go,
    start_rust,
    stop_go,
    stop_rust,
    uninstall_go,
    uninstall_rust,
)
from app.zapret_manager.features.upstreams import (
    check_updates,
    sync_flowseal,
    sync_stressozz_strategies,
)
from app.zapret_manager.features.hosts import (
    finland_discord_block,
    load_blocks_from_file,
    reset_hosts_windows,
    set_block_enabled,
    has_block,
    clear_all_manager_blocks,
)
from app.zapret_manager.features.zapret_runtime import (
    runtime_diagnostics_text,
    runtime_health,
    start_zapret_interactive,
    stop_zapret,
    WinwsStartError,
)
from app.zapret_manager.features.runtime_assets import repair_runtime_assets
from app.zapret_manager.features.test_urls import prepare_urls
from app.zapret_manager.utils.console import ask, clear, pause, safe_print

from app.zapret_manager.features.doh import PROFILES, start_doh, stop_doh
from app.zapret_manager.features.game_launcher import (
    add_profile,
    generate_bat,
    generate_shortcut,
    list_profiles,
    remove_profile,
    run_profile,
)
from app.zapret_manager.features.problem_domains import (
    add_problem_domain,
    clear_problem_domains,
    get_problem_domain_list,
    load_problem_domains,
    problem_domains_summary,
    remove_resolved_domain,
    write_problem_domains_summary_artifacts,
)

from app.zapret_manager.features.app_update import (
    AppUpdateError,
    build_update_plan,
    run_update,
)

from app.zapret_manager.core.menu_actions import menu_handler
from app.zapret_manager.core.current_state import load_current_state
from app.zapret_manager.features.singbox_health import build_singbox_health_report, write_singbox_health_artifacts
from app.zapret_manager.core.report import generate_bug_report_zip
from app.zapret_manager.features.diagnostics_artifacts import write_all_diagnostics_artifacts
from app.zapret_manager.core.commands import (
    create_bug_report as cmd_create_bug_report,
    generate_diagnostics_artifacts as cmd_generate_diagnostics_artifacts,
    singbox_health as cmd_singbox_health,
)


log = logging.getLogger(__name__)


def _test_concurrency(ctx: AppContext) -> int:
    """Return current configured concurrency for domain checks."""
    try:
        s = get_speed_settings(ctx)
        return int(s.get("concurrency", 8))
    except Exception:
        return 8


def _speed_settings_menu(ctx: AppContext) -> None:
    """UI to edit sweep/test speed settings stored in state.json.

    Workflow 02 requirement: keep this under existing test menu.
    """
    while True:
        clear()
        s = get_speed_settings(ctx)
        safe_print(f"{C.MAGENTA}Настройки скорости теста{C.RESET}\n")

        safe_print(f"{C.CYAN}1){C.RESET} Параллельные проверки доменов: {s['concurrency']}")
        safe_print(f"{C.CYAN}2){C.RESET} Connect timeout (сек): {s['connect_timeout_s']}")
        safe_print(f"{C.CYAN}3){C.RESET} Read timeout (сек): {s['read_timeout_s']}")
        safe_print(f"{C.CYAN}4){C.RESET} Общий лимит на домен (сек): {s['total_domain_timeout_s']}")
        safe_print(f"{C.CYAN}5){C.RESET} Общий лимит на стратегию (сек): {s['max_strategy_time_s']}")
        safe_print(
            f"{C.CYAN}6){C.RESET} Подробный вывод в консоль: {'ON' if s['detailed_console_output'] else 'OFF'}"
        )
        safe_print(f"{C.CYAN}7){C.RESET} DNS cache: {'ON' if s['dns_cache'] else 'OFF'}")
        safe_print(
            f"{C.CYAN}8){C.RESET} Deduplicate одинаковые стратегии: {'ON' if s['deduplicate_equivalent_strategies'] else 'OFF'}"
        )
        safe_print("")

        c = ask(f"{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return

        try:
            if c == "1":
                v = ask("Новая параллельность (1/4/8/16): ").strip()
                if v.isdigit():
                    set_speed_settings(ctx, {"concurrency": int(v)})
            elif c == "2":
                v = ask("Connect timeout (сек): ").strip().replace(",", ".")
                set_speed_settings(ctx, {"connect_timeout_s": float(v)})
            elif c == "3":
                v = ask("Read timeout (сек): ").strip().replace(",", ".")
                set_speed_settings(ctx, {"read_timeout_s": float(v)})
            elif c == "4":
                v = ask("Лимит на домен (сек): ").strip().replace(",", ".")
                set_speed_settings(ctx, {"total_domain_timeout_s": float(v)})
            elif c == "5":
                v = ask("Лимит на стратегию (сек): ").strip().replace(",", ".")
                set_speed_settings(ctx, {"max_strategy_time_s": float(v)})
            elif c == "6":
                set_speed_settings(ctx, {"detailed_console_output": not bool(s.get("detailed_console_output"))})
            elif c == "7":
                set_speed_settings(ctx, {"dns_cache": not bool(s.get("dns_cache"))})
            elif c == "8":
                set_speed_settings(
                    ctx,
                    {"deduplicate_equivalent_strategies": not bool(s.get("deduplicate_equivalent_strategies"))},
                )
        except Exception as e:
            safe_print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
            pause()


def _choose_test_mode() -> str:
    """Ask user for quick/full test mode."""
    # IMPORTANT: use safe_print for Cyrillic output. Windows CI stdout can be
    # cp1252/cp866 and a raw print may crash with UnicodeEncodeError.
    safe_print(f"\n{C.YELLOW}Режим проверки:{C.RESET}")
    safe_print(f"{C.CYAN}1){C.RESET} Быстрая проверка доступа (HTTP GET + Range)")
    safe_print(f"{C.CYAN}2){C.RESET} Полная диагностика (DNS/TCP/PING/UDP/HTTP)")
    ans = ask(f"\n{C.YELLOW}Выберите режим:{C.RESET} ").strip()
    if ans == "1":
        return "quick"
    return "full"


def auto_setup_menu(ctx: AppContext) -> None:
    """Автоматическая настройка (мастер).

    В рамках реорганизации меню: переносим "под ключ" и full-check в отдельный раздел.
    """
    while True:
        clear()
        print(f"{C.MAGENTA}Автоматическая настройка{C.RESET}\n")
        print(f"{C.CYAN}1){C.RESET} {C.GREEN}Быстрая автонастройка «под ключ»{C.RESET}")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}Под ключ + полная проверка/подбор (мастер){C.RESET}")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}Просмотр проблемных доменов{C.RESET}")
        print(f"{C.CYAN}4){C.RESET} {C.GREEN}Очистить проблемные домены{C.RESET}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        try:
            if c == "1":
                lines = key_setup(ctx)
                print()
                for ln in lines:
                    print(ln)
                print()
                pause()
            elif c == "2":
                lines = key_setup_full_check(ctx)
                print()
                for ln in lines:
                    print(ln)
                print()
                pause()
            elif c == "3":
                _problem_domains_menu(ctx)
            elif c == "4":
                clear_problem_domains(ctx)
                print(f"\n{C.GREEN}Все проблемные домены очищены.{C.RESET}\n")
                pause()
        except Exception as e:
            log.exception("auto_setup_menu failed")
            print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
            pause()


def extras_menu(ctx: AppContext) -> None:
    """Дополнительные режимы (YouTube/Discord/Games/TG/DNS/Hosts/Launcher)."""
    while True:
        clear()
        print(f"{C.MAGENTA}Дополнительные режимы{C.RESET}\n")
        print(f"{C.CYAN}1){C.RESET} {C.GREEN}YouTube слой{C.RESET} (в меню стратегий)")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}Discord{C.RESET}")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}Games{C.RESET} (профили Gv1..Gv4 в меню стратегий)")
        print(f"{C.CYAN}4){C.RESET} {C.GREEN}TG WS Proxy{C.RESET}")
        print(f"{C.CYAN}5){C.RESET} {C.GREEN}DNS over HTTPS{C.RESET}")
        print(f"{C.CYAN}6){C.RESET} {C.GREEN}Hosts{C.RESET}")
        print(f"{C.CYAN}7){C.RESET} {C.GREEN}Запуск игры / программы{C.RESET}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        try:
            if c == "2":
                discord_menu(ctx)
            elif c == "4":
                tg_menu(ctx)
            elif c == "5":
                doh_menu(ctx)
            elif c == "6":
                hosts_menu(ctx)
            elif c == "7":
                game_launcher_menu(ctx)
        except Exception as e:
            log.exception("extras_menu failed")
            print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
            pause()


def service_menu(ctx: AppContext) -> None:
    """Настройки / обслуживание.

    Пока является оболочкой над существующим system_menu(), чтобы сохранить функционал
    и постепенно перегруппировать пункты.
    """
    system_menu(ctx)


def strategies_menu(ctx: AppContext) -> None:
    """
    StressOzz-like menu_str():
    1) v strategies
    2) Flowseal strategies
    3) YouTube strategies (Yv)
    4) Games strategies (Gv)
    5) RKN toggle
    6) Update exclude list
    7) wssize toggle
    """
    while True:
        clear()
        # Human-friendly header (Workflow 03)
        print(
            "Стратегия — это технический набор параметров winws.\n"
            "Профиль — это пользовательский сценарий (например Discord или Games).\n"
        )
        base = ctx.state.zapret.base_strategy or "-"
        yv = ctx.state.zapret.youtube_layer or "-"
        dv = ctx.state.zapret.discord_layer or "-"
        rkn = "ON" if ctx.state.zapret.rkn_enabled else "OFF"
        gv = ctx.state.zapret.games_profile or "-"
        wss = "ON" if ctx.state.zapret.wssize_enabled else "OFF"
        eng = (getattr(ctx.state.zapret, "engine_mode", "auto") or "auto").strip().lower()

        # Best-effort: show recommended strategy from latest ranking
        recommended = "-"
        try:
            from app.zapret_manager.core.commands import get_status_summary

            ss = get_status_summary(ctx)
            if ss.ok and isinstance(ss.details, dict):
                latest = ss.details.get("latest_ranking")
                if isinstance(latest, dict):
                    recommended = str(latest.get("recommended") or "").strip() or "-"
        except Exception:
            recommended = "-"

        print(f"{C.MAGENTA}Меню стратегий{C.RESET}\n")
        print(f"{C.YELLOW}Base:{C.RESET} {C.CYAN}{base}{C.RESET}")
        print(f"{C.YELLOW}Recommended:{C.RESET} {C.CYAN}{recommended}{C.RESET}")
        print(f"{C.YELLOW}Engine mode:{C.RESET} {C.CYAN}{eng}{C.RESET}")
        print(f"{C.YELLOW}YouTube:{C.RESET} {C.CYAN}{yv}{C.RESET}")
        print(f"{C.YELLOW}Discord:{C.RESET} {C.CYAN}{dv}{C.RESET}")
        print(f"{C.YELLOW}RKN:{C.RESET} {C.CYAN}{rkn}{C.RESET}")
        print(f"{C.YELLOW}Games:{C.RESET} {C.CYAN}{gv}{C.RESET}")
        print(f"{C.YELLOW}wssize:{C.RESET} {C.CYAN}{wss}{C.RESET}\n")

        print(f"{C.DIM}Основное:{C.RESET}")
        print(f"{C.CYAN}R){C.RESET} {C.GREEN}Выбрать Recommended{C.RESET} {C.DIM}— по последнему рейтингу{C.RESET}")
        print(f"{C.CYAN}1){C.RESET} {C.GREEN}Выбрать и установить стратегию v1-v9{C.RESET}")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}Выбрать и установить стратегию от Flowseal{C.RESET}")
        print(f"\n{C.DIM}Профили / слои:{C.RESET}")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}Выбрать и установить стратегию для YouTube{C.RESET}")
        print(f"{C.CYAN}4){C.RESET} {C.GREEN}Выбрать и установить стратегию для игр{C.RESET}")
        print(f"\n{C.DIM}Опции:{C.RESET}")
        print(f"{C.CYAN}5){C.RESET} {C.GREEN}Включить / Выключить обход по спискам РКН{C.RESET}")
        print(f"{C.CYAN}6){C.RESET} {C.GREEN}Обновить список исключений{C.RESET}")
        print(f"{C.CYAN}7){C.RESET} {C.GREEN}Добавить / Удалить блок с --wssize 1:6{C.RESET}")
        print(f"{C.CYAN}C){C.RESET} {C.GREEN}Проверить конфликты текущих слоёв{C.RESET} {C.DIM}(MVP){C.RESET}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        try:
            if c.lower() == "r":
                from app.zapret_manager.core.commands import apply_recommended_strategy

                r = apply_recommended_strategy(ctx, restart_if_running=True)
                if r.ok:
                    print(f"\n{C.GREEN}{r.message}{C.RESET}\n")
                else:
                    print(f"\n{C.RED}{r.message}{C.RESET}\n")
                    for e in r.errors:
                        print(f"- {e}")
                pause()
            elif c == "1":
                v = ask("\nВведите версию стратегии (1-9): ").strip()
                if v.isdigit() and 1 <= int(v) <= 9:
                    _set_base(ctx, f"v{int(v)}")
            elif c == "2":
                _pick_flowseal_base(ctx)
            elif c == "3":
                _pick_youtube_layer(ctx)
            elif c == "4":
                _games_menu(ctx)
            elif c == "5":
                _toggle_rkn(ctx)
            elif c == "6":
                p = update_exclude(ctx)
                print(f"\n{C.GREEN}Exclude обновлён:{C.RESET} {p}\n")
                pause()
            elif c == "7":
                ctx.state.zapret.wssize_enabled = not ctx.state.zapret.wssize_enabled
                save_state(ctx.paths.state_file, ctx.state)
                _restart_if_running(ctx)
            elif c.lower() == "c":
                _strategy_conflicts_menu(ctx)
            else:
                continue
        except Exception as e:
            log.exception("strategies_menu failed")
            print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
            pause()


def _strategy_conflicts_menu(ctx: AppContext) -> None:
    """MVP conflicts checker (Workflow 03).

    Full logic lives in `features/strategy_conflicts.py`.
    """
    clear()
    print(f"{C.MAGENTA}Проверка конфликтов (MVP){C.RESET}\n")
    try:
        from app.zapret_manager.features.strategy_conflicts import build_conflict_report_for_current_layers

        rep = build_conflict_report_for_current_layers(ctx)
        print(rep)
    except Exception as e:
        print(f"{C.RED}Не удалось выполнить проверку:{C.RESET} {e}\n")
    pause()


def _set_base(ctx: AppContext, name: str) -> None:
    st = find_strategy(ctx, name, kind="base")
    if not st:
        raise RuntimeError(f"Стратегия {name} не найдена. Сделай sync StressOzz/Flowseal.")
    ctx.state.zapret.base_strategy = st.name
    ctx.state.zapret.selected_strategy = st.name
    save_state(ctx.paths.state_file, ctx.state)
    _restart_if_running(ctx)


def _pick_flowseal_base(ctx: AppContext) -> None:
    bases = [b for b in list_bases(ctx) if (b.upstream or "").lower() == "flowseal"]
    if not bases:
        print(f"\n{C.YELLOW}Flowseal стратегий нет. Сделай sync в меню стратегий (или system->updates).{C.RESET}\n")
        pause()
        return
    clear()
    print(f"{C.MAGENTA}Flowseal стратегии{C.RESET}\n")
    for i, st in enumerate(bases, start=1):
        mark = "*" if st.name == ctx.state.zapret.base_strategy else " "
        print(f"{mark} {i:03d}) {st.name} {C.DIM}({st.engine}){C.RESET}")
    s = ask(f"\n{C.YELLOW}Номер стратегии:{C.RESET} ").strip()
    if not s.isdigit():
        return
    idx = int(s)
    if 1 <= idx <= len(bases):
        ctx.state.zapret.base_strategy = bases[idx - 1].name
        ctx.state.zapret.selected_strategy = bases[idx - 1].name
        save_state(ctx.paths.state_file, ctx.state)
        _restart_if_running(ctx)


def _pick_youtube_layer(ctx: AppContext) -> None:
    layers = [s for s in list_layers(ctx, "youtube") if s.name.lower().startswith("yv")]
    if not layers:
        print(f"\n{C.YELLOW}YouTube стратегий нет. Сделай sync StressOzz.{C.RESET}\n")
        pause()
        return
    clear()
    print(f"{C.MAGENTA}YouTube стратегии (Yv){C.RESET}\n")
    for i, st in enumerate(layers, start=1):
        mark = "*" if st.name == ctx.state.zapret.youtube_layer else " "
        print(f"{mark} {i:03d}) {st.name}")
    s = ask(f"\n{C.YELLOW}Номер стратегии (пусто=выкл):{C.RESET} ").strip()
    if not s:
        ctx.state.zapret.youtube_layer = ""
        save_state(ctx.paths.state_file, ctx.state)
        _restart_if_running(ctx)
        return
    if not s.isdigit():
        return
    idx = int(s)
    if 1 <= idx <= len(layers):
        ctx.state.zapret.youtube_layer = layers[idx - 1].name
        save_state(ctx.paths.state_file, ctx.state)
        _restart_if_running(ctx)


def _games_menu(ctx: AppContext) -> None:
    while True:
        clear()
        print(f"{C.MAGENTA}Выберите стратегию для игр{C.RESET}\n")
        cur = ctx.state.zapret.games_profile or ""
        for i in range(1, 5):
            name = f"Gv{i}"
            state = "Удалить" if cur == name else "Установить"
            print(f"{C.CYAN}{i}){C.RESET} {C.GREEN}{state}{C.RESET} {name}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        if c in {"1", "2", "3", "4"}:
            name = f"Gv{c}"
            ctx.state.zapret.games_profile = "" if ctx.state.zapret.games_profile == name else name
            save_state(ctx.paths.state_file, ctx.state)
            _restart_if_running(ctx)


def _toggle_rkn(ctx: AppContext) -> None:
    base = find_strategy(ctx, ctx.state.zapret.base_strategy, kind="base")
    if not base:
        raise RuntimeError("Сначала выбери базовую стратегию.")
    if not any(a.startswith("--hostlist-exclude=") for a in base.args):
        raise RuntimeError("Стратегия не подходит для РКН (нет --hostlist-exclude=...).")
    if not ctx.state.zapret.rkn_enabled:
        update_rkn(ctx)
    ctx.state.zapret.rkn_enabled = not ctx.state.zapret.rkn_enabled
    save_state(ctx.paths.state_file, ctx.state)
    _restart_if_running(ctx)


def discord_menu(ctx: AppContext) -> None:
    """
    StressOzz Discord_menu (Windows-адаптация):
    1..4 choose 50-* discord script (as layer preset)
    5 remove script
    6 toggle Finland hosts
    7 choose Dv1..Dv17
    """
    while True:
        clear()
        print(f"{C.MAGENTA}Меню настройки Discord{C.RESET}\n")
        print(f"{C.YELLOW}Discord script:{C.RESET} {ctx.state.zapret.discord_script or '-'}")
        print(f"{C.YELLOW}Dv layer:{C.RESET} {ctx.state.zapret.discord_layer or '-'}")
        fin = finland_discord_block()
        enabled_fin = has_block(fin.key)
        print(f"{C.YELLOW}Finland hosts:{C.RESET} {'ON' if enabled_fin else 'OFF'}\n")
        print(f"{C.CYAN}1){C.RESET} {C.GREEN}Установить скрипт 50-stun4all{C.RESET}")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}Установить скрипт 50-quic4all{C.RESET}")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}Установить скрипт 50-discord-media{C.RESET}")
        print(f"{C.CYAN}4){C.RESET} {C.GREEN}Установить скрипт 50-discord{C.RESET}")
        print(f"{C.CYAN}5){C.RESET} {C.GREEN}Удалить скрипт{C.RESET}")
        print(f"{C.CYAN}6){C.RESET} {C.GREEN}Добавить / Удалить Финские IP в hosts{C.RESET}")
        print(f"{C.CYAN}7){C.RESET} {C.GREEN}Выбрать и установить стратегию для discord.media{C.RESET}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        try:
            if c == "1":
                ctx.state.zapret.discord_script = "50-stun4all"
                save_state(ctx.paths.state_file, ctx.state)
                _restart_if_running(ctx)
            elif c == "2":
                ctx.state.zapret.discord_script = "50-quic4all"
                save_state(ctx.paths.state_file, ctx.state)
                _restart_if_running(ctx)
            elif c == "3":
                ctx.state.zapret.discord_script = "50-discord-media"
                save_state(ctx.paths.state_file, ctx.state)
                _restart_if_running(ctx)
            elif c == "4":
                ctx.state.zapret.discord_script = "50-discord"
                save_state(ctx.paths.state_file, ctx.state)
                _restart_if_running(ctx)
            elif c == "5":
                ctx.state.zapret.discord_script = ""
                save_state(ctx.paths.state_file, ctx.state)
                _restart_if_running(ctx)
            elif c == "6":
                # toggle finland block
                is_on = has_block(fin.key)
                set_block_enabled(fin.key, not is_on)
                flush_dns()
            elif c == "7":
                _pick_dv(ctx)
            else:
                continue
        except Exception as e:
            log.exception("discord_menu failed")
            print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
            pause()


def _pick_dv(ctx: AppContext) -> None:
    layers = [s for s in list_layers(ctx, "discord") if s.name.lower().startswith("dv")]
    if not layers:
        raise RuntimeError("Dv стратегий нет. Сделай sync StressOzz.")
    clear()
    print(f"{C.MAGENTA}Dv стратегии (discord.media){C.RESET}\n")
    # sort by numeric suffix
    def key(st):
        try:
            return int(st.name[2:])
        except Exception:
            return 999

    layers = sorted(layers, key=key)
    for i, st in enumerate(layers, start=1):
        mark = "*" if st.name == ctx.state.zapret.discord_layer else " "
        print(f"{mark} {i:02d}) {st.name}")
    s = ask(f"\n{C.YELLOW}Номер стратегии (пусто=выкл):{C.RESET} ").strip()
    if not s:
        ctx.state.zapret.discord_layer = ""
        save_state(ctx.paths.state_file, ctx.state)
        _restart_if_running(ctx)
        return
    if not s.isdigit():
        return
    idx = int(s)
    if not (1 <= idx <= len(layers)):
        return
    # validate base suitability by attempting restart
    ctx.state.zapret.discord_layer = layers[idx - 1].name
    save_state(ctx.paths.state_file, ctx.state)
    try:
        _restart_if_running(ctx)
    except Exception as e:
        # rollback
        ctx.state.zapret.discord_layer = ""
        save_state(ctx.paths.state_file, ctx.state)
        raise


def hosts_menu(ctx: AppContext) -> None:
    """
    StressOzz menu_hosts 0..11:
    0..9 toggle categories
    10 toggle all
    11 reset hosts
    """
    blocks_file = (ctx.paths.data_dir / "hosts" / "blocks.json").resolve()
    base_blocks = load_blocks_from_file(blocks_file)
    while True:
        clear()
        print(f"{C.MAGENTA}Меню управления доменами в hosts{C.RESET}\n")
        for idx, b in enumerate(base_blocks):
            state = "Удалить" if has_block(b.key) else "Добавить"
            print(f"{C.CYAN}{idx}){C.RESET} {C.GREEN}{state}{C.RESET} {b.title}")
        print(f"{C.CYAN}10){C.RESET} {C.GREEN}Добавить / Удалить все домены{C.RESET}")
        print(f"{C.CYAN}11){C.RESET} {C.GREEN}Восстановить hosts{C.RESET}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        try:
            if c == "10":
                all_on = all(has_block(b.key) for b in base_blocks)
                for b in base_blocks:
                    set_block_enabled(b.key, not all_on)
                flush_dns()
                continue
            if c == "11":
                clear_all_manager_blocks()
                reset_hosts_windows()
                flush_dns()
                continue
            if not c.isdigit():
                continue
            idx = int(c)
            if 0 <= idx < len(base_blocks):
                b = base_blocks[idx]
                set_block_enabled(b.key, not has_block(b.key))
                flush_dns()
        except Exception as e:
            log.exception("hosts_menu failed")
            print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
            pause()


def test_menu(ctx: AppContext) -> None:
    """
    StressOzz TEST_menu:
    1) test v
    2) test flowseal
    3) test v+flowseal
    4) test current
    5) test by domain
    6) youtube auto test
    9) results
    0) delete results
    """
    while True:
        clear()
        have_results = any(ctx.paths.results_dir.glob("results_*.txt"))
        conc = _test_concurrency(ctx)
        print(f"{C.MAGENTA}Меню тестирования стратегий{C.RESET}\n")
        print(
            "Здесь проверяется, какие стратегии реально работают в вашей сети.\n"
            "Для первого подбора используйте “Тест всех стратегий”.\n"
            "Для проверки без обхода используйте “Control test”.\n"
        )
        print(f"{C.DIM}Speed: concurrency={conc} (меняется в 'S' → Настройки скорости теста){C.RESET}\n")

        print(f"{C.DIM}Основное:{C.RESET}")
        print(f"{C.CYAN}T){C.RESET} {C.GREEN}Тест всех стратегий{C.RESET} {C.DIM}— рейтинг + прогресс{C.RESET}")
        print(f"{C.CYAN}4){C.RESET} {C.GREEN}Тест текущей стратегии{C.RESET} {C.DIM}— быстрый sanity-check{C.RESET}")
        print(f"{C.CYAN}0){C.RESET} {C.GREEN}Control test (без zapret){C.RESET} {C.DIM}— базовая доступность{C.RESET}")
        print(f"{C.CYAN}9){C.RESET} {C.GREEN}Тест проблемных доменов / автоподбор{C.RESET} {C.DIM}— TOP-5 и применение{C.RESET}")
        print(f"{C.CYAN}8){C.RESET} {C.GREEN}Proof-of-effect test{C.RESET} {C.DIM}— baseline vs strategy{C.RESET}")

        print(f"\n{C.DIM}Группы стратегий:{C.RESET}")
        print(f"{C.CYAN}1){C.RESET} {C.GREEN}Тестировать стратегии v{C.RESET}")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}Тестировать стратегии Flowseal{C.RESET}")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}Тестировать v и Flowseal стратегии{C.RESET}")
        print(f"{C.CYAN}5){C.RESET} {C.GREEN}Тестировать стратегии по домену{C.RESET}")
        print(f"{C.CYAN}6){C.RESET} {C.GREEN}YouTube auto-test (Yv){C.RESET}")

        print(f"\n{C.DIM}Результаты:{C.RESET}")
        print(f"{C.CYAN}L){C.RESET} {C.GREEN}Последний рейтинг стратегий{C.RESET}")
        print(f"{C.CYAN}R){C.RESET} {C.GREEN}Применить Recommended стратегию{C.RESET}")
        print(f"{C.CYAN}P){C.RESET} {C.GREEN}Сохранить TOP-5{C.RESET}")
        if have_results:
            print(f"{C.CYAN}A){C.RESET} {C.GREEN}Результаты тестирования стратегий{C.RESET}")
            print(f"{C.CYAN}D){C.RESET} {C.GREEN}Удалить результаты тестирования{C.RESET}")

        print(f"\n{C.DIM}Настройки теста:{C.RESET}")
        print(f"{C.CYAN}7){C.RESET} {C.GREEN}Выбрать набор доменов{C.RESET}")
        print(f"{C.CYAN}S){C.RESET} {C.GREEN}Настройки скорости теста{C.RESET}")
        print(f"{C.CYAN}O){C.RESET} {C.GREEN}Подробный / компактный вывод{C.RESET}")
        if have_results:
            pass
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        try:
            if c == "0":
                _run_control_test(ctx)
            elif c == "1":
                _run_test_group(ctx, group="v")
            elif c == "2":
                _run_test_group(ctx, group="flowseal")
            elif c == "3":
                _run_test_group(ctx, group="all")
            elif c == "4":
                _run_test_current(ctx)
            elif c == "5":
                _run_test_by_domain(ctx)
            elif c == "6":
                _youtube_auto_test(ctx)
            elif c == "7":
                _choose_domain_set(ctx)
            elif c == "8":
                _run_proof_of_effect_test(ctx)
            elif c == "9":
                _problem_domains_menu(ctx)
            elif c.lower() == "t":
                _test_all_strategies_menu(ctx)
            elif c.lower() == "s":
                _speed_settings_menu(ctx)
            elif c.lower() == "o":
                s = get_speed_settings(ctx)
                set_speed_settings(ctx, {"detailed_console_output": not bool(s.get("detailed_console_output"))})
            elif c.lower() == "l":
                _show_latest_ranking(ctx)
            elif c.lower() == "r":
                from app.zapret_manager.core.commands import apply_recommended_strategy

                r = apply_recommended_strategy(ctx, restart_if_running=True)
                if r.ok:
                    print(f"\n{C.GREEN}{r.message}{C.RESET}\n")
                else:
                    print(f"\n{C.RED}{r.message}{C.RESET}\n")
                    for e in r.errors:
                        print(f"- {e}")
                pause()
            elif c.lower() == "p":
                _save_top5(ctx)
            elif c.lower() == "a" and have_results:
                _show_results(ctx)
            elif c.lower() == "d" and have_results:
                for p in ctx.paths.results_dir.glob("results_*.txt"):
                    p.unlink(missing_ok=True)  # type: ignore[arg-type]
                print(f"\n{C.GREEN}Удалено.{C.RESET}\n")
                pause()
        except Exception as e:
            log.exception("test_menu failed")
            print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
            pause()


def _read_latest_ranking_json(ctx: AppContext) -> dict | None:
    try:
        p = (ctx.paths.data_dir / "telemetry" / "latest_strategy_ranking.json").resolve()
        if not p.exists():
            return None
        import json

        obj = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _recommended_from_ranking(ranking: dict | None) -> str:
    if not ranking:
        return ""
    rows = ranking.get("rows")
    if not isinstance(rows, list):
        return ""
    ok_rows = [r for r in rows if isinstance(r, dict) and str(r.get("status") or "ok") == "ok"]
    best = ok_rows[0] if ok_rows else next((r for r in rows if isinstance(r, dict)), None)
    if not isinstance(best, dict):
        return ""
    return str(best.get("strategy") or best.get("name") or "").strip()


def _show_latest_ranking(ctx: AppContext) -> None:
    clear()
    ranking = _read_latest_ranking_json(ctx)
    if not ranking:
        safe_print(f"{C.YELLOW}Рейтинг ещё не создан.{C.RESET} Запустите “Тест всех стратегий”.\n")
        pause()
        return
    created_at = str(ranking.get("created_at") or ranking.get("ts") or "-")
    domain_set = str(ranking.get("domain_set") or "-")
    mode = str(ranking.get("mode") or "-")
    rec = _recommended_from_ranking(ranking) or "-"

    safe_print(f"{C.MAGENTA}Последний рейтинг стратегий{C.RESET}\n")
    safe_print(f"created_at: {created_at}")
    safe_print(f"domain_set: {domain_set}")
    safe_print(f"mode: {mode}")
    safe_print(f"recommended: {rec}\n")

    rows = ranking.get("rows")
    if isinstance(rows, list):
        for i, r in enumerate(rows[:10], start=1):
            if not isinstance(r, dict):
                continue
            name = str(r.get("strategy") or r.get("name") or "-")
            ok = r.get("ok")
            fail = r.get("fail")
            score = r.get("score")
            status = str(r.get("status") or "ok")
            safe_print(f"{i:02d}. {name} | ok={ok} fail={fail} score={score} status={status}")
    safe_print("")
    pause()


def _save_top5(ctx: AppContext) -> None:
    ranking = _read_latest_ranking_json(ctx)
    if not ranking:
        safe_print(f"\n{C.YELLOW}Рейтинг ещё не создан.{C.RESET} Запустите “Тест всех стратегий”.\n")
        pause()
        return
    rows = ranking.get("rows")
    if not isinstance(rows, list) or not rows:
        safe_print(f"\n{C.YELLOW}Рейтинг пуст.{C.RESET}\n")
        pause()
        return

    ok_rows = [r for r in rows if isinstance(r, dict) and str(r.get("status") or "ok") == "ok"]
    top = ok_rows[:5]
    if not top:
        safe_print(f"\n{C.YELLOW}Нет валидных стратегий в рейтинге (все INVALID/CRASHED).{C.RESET}\n")
        pause()
        return

    out_dir = (ctx.paths.data_dir / "telemetry").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out = (out_dir / "latest_strategy_top5.txt").resolve()
    lines = ["TOP-5 strategies (latest ranking):"]
    for i, r in enumerate(top, start=1):
        name = str(r.get("strategy") or r.get("name") or "-")
        lines.append(f"{i}. {name}")
    out.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    safe_print(f"\n{C.GREEN}Сохранено:{C.RESET} {out}\n")
    pause()


def _domains_for_current_set(ctx: AppContext) -> list[str]:
    # Default behavior: use domains_default.txt if present.
    key = (ctx.state.tg.get("domain_set") or "default") if isinstance(ctx.state.tg, dict) else "default"
    if key == "all":
        # Combine all sets (excluding "all" itself).
        keys = [d.key for d in DOMAIN_SETS if d.key != "all"]
        domains = combine_domain_sets(ctx, keys)
        return domains or [f"https://{d}/" for d in DEFAULT_TEST_DOMAINS]
    ds = next((d for d in DOMAIN_SETS if d.key == key), next((d for d in DOMAIN_SETS if d.key == "default"), DOMAIN_SETS[0]))
    domains = read_domain_set_file(ds.file_path(ctx))
    return domains or [f"https://{d}/" for d in DEFAULT_TEST_DOMAINS]


def _choose_domain_set_extended(ctx: AppContext) -> tuple[str, list[str]]:
    """Extended domain set chooser for the sweep "test all strategies".

    Supported options:
      - Default
      - YouTube
      - Discord
      - Games
      - Problem domains (from problem_domains.json)
      - All (combine)
      - Custom file
    """
    clear()
    safe_print(f"{C.MAGENTA}Наборы доменов для теста стратегий{C.RESET}\n")
    safe_print(f"{C.CYAN}1){C.RESET} Default")
    safe_print(f"{C.CYAN}2){C.RESET} YouTube")
    safe_print(f"{C.CYAN}3){C.RESET} Discord")
    safe_print(f"{C.CYAN}4){C.RESET} Games")
    safe_print(f"{C.CYAN}5){C.RESET} Problem domains")
    safe_print(f"{C.CYAN}6){C.RESET} All")
    safe_print(f"{C.CYAN}7){C.RESET} Custom file")
    ans = ask(f"\n{C.YELLOW}Выберите набор:{C.RESET} ").strip()
    key = "default"
    domains: list[str] = []

    if ans == "1":
        key = "default"
        domains = read_domain_set_file(next(d for d in DOMAIN_SETS if d.key == "default").file_path(ctx))
    elif ans == "2":
        key = "youtube"
        domains = read_domain_set_file(next(d for d in DOMAIN_SETS if d.key == "youtube").file_path(ctx))
    elif ans == "3":
        key = "discord"
        domains = read_domain_set_file(next(d for d in DOMAIN_SETS if d.key == "discord").file_path(ctx))
    elif ans == "4":
        key = "games"
        domains = read_domain_set_file(next(d for d in DOMAIN_SETS if d.key == "games").file_path(ctx))
    elif ans == "5":
        key = "problem"
        domains = [f"https://{d}/" for d in get_problem_domain_list(ctx)]
    elif ans == "6":
        key = "all"
        keys = ["default", "youtube", "discord", "games"]
        domains = combine_domain_sets(ctx, keys)
    elif ans == "7":
        key = "custom"
        p = ask("\nПуть к файлу со списком доменов: ").strip()
        if p:
            domains = read_domain_set_file(Path(p))
    else:
        # fallback to current selected set
        key = (ctx.state.tg.get("domain_set") or "default") if isinstance(ctx.state.tg, dict) else "default"
        domains = _domains_for_current_set(ctx)

    # Fallback if empty: default hardcoded (but NOT for explicit problem domains).
    if not domains and key != "problem":
        domains = [f"https://{d}/" for d in DEFAULT_TEST_DOMAINS]
    return key, domains


def _choose_sweep_mode() -> str:
    clear()
    safe_print(f"{C.MAGENTA}Режим теста всех стратегий{C.RESET}\n")
    safe_print(f"{C.CYAN}1){C.RESET} Quick (builtin/base only)")
    safe_print(f"{C.CYAN}2){C.RESET} Full (builtin + generated + packs if available)")
    safe_print(f"{C.CYAN}3){C.RESET} Exhaustive (может быть очень долго)")
    ans = ask(f"\n{C.YELLOW}Выберите режим:{C.RESET} ").strip()
    if ans == "1":
        return "quick"
    if ans == "2":
        return "full"
    if ans == "3":
        warn = ask(f"\n{C.RED}ВНИМАНИЕ:{C.RESET} exhaustive может идти долго. Введите YES чтобы продолжить: ").strip()
        if warn == "YES":
            return "exhaustive"
        return "full"
    return "full"


def _test_all_strategies_menu(ctx: AppContext) -> None:
    # Domain set
    domain_set_key, base_urls = _choose_domain_set_extended(ctx)
    if domain_set_key == "problem" and not base_urls:
        safe_print(
            f"\n{C.YELLOW}Список проблемных доменов пуст.{C.RESET} Сначала запустите обычный тест или добавьте домены вручную.\n"
        )
        pause()
        return
    # NOTE: For problem domains set we do NOT auto-append default/suite.
    # It must stay strictly user-derived, otherwise it stops being a "problem" set.
    if domain_set_key == "problem":
        urls = prepare_urls(base_urls=base_urls, include_default=False, include_suite=False)
    else:
        urls = prepare_urls(base_urls=base_urls, include_default=True, include_suite=True)
    domains = [u.url for u in urls]
    if not domains:
        safe_print(f"\n{C.RED}Ошибка:{C.RESET} список доменов пуст.\n")
        pause()
        return

    mode = _choose_sweep_mode()
    parallel = 8

    # NOTE: We intentionally don't run baseline control test here; user can run it separately.
    safe_print(f"\n{C.MAGENTA}Запуск теста всех стратегий...{C.RESET}\n")
    summary, rows, ranking_json = test_all_strategies_with_progress(
        ctx,
        domains=domains,
        domain_set=domain_set_key,
        mode=mode,
        parallel=parallel,
        top_n_pin=5,
    )

    # Offer collecting failing domains into Problem Domains.
    failed = []
    for r in rows:
        checks = getattr(r, "checks", None)
        if not checks:
            continue
        for c in checks:
            if getattr(c, "ok", True):
                continue
            dom = getattr(c, "domain", "")
            if dom:
                failed.append(dom)
    if failed:
        ans = ask("\nДобавить провалившиеся домены в «Проблемные домены»? [Y/n]: ").strip().lower()
        if ans in {"", "y", "yes"}:
            from app.zapret_manager.features.problem_domains import add_problem_domains_from_results

            n = add_problem_domains_from_results(ctx, rows)
            safe_print(f"\n{C.GREEN}Добавлено/обновлено проблемных доменов:{C.RESET} {n}\n")
            # refresh artifacts (best-effort)
            try:
                write_problem_domains_summary_artifacts(ctx)
            except Exception:
                pass
    else:
        safe_print(f"\n{C.GREEN}Провалившихся доменов нет.{C.RESET}\n")

    safe_print(f"\n{C.GREEN}Готово.{C.RESET}")
    safe_print(f"{C.DIM}Results file:{C.RESET} {summary.results_file}")
    safe_print(f"{C.DIM}Ranking json:{C.RESET} {ranking_json}")
    telem = (ctx.paths.data_dir / "telemetry" / "strategy_runs.jsonl").resolve()
    safe_print(f"{C.DIM}JSONL telemetry:{C.RESET} {telem}")
    if summary.pinned:
        safe_print(f"\n{C.YELLOW}Закреплено (top 5) в custom:{C.RESET}")
        for p in summary.pinned:
            safe_print(f"- {p}")
    safe_print("")
    pause()


def _choose_domain_set(ctx: AppContext) -> None:
    clear()
    print(f"{C.MAGENTA}Наборы доменов{C.RESET}\n")
    cur = (ctx.state.tg.get("domain_set") or "default") if isinstance(ctx.state.tg, dict) else "default"
    for i, ds in enumerate(DOMAIN_SETS, start=1):
        mark = "*" if ds.key == cur else " "
        print(f"{mark} {i}) {ds.title}")
        if ds.description:
            print(f"    {C.DIM}{ds.description}{C.RESET}")
        print(f"    file: {ds.file_path(ctx)}")
    s = ask(f"\n{C.YELLOW}Выберите набор:{C.RESET} ").strip()
    if not s.isdigit():
        return
    idx = int(s)
    if not (1 <= idx <= len(DOMAIN_SETS)):
        return
    if isinstance(ctx.state.tg, dict):
        ctx.state.tg["domain_set"] = DOMAIN_SETS[idx - 1].key
        save_state(ctx.paths.state_file, ctx.state)
    print(f"\n{C.GREEN}Выбрано:{C.RESET} {DOMAIN_SETS[idx - 1].title}\n")
    pause()


def _run_control_test(ctx: AppContext) -> None:
    domains = _domains_for_current_set(ctx)
    if not domains:
        safe_print(
            f"\n{C.RED}Ошибка:{C.RESET} Набор доменов пуст. Выберите набор в меню тестов (пункт 7) или добавьте домены.\n"
        )
        pause()
        return
    mode = _choose_test_mode()
    # baseline must be WITHOUT zapret
    try:
        from app.zapret_manager.utils.platform import is_windows

        if is_windows():
            stop_zapret(ctx)
    except Exception:
        # In tests / non-Windows environments stop_zapret may be unsupported.
        pass
    r = control_test_mode(ctx, domains, mode=mode, parallel=8, progress=True)
    out = write_results(ctx, [r], "results_control.txt")
    print(f"\n{C.GREEN}Control test:{C.RESET} {r.summary_text()}\n{C.DIM}{out}{C.RESET}\n")
    pause()


def _bases_v(ctx: AppContext):
    return [b for b in list_bases(ctx) if b.name.lower().startswith("v") and b.name[1:].isdigit()]


def _bases_flowseal(ctx: AppContext):
    return [b for b in list_bases(ctx) if (b.upstream or "").lower() == "flowseal"]


def _run_test_group(ctx: AppContext, *, group: str) -> None:
    base_urls = _domains_for_current_set(ctx)
    urls = prepare_urls(base_urls=base_urls, include_default=True, include_suite=True)
    domains = [u.url for u in urls]
    parallel = 8
    mode = _choose_test_mode()
    results: list[TestResult] = [control_test_mode(ctx, domains, parallel=parallel, progress=False, mode=mode)]

    if group == "v":
        out_name = "results_versions.txt"
        ensure_flowseal = False
    elif group == "flowseal":
        out_name = "results_flowseal.txt"
        ensure_flowseal = True
    else:
        out_name = "results_all.txt"
        ensure_flowseal = True

    # run each base strategy with layers disabled
    ctx.state.zapret.youtube_layer = ""
    ctx.state.zapret.discord_layer = ""
    ctx.state.zapret.discord_script = ""
    ctx.state.zapret.games_profile = ""
    ctx.state.zapret.rkn_enabled = False
    ctx.state.zapret.wssize_enabled = False
    save_state(ctx.paths.state_file, ctx.state)

    summary = test_session(
        ctx,
        group=group,
        domains=domains,
        out_name=out_name,
        top_n=5,
        parallel=parallel,
        ensure_runtime=True,
        ensure_flowseal=ensure_flowseal,
        ensure_stressozz=True,
        mode=mode,
    )
    out = summary.results_file
    print(f"\n{C.GREEN}Готово:{C.RESET} {out}")
    if summary.pinned:
        print(f"\n{C.YELLOW}Закреплено (top 5) в custom:{C.RESET}")
        for p in summary.pinned:
            print(f"- {p}")
    print()
    pause()


def _run_test_current(ctx: AppContext) -> None:
    base = find_strategy(ctx, ctx.state.zapret.base_strategy, kind="base")
    if not base:
        raise RuntimeError("Базовая стратегия не выбрана (выбери в меню стратегий).")
    base_urls = _domains_for_current_set(ctx)
    domains = [u.url for u in prepare_urls(base_urls=base_urls, include_default=True, include_suite=True)]
    mode = _choose_test_mode()
    r = test_strategy(ctx, base, domains, parallel=8, mode=mode)
    out = write_results(ctx, [r], "results_current.txt")
    print(f"\n{C.GREEN}Результат:{C.RESET} {r.summary_text()}\n{C.DIM}{out}{C.RESET}\n")
    pause()


def _run_test_by_domain(ctx: AppContext) -> None:
    inp = ask("\nВведите домены через пробел (пример: x.com vk.com): ").strip()
    if not inp:
        return
    domains = []
    for d in inp.split():
        d = d.strip()
        if not d:
            continue
        domains.append(f"https://{d}/")
    if not domains:
        print(f"\n{C.RED}Ошибка:{C.RESET} Нет валидных доменов.\n")
        pause()
        return
    mode = _choose_test_mode()
    results: list[TestResult] = [control_test_mode(ctx, domains, parallel=8, progress=False, mode=mode)]
    strategies = _bases_v(ctx) + _bases_flowseal(ctx)
    if not strategies:
        raise RuntimeError("Стратегий нет. Сделай sync.")
    for st in strategies:
        print(f"\n{C.CYAN}Тест:{C.RESET} {st.name}")
        results.append(test_strategy(ctx, st, domains, parallel=8, mode=mode))
    out = write_results(ctx, results, "results_domain.txt")
    print(f"\n{C.GREEN}Готово:{C.RESET} {out}\n")
    pause()


def _youtube_auto_test(ctx: AppContext) -> None:
    mode = _choose_test_mode()
    base = find_strategy(ctx, ctx.state.zapret.base_strategy, kind="base")
    if not base:
        raise RuntimeError("Выбери базовую стратегию (меню стратегий).")
    yv_layers = [s for s in list_layers(ctx, "youtube") if s.name.lower().startswith("yv")]
    if not yv_layers:
        # auto ensure packs
        sync_stressozz_strategies(ctx)
        yv_layers = [s for s in list_layers(ctx, "youtube") if s.name.lower().startswith("yv")]
        if not yv_layers:
            raise RuntimeError("YouTube стратегий нет даже после sync StressOzz.")

    print(f"\n{C.YELLOW}YouTube auto-test:{C.RESET} тестируем Yv на доменах googlevideo...\n")
    pause("Enter чтобы начать...")

    for yv in yv_layers:
        print(f"\n{C.CYAN}Тест:{C.RESET} {yv.name}")
        # Use youtube pack file if user selected it; fallback to DEFAULT_TEST_DOMAINS.
        domains = _domains_for_current_set(ctx)
        if not domains:
            domains = [f"https://{d}/" for d in DEFAULT_TEST_DOMAINS]
        r = test_strategy(ctx, base, domains, youtube=yv, parallel=4, mode=mode)
        print(f"{C.YELLOW}Результат:{C.RESET} {r.summary_text()}")
        if r.ok == r.total and r.total > 0:
            ans = ask("Enter=применить, N=дальше, S=стоп: ").strip().lower()
            if ans == "":
                ctx.state.zapret.youtube_layer = yv.name
                save_state(ctx.paths.state_file, ctx.state)
                print(f"\n{C.GREEN}Применено:{C.RESET} {yv.name}\n")
                pause()
                return
            if ans == "s":
                return
        else:
            ans = ask("N=дальше, S=стоп: ").strip().lower()
            if ans == "s":
                return


def _show_results(ctx: AppContext) -> None:
    files = sorted(ctx.paths.results_dir.glob("results_*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print(f"\n{C.YELLOW}Нет результатов.{C.RESET}\n")
        pause()
        return
    clear()
    print(f"{C.MAGENTA}Результаты{C.RESET}\n")
    for i, p in enumerate(files, start=1):
        print(f"{i}) {p.name}")
    s = ask(f"\n{C.YELLOW}Номер файла:{C.RESET} ").strip()
    if not s.isdigit():
        return
    idx = int(s)
    if not (1 <= idx <= len(files)):
        return
    p = files[idx - 1]
    clear()
    print(f"{C.CYAN}{p}{C.RESET}\n")
    print(p.read_text(encoding="utf-8", errors="replace")[:12000])
    pause()


def _run_proof_of_effect_test(ctx: AppContext) -> None:
    """Run proof-of-effect test: baseline vs strategy."""
    mode = _choose_test_mode()
    # Check if strategy is selected
    strategy_name = ctx.state.zapret.selected_strategy or ctx.state.zapret.base_strategy
    if not strategy_name:
        print(f"\n{C.YELLOW}Не выбрана стратегия для тестирования.{C.RESET}")
        print(f"{C.YELLOW}Выберите стратегию в меню 'Стратегии' и повторите попытку.{C.RESET}\n")
        pause()
        return
    
    # Find the strategy
    strategy = find_strategy(ctx, strategy_name, kind="base") or find_strategy(ctx, strategy_name)
    if not strategy:
        print(f"\n{C.RED}Стратегия '{strategy_name}' не найдена.{C.RESET}")
        print(f"{C.YELLOW}Попробуйте сделать sync стратегий в системном меню.{C.RESET}\n")
        pause()
        return
    
    # Get domains for current set
    domains = _domains_for_current_set(ctx)
    if not domains:
        domains = [f"https://{d}/" for d in DEFAULT_TEST_DOMAINS]
    
    print(f"\n{C.MAGENTA}Proof-of-effect тест{C.RESET}")
    print(f"Стратегия: {strategy.name}")
    print(f"Домены: {len(domains)}")
    print(f"Формат: Базовый тест → Тест со стратегией → Сравнение")
    print("-" * 70)
    
    try:
        # Run proof-of-effect test
        result = proof_of_effect(ctx, strategy, domains, settle_s=1.5, parallel=6, mode=mode)
        
        # Display results
        print(f"\n{C.CYAN}{'domain':<25} {'baseline':<10} {'strategy':<10} {'effect':<12} {'error':<15}{C.RESET}")
        print("-" * 70)
        
        for row in result.rows:
            baseline_status = "OK" if row.baseline_ok else "FAIL"
            strategy_status = "OK" if row.strategy_ok else "FAIL"
            print(f"{row.domain:<25} {baseline_status:<10} {strategy_status:<10} {row.effect:<12} {row.strategy_error or '-':<15}")
        
        # Summary
        print("-" * 70)
        print(f"{C.MAGENTA}Сводка:{C.RESET}")
        print(f"  total: {result.total}")
        print(f"  improved: {result.improved}")
        print(f"  already_ok: {result.already_ok}")
        print(f"  no_effect: {result.no_effect}")
        print(f"  worsened: {result.worsened}")
        print(f"  invalid: {result.invalid}")
        
        # WinWS evidence
        print(f"\n{C.MAGENTA}WinWS доказательство:{C.RESET}")
        print(f"  pid: {result.winws_pid or 'N/A'}")
        print(f"  alive at start: {result.winws_alive_at_start}")
        print(f"  alive at end: {result.winws_alive_at_end}")
        
        # Effect proven status
        if result.strategy_effect_proven:
            print(f"\n{C.GREEN}✓ Доказано, что стратегия влияет на соединение{C.RESET}")
        else:
            print(f"\n{C.YELLOW}✗ Не доказано, что стратегия влияет на соединение{C.RESET}")
        
        # Restore warning if any
        if result.restore_warning:
            print(f"\n{C.YELLOW}Предупреждение при восстановлении:{C.RESET}")
            print(f"  {result.restore_warning}")
        
        if result.invalid_reason:
            print(f"\n{C.RED}Причина недействительности:{C.RESET}")
            print(f"  {result.invalid_reason}")
        
        print(f"\n{C.GREEN}Тест завершен.{C.RESET}\n")
        pause()
        
    except Exception as e:
        print(f"\n{C.RED}Ошибка при выполнении proof-of-effect теста:{C.RESET}")
        print(f"{e}\n")
        pause()


def tg_menu(ctx: AppContext) -> None:
    while True:
        clear()
        go = ctx.state.tg.get("go") or {}
        ru = ctx.state.tg.get("rust") or {}
        print(f"{C.MAGENTA}Меню TG WS Proxy{C.RESET}\n")
        print(f"{C.YELLOW}Go:{C.RESET} {'установлен' if go.get('path') else 'не установлен'} pid={go.get('pid') or '-'}")
        print(f"{C.YELLOW}Rust:{C.RESET} {'установлен' if ru.get('path') else 'не установлен'} pid={ru.get('pid') or '-'}\n")
        print(f"{C.CYAN}1){C.RESET} {C.GREEN}Установить / Удалить TG WS Proxy Go{C.RESET}")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}Установить / Удалить TG WS Proxy Rust{C.RESET}")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}Старт/Стоп Go{C.RESET}")
        print(f"{C.CYAN}4){C.RESET} {C.GREEN}Старт/Стоп Rust{C.RESET}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        try:
            if c == "1":
                if go.get("path"):
                    uninstall_go(ctx)
                    print(f"\n{C.GREEN}Удалено.{C.RESET}\n")
                else:
                    p = install_go(ctx)
                    print(f"\n{C.GREEN}Установлено:{C.RESET} {p}\nsha256={ctx.state.tg.get('go',{}).get('sha256')}\n")
                pause()
            elif c == "2":
                if ru.get("path"):
                    uninstall_rust(ctx)
                    print(f"\n{C.GREEN}Удалено.{C.RESET}\n")
                else:
                    p = install_rust(ctx)
                    print(f"\n{C.GREEN}Установлено:{C.RESET} {p}\nsha256={ctx.state.tg.get('rust',{}).get('sha256')}\n")
                pause()
            elif c == "3":
                if go.get("pid"):
                    stop_go(ctx)
                else:
                    start_go(ctx)
                pause()
            elif c == "4":
                if ru.get("pid"):
                    stop_rust(ctx)
                else:
                    host = ask("host (Enter=0.0.0.0): ").strip() or "0.0.0.0"
                    port_s = ask("port (Enter=2443): ").strip() or "2443"
                    secret = ask("secret (optional): ").strip() or None
                    start_rust(ctx, host=host, port=int(port_s), secret=secret)
                pause()
        except Exception as e:
            log.exception("tg_menu failed")
            print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
            pause()


def system_menu(ctx: AppContext) -> None:
    while True:
        clear()
        print(f"{C.MAGENTA}Системное меню{C.RESET}\n")
        print(f"{C.CYAN}1){C.RESET} {C.GREEN}Runtime / Blockcheck / Diagnostics{C.RESET}")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}Upstreams (обновления стратегий){C.RESET}")
        print(f"{C.CYAN}A){C.RESET} {C.GREEN}DedZapret App Update (самообновление){C.RESET}")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}Network (QUIC / TCP timestamps / Flush DNS){C.RESET}")
        print(f"{C.CYAN}4){C.RESET} {C.GREEN}Backup / Restore{C.RESET}")
        print(f"{C.CYAN}5){C.RESET} {C.GREEN}Системная информация{C.RESET}")
        print(f"{C.CYAN}S){C.RESET} {C.GREEN}Support: Generate bug report{C.RESET}")
        print(f"{C.CYAN}X){C.RESET} {C.GREEN}Support: Сформировать диагностические артефакты{C.RESET}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        try:
            if c == "1":
                _runtime_menu(ctx)
            elif c == "2":
                _upstreams_menu(ctx)
            elif c.lower() == "a":
                _app_update_menu(ctx)
            elif c == "3":
                _network_menu(ctx)
            elif c == "4":
                _backup_menu(ctx)
            elif c == "5":
                clear()
                print("\n" + system_info_text(ctx) + "\n")
                pause()
            elif c.lower() == "s":
                _support_generate_bug_report(ctx)
            elif c.lower() == "x":
                _support_generate_diagnostics_artifacts(ctx)
        except Exception as e:
            log.exception("system_menu failed")
            print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
            pause()


@menu_handler("support.generate_bug_report")
def _support_generate_bug_report(ctx: AppContext) -> None:
    """Generate a masked bug report zip without leaking secrets."""
    clear()
    print(f"{C.MAGENTA}Support: Generate bug report{C.RESET}\n")
    print("Будет создан zip-архив с логами/диагностикой/состоянием.")
    print(f"{C.YELLOW}Важно:{C.RESET} секреты маскируются (UUID, пароли, приватные ключи, ссылки).\n")
    ans = ask("Создать bug report? (Y/n): ").strip().lower()
    if ans not in {"", "y", "yes"}:
        return

    cur_path = (ctx.paths.data_dir / "state" / "current.json").resolve()
    load_current_state(cur_path)  # ensure file exists

    res = cmd_create_bug_report(ctx)
    if res.ok:
        out = (res.details or {}).get("zip_path")
        safe_print(f"\n{C.GREEN}Bug report создан:{C.RESET} {out}\n")
        extras = (res.details or {}).get("extras")
        if isinstance(extras, list) and extras:
            safe_print("Included extra files:")
            for p in extras:
                safe_print(f"- {p}")
            safe_print("\n")
        if res.warnings:
            safe_print(f"{C.YELLOW}Предупреждения:{C.RESET}")
            for w in res.warnings:
                safe_print(f"- {w}")
            safe_print("\n")
    else:
        safe_print(f"\n{C.RED}{res.message}{C.RESET}\n")
        for e in res.errors:
            safe_print(f"- {e}")
        safe_print("\n")
    pause()


@menu_handler("support.generate_diagnostics_artifacts")
def _support_generate_diagnostics_artifacts(ctx: AppContext) -> None:
    """Create diagnostics artifacts into DedZapretData/data/diagnostics."""
    clear()
    print(f"{C.MAGENTA}Support: Диагностические артефакты{C.RESET}\n")
    print("Будут созданы небольшие summary файлы (best-effort), без сетевых операций.")
    print("Папка: DedZapretData/data/diagnostics\n")
    ans = ask("Сформировать артефакты? (Y/n): ").strip().lower()
    if ans not in {"", "y", "yes"}:
        return
    r = cmd_generate_diagnostics_artifacts(ctx)
    if r.ok:
        safe_print(f"\n{C.GREEN}Готово.{C.RESET}\n")
        for p in (r.details or {}).get("created_files", []) or []:
            safe_print(f"- {p}")
        if r.warnings:
            safe_print(f"\n{C.YELLOW}Ошибки (best-effort, не критично):{C.RESET}")
            for w in r.warnings:
                safe_print(f"- {w}")
        safe_print("\n")
    else:
        safe_print(f"\n{C.RED}{r.message}{C.RESET}\n")
        for e in r.errors:
            safe_print(f"- {e}")
        safe_print("\n")
    pause()



def _app_update_menu(ctx: AppContext) -> None:
    while True:
        clear()
        from app.zapret_manager import __version__

        print(f"{C.MAGENTA}DedZapret App Update (самообновление){C.RESET}\n")
        print(f"{C.YELLOW}Текущая версия:{C.RESET} {__version__}\n")
        print(f"{C.CYAN}1){C.RESET} {C.GREEN}Check app updates (latest release){C.RESET}")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}Download & install latest portable release{C.RESET}")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}Открыть update.log{C.RESET}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        try:
            if c == "1":
                plan = build_update_plan(ctx)
                print(f"\n{C.GREEN}Latest:{C.RESET} {plan.latest_tag}")
                print(f"{C.GREEN}Asset:{C.RESET} {plan.asset.name} ({plan.asset.size} bytes)")
                print(f"{C.GREEN}Repo:{C.RESET} {plan.repo}\n")
                pause()
            elif c == "2":
                ans = ask("\nНачать обновление? Будет создан backup DedZapretData. (Y/n): ").strip().lower()
                if ans not in {"", "y", "yes"}:
                    continue
                run_update(ctx)
                # updater.bat will run in background. user can close app.
                pause("\nНажми Enter чтобы вернуться в меню (обновление уже запущено)... ")
            elif c == "3":
                p = (ctx.paths.logs_dir / "update.log").resolve()
                if not p.exists():
                    print(f"\n{C.YELLOW}Лог обновления ещё не создан:{C.RESET} {p}\n")
                else:
                    print("\n" + p.read_text(encoding="utf-8", errors="replace") + "\n")
                pause()
        except AppUpdateError as e:
            print(f"\n{C.RED}Update error:{C.RESET} {e}\n")
            pause()
        except Exception as e:
            log.exception("app_update_menu failed")
            print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
            pause()


def _runtime_menu(ctx: AppContext) -> None:
    while True:
        clear()
        print(f"{C.MAGENTA}Runtime / Blockcheck / Diagnostics{C.RESET}\n")
        h = runtime_health(ctx)
        ok = bool(h.get("ok"))
        print(f"{C.YELLOW}Runtime:{C.RESET} " + (f"{C.GREEN}OK{C.RESET}" if ok else f"{C.RED}MISSING/BROKEN{C.RESET}"))
        diag_on = bool(getattr(ctx.config, "diagnostics", None) and ctx.config.diagnostics.enabled)
        print(f"{C.YELLOW}Diagnostics:{C.RESET} " + (f"{C.GREEN}ON{C.RESET}" if diag_on else f"{C.DIM}OFF{C.RESET}") + "\n")
        print(f"{C.CYAN}1){C.RESET} {C.GREEN}Показать runtime diagnostics{C.RESET}")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}Запустить blockcheck{C.RESET}")
        print(f"{C.CYAN}R){C.RESET} {C.GREEN}Repair runtime assets (lists + fake){C.RESET}")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}Запустить blockcheck2{C.RESET}")
        print(f"{C.CYAN}4){C.RESET} {C.GREEN}Toggle Diagnostics (в config.yaml){C.RESET}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        if c == "1":
            clear()
            print(runtime_diagnostics_text(ctx))
            pause()
        elif c == "2":
            run_blockcheck(ctx, variant="1")
        elif c.lower() == "r":

            items = repair_runtime_assets(ctx)
            clear()
            print(f"{C.MAGENTA}Repair runtime assets{C.RESET}\n")
            for it in items:
                color = C.GREEN if it.status in {"OK", "CREATED", "COPIED"} else C.RED
                print(f"- {color}{it.status}{C.RESET} {it.name} {C.DIM}{it.details}{C.RESET}")
            pause()
        elif c == "4":
            _toggle_diagnostics_in_config(ctx)
            pause()


def _upstreams_menu(ctx: AppContext) -> None:
    while True:
        clear()
        print(f"{C.MAGENTA}Upstreams (обновления){C.RESET}\n")
        print(f"{C.CYAN}1){C.RESET} {C.GREEN}Проверить обновления upstream{C.RESET}")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}Sync Flowseal{C.RESET}")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}Sync StressOzz{C.RESET}")
        print(f"{C.CYAN}4){C.RESET} {C.GREEN}Sync оба (Flowseal + StressOzz){C.RESET}")
        print(f"{C.CYAN}5){C.RESET} {C.GREEN}Обновить exclude + RKN list{C.RESET}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        if c == "1":
            res = check_updates(ctx)
            print()
            for name, (changed, msg) in res.items():
                flag = f"{C.GREEN}update{C.RESET}" if changed else f"{C.DIM}ok{C.RESET}"
                print(f"- {name}: {flag} ({msg})")
            print()
            pause()
        elif c == "2":
            print(f"\n{C.MAGENTA}Sync Flowseal...{C.RESET}")
            sync_flowseal(ctx)
            print(f"\n{C.GREEN}Готово.{C.RESET}\n")
            pause()
        elif c == "3":
            print(f"\n{C.MAGENTA}Sync StressOzz...{C.RESET}")
            sync_stressozz_strategies(ctx)
            print(f"\n{C.GREEN}Готово.{C.RESET}\n")
            pause()
        elif c == "4":
            print(f"\n{C.MAGENTA}Sync Flowseal...{C.RESET}")
            sync_flowseal(ctx)
            print(f"{C.MAGENTA}Sync StressOzz...{C.RESET}")
            sync_stressozz_strategies(ctx)
            print(f"\n{C.GREEN}Готово.{C.RESET}\n")
            pause()
        elif c == "5":
            p1 = update_exclude(ctx)
            p2 = update_rkn(ctx)
            print(f"\n{C.GREEN}OK:{C.RESET} {p1}\n{C.GREEN}OK:{C.RESET} {p2}\n")
            pause()


def _network_menu(ctx: AppContext) -> None:
    while True:
        clear()
        print(f"{C.MAGENTA}Network{C.RESET}\n")
        print(f"{C.YELLOW}QUIC block:{C.RESET} {'on' if quic_rule_exists() else 'off'}\n")
        print(f"{C.YELLOW}TCP timestamps:{C.RESET} {show_tcp_timestamp_status()}")
        print()
        print(f"{C.CYAN}1){C.RESET} {C.GREEN}Вкл/выкл блокировку QUIC (UDP 443){C.RESET}")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}TCP timestamps: enabled{C.RESET}")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}TCP timestamps: disabled{C.RESET}")
        print(f"{C.CYAN}4){C.RESET} {C.GREEN}Flush DNS{C.RESET}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        if c == "1":
            if quic_rule_exists():
                quic_block_disable()
            else:
                quic_block_enable()
            pause()
        elif c == "2":
            tcp_timestamps_enable()
            pause()
        elif c == "3":
            tcp_timestamps_disable()
            pause()
        elif c == "4":
            flush_dns()
            pause()


def _backup_menu(ctx: AppContext) -> None:
    while True:
        clear()
        print(f"{C.MAGENTA}Backup / Restore{C.RESET}\n")
        print(f"{C.CYAN}1){C.RESET} {C.GREEN}Бэкап (zip){C.RESET}")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}Восстановить из бэкапа (zip){C.RESET}")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}Автонастройка «под ключ» (без переустановки){C.RESET}")
        print(f"{C.CYAN}4){C.RESET} {C.GREEN}Под ключ + полная проверка/подбор (мастер){C.RESET}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        if c == "1":
            p = backup(ctx)
            print(f"\n{C.GREEN}Бэкап создан:{C.RESET} {p}\n")
            pause()
        elif c == "2":
            p = ask("\nПуть к zip бэкапу: ").strip()
            if p:
                restore(ctx, Path(p))
                print(f"\n{C.GREEN}Восстановлено.{C.RESET}\n")
                pause()
        elif c == "3":
            lines = key_setup(ctx)
            print()
            for ln in lines:
                print(ln)
            print()
            pause()
        elif c == "4":
            lines = key_setup_full_check(ctx)
            print()
            for ln in lines:
                print(ln)
            print()
            pause()


def _toggle_diagnostics_in_config(ctx: AppContext) -> None:
    """Toggle diagnostics.enabled in DedZapretData/config.yaml.

    Note: diagnostics session recorder is created at bootstrap, so this takes
    effect after restart.
    """
    p = ctx.paths.config_file
    data = {}
    if p.exists():
        data = yaml.safe_load(p.read_text(encoding="utf-8", errors="replace")) or {}
    diag = data.get("diagnostics") if isinstance(data, dict) else None
    if not isinstance(diag, dict):
        diag = {}
        if isinstance(data, dict):
            data["diagnostics"] = diag
    cur = bool(diag.get("enabled", False))
    diag["enabled"] = not cur
    p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    state = "ON" if diag["enabled"] else "OFF"
    print(f"\n{C.GREEN}Diagnostics теперь: {state}{C.RESET}")
    print(f"{C.YELLOW}Важно:{C.RESET} вступит в силу после перезапуска DedZapret.\n")


def _restart_if_running(ctx: AppContext) -> None:
    if not ctx.state.zapret.running:
        return
    base = find_strategy(ctx, ctx.state.zapret.base_strategy, kind="base")
    if not base:
        return
    youtube = find_strategy(ctx, ctx.state.zapret.youtube_layer, kind="youtube")
    discord = find_strategy(ctx, ctx.state.zapret.discord_layer, kind="discord")
    stop_zapret(ctx)
    try:
        start_zapret_interactive(ctx, base, youtube=youtube, discord=discord)
    except WinwsStartError as e:
        # Preflight/validation errors should not crash the strategies menu.
        log.exception("winws start failed")
        clear()
        print(f"{C.RED}Стратегия не запустилась (preflight).{C.RESET}\n")
        # show first N lines to avoid a huge wall
        lines = [ln.strip() for ln in str(e).splitlines() if ln.strip()]
        if lines:
            print(f"{C.YELLOW}Причина:{C.RESET}")
            for ln in lines[:8]:
                print(f"- {ln}")
            if len(lines) > 8:
                print(f"{C.DIM}... ({len(lines) - 8} строк скрыто; подробности в log){C.RESET}")
        print("\nЧто сделать:")
        print(f"1) {C.GREEN}System → Runtime → R: Repair runtime assets{C.RESET}")
        print(f"2) {C.GREEN}Включить Games профиль, если стратегия требует игровых портов{C.RESET}")
        print(f"3) {C.GREEN}Sync Flowseal/StressOzz стратегий{C.RESET}\n")
        pause()


def game_launcher_menu(ctx: AppContext) -> None:
    """Меню запуска игр/программ с автозапуском winws."""
    while True:
        clear()
        profiles = list_profiles(ctx)
        print(f"{C.MAGENTA}Меню запуска игр / программ{C.RESET}\n")
        if not profiles:
            print(f"{C.YELLOW}Нет сохранённых профилей.{C.RESET}\n")
        else:
            for i, p in enumerate(profiles, start=1):
                print(f"{C.CYAN}{i}){C.RESET} {p.name} {C.DIM}({p.exe_path}) → {p.strategy_name}{C.RESET}")
        print(f"\n{C.CYAN}A){C.RESET} {C.GREEN}Добавить профиль{C.RESET}")
        print(f"{C.CYAN}D){C.RESET} {C.GREEN}Удалить профиль{C.RESET}")
        print(f"{C.CYAN}B){C.RESET} {C.GREEN}Сгенерировать .bat{C.RESET}")
        print(f"{C.CYAN}S){C.RESET} {C.GREEN}Сгенерировать ярлык .lnk{C.RESET}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        try:
            if c.lower() == "a":
                name = ask("Имя профиля: ").strip()
                exe = ask("Путь к .exe: ").strip()
                strat = ask("Имя стратегии (например v7): ").strip()
                if name and exe and strat:
                    add_profile(ctx, name, exe, strat)
                    print(f"\n{C.GREEN}Профиль добавлен.{C.RESET}\n")
                    pause()
            elif c.lower() == "d" and profiles:
                num = ask("Номер профиля для удаления: ").strip()
                if num.isdigit() and 1 <= int(num) <= len(profiles):
                    remove_profile(ctx, profiles[int(num) - 1].name)
                    print(f"\n{C.GREEN}Профиль удалён.{C.RESET}\n")
                    pause()
            elif c.lower() == "b" and profiles:
                num = ask("Номер профиля: ").strip()
                if num.isdigit() and 1 <= int(num) <= len(profiles):
                    p = profiles[int(num) - 1]
                    out = Path(ctx.paths.data_dir / f"{p.name}_launcher.bat")
                    generate_bat(ctx, p, out)
                    print(f"\n{C.GREEN}.bat создан:{C.RESET} {out}\n")
                    pause()
            elif c.lower() == "s" and profiles:
                num = ask("Номер профиля: ").strip()
                if num.isdigit() and 1 <= int(num) <= len(profiles):
                    p = profiles[int(num) - 1]
                    out = Path(ctx.paths.data_dir / f"{p.name}_launcher.lnk")
                    generate_shortcut(ctx, p, out)
                    print(f"\n{C.GREEN}Ярлык создан:{C.RESET} {out}\n")
                    pause()
            elif c.isdigit() and profiles:
                idx = int(c)
                if 1 <= idx <= len(profiles):
                    p = profiles[idx - 1]
                    print(f"\n{C.CYAN}Запуск {p.name}...{C.RESET}\n")
                    run_profile(ctx, p)
        except Exception as e:
            log.exception("game_launcher_menu failed")
            print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
            pause()


def pause(msg: str = "\nНажмите Enter...") -> None:
    """Simple pause with message."""
    ask(msg)


def doh_menu(ctx: AppContext) -> None:
    """DoH/DNS configuration menu."""
    print(f"{C.CYAN}Настройки DoH/DNS{C.RESET}\n")
    print(f"{C.CYAN}1){C.RESET} {C.GREEN}Статус DoH{C.RESET}")
    print(f"{C.CYAN}2){C.RESET} {C.GREEN}Выбрать профиль DoH{C.RESET}")
    print(f"{C.CYAN}3){C.RESET} {C.GREEN}Настроить DoH{C.RESET}")
    print(f"{C.CYAN}4){C.RESET} {C.GREEN}Отключить DoH{C.RESET}")
    print(f"{C.CYAN}5){C.RESET} {C.GREEN}Сбросить DNS кэш{C.RESET}")
    print(f"{C.CYAN}6){C.RESET} {C.GREEN}Восстановить hosts{C.RESET}")
    print(f"{C.CYAN}7){C.RESET} {C.GREEN}В главное меню{C.RESET}")
    
    choice = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
    if not choice:
        return
    
    try:
        if choice == "1":
            from app.zapret_manager.features.doh import get_status as get_doh_status
            status = get_doh_status(ctx)
            print(f"\n{C.YELLOW}Статус DoH:{C.RESET}")
            print(f"  Включен: {status.enabled}")
            print(f"  Профиль: {status.profile}")
            print(f"  PID: {status.pid}")
            print(f"  Адаптер: {status.adapter}")
            print(f"  Слушает: {status.listen}")
            pause()
        elif choice == "2":
            from app.zapret_manager.features.doh import select_profile
            select_profile(ctx)
        elif choice == "3":
            from app.zapret_manager.features.doh import set_profile
            set_profile(ctx)
        elif choice == "4":
            from app.zapret_manager.features.doh import stop_doh
            stop_doh(ctx)
        elif choice == "5":
            from app.zapret_manager.features.doh import reset_to_dhcp
            reset_to_dhcp(ctx)
        elif choice == "6":
            from app.zapret_manager.features.doh import flush_dns
            flush_dns(ctx)
        elif choice == "7":
            return
        else:
            print(f"\n{C.RED}Неверный выбор: {choice}{C.RESET}")
            pause()
    except Exception as e:
        log.exception("doh_menu failed")
        print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
        pause()


def _problem_domains_menu(ctx: AppContext) -> None:
    """Меню авто-подбора по проблемным доменам."""
    while True:
        clear()
        summary = problem_domains_summary(ctx)
        print(f"{C.MAGENTA}Авто-подбор по проблемным доменам{C.RESET}\n")
        print(summary)
        print()
        print(f"{C.CYAN}1){C.RESET} {C.GREEN}Запустить тест стратегий по проблемным доменам{C.RESET}")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}Добавить домен вручную{C.RESET}")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}Удалить домен (пометить как решённый){C.RESET}")
        print(f"{C.CYAN}4){C.RESET} {C.GREEN}Очистить все проблемные домены{C.RESET}")
        print(f"{C.CYAN}5){C.RESET} {C.GREEN}Авто-подбор TOP-5 стратегий по проблемным доменам{C.RESET}")
        print(f"{C.CYAN}6){C.RESET} {C.GREEN}Экспортировать summary (diagnostics){C.RESET}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        try:
            if c == "1":
                _auto_tune_by_problem_domains(ctx)
            elif c == "5":
                _auto_tune_top5_by_problem_domains(ctx)
            elif c == "2":
                domain = ask("Введите домен (например x.com): ").strip()
                if domain:
                    add_problem_domain(ctx, domain, error="manual", strategy="")
                    print(f"\n{C.GREEN}Домен добавлен.{C.RESET}\n")
                    pause()
            elif c == "3":
                domains = get_problem_domain_list(ctx)
                if not domains:
                    print(f"\n{C.YELLOW}Список пуст.{C.RESET}\n")
                    pause()
                    continue
                for i, d in enumerate(domains, start=1):
                    print(f"{i}) {d}")
                num = ask("\nНомер домена для удаления: ").strip()
                if num.isdigit():
                    idx = int(num) - 1
                    if 0 <= idx < len(domains):
                        remove_resolved_domain(ctx, domains[idx])
                        print(f"\n{C.GREEN}Домен удалён.{C.RESET}\n")
                        pause()
            elif c == "4":
                clear_problem_domains(ctx)
                print(f"\n{C.GREEN}Все проблемные домены очищены.{C.RESET}\n")
                pause()
            elif c == "6":
                paths = write_problem_domains_summary_artifacts(ctx)
                print(f"\n{C.GREEN}Готово:{C.RESET}")
                for p in paths:
                    print(f"- {p}")
                print()
                pause()
        except Exception as e:
            log.exception("problem_domains_menu failed")
            print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
            pause()


def _auto_tune_by_problem_domains(ctx: AppContext) -> None:
    """Run strategy tests only on problem domains."""
    domains = get_problem_domain_list(ctx)
    if not domains:
        print(f"\n{C.YELLOW}Нет проблемных доменов. Сначала запустите тесты (control test или proof-of-effect).{C.RESET}\n")
        pause()
        return

    # Convert domains to URLs
    urls = [f"https://{d}/" for d in domains]
    print(f"\n{C.MAGENTA}Авто-подбор стратегий по {len(domains)} проблемным доменам{C.RESET}\n")
    print(f"Домены: {', '.join(domains[:5])}{'...' if len(domains) > 5 else ''}\n")

    # Check if strategy is selected
    strategy_name = ctx.state.zapret.selected_strategy or ctx.state.zapret.base_strategy
    if not strategy_name:
        print(f"{C.YELLOW}Не выбрана стратегия. Выберите в меню 'Стратегии'.{C.RESET}\n")
        pause()
        return

    strategy = find_strategy(ctx, strategy_name, kind="base") or find_strategy(ctx, strategy_name)
    if not strategy:
        print(f"{C.RED}Стратегия '{strategy_name}' не найдена.{C.RESET}\n")
        pause()
        return

    # Run proof-of-effect test on problem domains
    print(f"Тестируем стратегию: {strategy.name}\n")
    mode = _choose_test_mode()
    try:
        result = proof_of_effect(ctx, strategy, urls, settle_s=1.5, parallel=6, mode=mode)
        # Display results
        print(f"\n{C.CYAN}{'domain':<25} {'baseline':<10} {'strategy':<10} {'effect':<12}{C.RESET}")
        print("-" * 70)
        for row in result.rows:
            baseline_status = "OK" if row.baseline_ok else "FAIL"
            strategy_status = "OK" if row.strategy_ok else "FAIL"
            print(f"{row.domain:<25} {baseline_status:<10} {strategy_status:<10} {row.effect:<12}")
        print("-" * 70)
        print(f"\n{C.MAGENTA}Сводка:{C.RESET}")
        print(f"  improved: {result.improved}")
        print(f"  already_ok: {result.already_ok}")
        print(f"  no_effect: {result.no_effect}")
        print(f"  worsened: {result.worsened}")
        if result.strategy_effect_proven:
            print(f"\n{C.GREEN}✓ Стратегия эффективна на проблемных доменах{C.RESET}")
        else:
            print(f"\n{C.YELLOW}✗ Стратегия не показала эффекта на проблемных доменах{C.RESET}")
        print(f"\n{C.GREEN}Тест завершён.{C.RESET}\n")
        pause()
    except Exception as e:
        print(f"\n{C.RED}Ошибка при выполнении теста:{C.RESET}")
        print(f"{e}\n")
        pause()


def _auto_tune_top5_by_problem_domains(ctx: AppContext) -> None:
    """Sweep strategy groups on problem domains, show TOP-5 and optionally apply."""
    from app.zapret_manager.features.runtime_assets import repair_runtime_assets
    from app.zapret_manager.features.zapret_runtime import WinwsStartError

    domains = get_problem_domain_list(ctx)
    if not domains:
        print(f"\n{C.YELLOW}Нет проблемных доменов. Сначала запусти Control test или Proof-of-effect.{C.RESET}\n")
        pause()
        return

    urls = [f"https://{d}/" for d in domains]
    mode = _choose_test_mode()

    clear()
    print(f"{C.MAGENTA}Авто-подбор TOP-5 по проблемным доменам{C.RESET}\n")
    print(f"Доменов: {len(domains)}")
    print(f"Режим: {mode}\n")

    print(f"{C.YELLOW}Группы стратегий:{C.RESET}")
    print(f"{C.CYAN}1){C.RESET} v (v1-v9)")
    print(f"{C.CYAN}2){C.RESET} flowseal")
    print(f"{C.CYAN}3){C.RESET} v + flowseal (all)")
    g = ask(f"\n{C.YELLOW}Выберите группу:{C.RESET} ").strip()
    group = "all"
    ensure_flowseal = True
    if g == "1":
        group = "v"
        ensure_flowseal = False
    elif g == "2":
        group = "flowseal"
        ensure_flowseal = True

    print(f"\n{C.MAGENTA}Запускаю sweep...{C.RESET}\n")
    try:
        summary = test_session(
            ctx,
            group=group,
            domains=urls,
            out_name=f"results_problem_domains_{group}.txt",
            top_n=5,
            parallel=8,
            ensure_runtime=True,
            ensure_flowseal=ensure_flowseal,
            ensure_stressozz=True,
            mode=mode,
        )
    except WinwsStartError as e:
        # Offer repair and retry
        print(f"\n{C.RED}Не удалось запустить winws (preflight).{C.RESET}\n{e}\n")
        ans = ask("Repair runtime assets и повторить? (Y/n): ").strip().lower()
        if ans not in {"", "y", "yes"}:
            pause()
            return
        items = repair_runtime_assets(ctx)
        print(f"\n{C.MAGENTA}Repair runtime assets{C.RESET}")
        for it in items:
            color = C.GREEN if it.status in {"OK", "CREATED", "COPIED"} else C.RED
            print(f"- {color}{it.status}{C.RESET} {it.name} {C.DIM}{it.details}{C.RESET}")
        print()
        pause("Enter чтобы повторить sweep...")
        summary = test_session(
            ctx,
            group=group,
            domains=urls,
            out_name=f"results_problem_domains_{group}.txt",
            top_n=5,
            parallel=8,
            ensure_runtime=True,
            ensure_flowseal=ensure_flowseal,
            ensure_stressozz=True,
            mode=mode,
        )

    ranked = sorted(
        summary.results,
        key=lambda r: (
            0 if r.status == "ok" else -1,
            r.ok,
            r.total,
            r.strategy,
        ),
        reverse=True,
    )
    ok_ranked = [r for r in ranked if r.status == "ok" and r.total > 0]
    invalid = [r for r in ranked if r.status != "ok"]

    top5 = ok_ranked[:5]
    clear()
    print(f"{C.MAGENTA}TOP-5 стратегии ({group}){C.RESET}\n")
    if not top5:
        print(f"{C.YELLOW}Нет валидных результатов (все INVALID или 0 доменов).{C.RESET}\n")
        if invalid:
            print(f"{C.RED}INVALID:{C.RESET}")
            for r in invalid[:10]:
                print(f"- {r.strategy}: {r.error}")
        pause()
        return

    for i, r in enumerate(top5, start=1):
        print(f"{C.CYAN}{i}){C.RESET} {C.GREEN}{r.strategy}{C.RESET} -> {r.summary_text()}")
    print(f"\n{C.DIM}Результаты: {summary.results_file}{C.RESET}")
    if summary.pinned:
        print(f"{C.DIM}Закреплено в custom: {len(summary.pinned)}{C.RESET}")

    ans = ask("\nПрименить стратегию из TOP-5? (1-5 / Enter=лучшую / N=нет): ").strip().lower()
    if ans in {"n", "no"}:
        return
    pick = 1
    if ans.isdigit():
        pick = int(ans)
    if pick < 1 or pick > len(top5):
        pick = 1
    best_name = top5[pick - 1].strategy
    base = find_strategy(ctx, best_name, kind="base") or find_strategy(ctx, best_name)
    if not base:
        print(f"\n{C.RED}Не нашёл стратегию:{C.RESET} {best_name}\n")
        pause()
        return
    ctx.state.zapret.base_strategy = base.name
    ctx.state.zapret.selected_strategy = base.name
    save_state(ctx.paths.state_file, ctx.state)
    try:
        stop_zapret(ctx)
        start_zapret_interactive(ctx, base)
        print(f"\n{C.GREEN}Применено и запущено:{C.RESET} {base.name}\n")
    except Exception as e:
        print(f"\n{C.RED}Не удалось запустить с выбранной стратегией:{C.RESET} {e}\n")
    pause()
