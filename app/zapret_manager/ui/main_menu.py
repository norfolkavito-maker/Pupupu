from __future__ import annotations

import logging

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.state import save_state
from app.zapret_manager.features.system import quic_rule_exists
from app.zapret_manager.features.zapret_runtime import (
    detect_runtime_files,
    runtime_health,
    validate_strategy_assets,
    start_zapret_interactive,
    stop_zapret,
    WinwsStartError,
)
from app.zapret_manager.strategies.store import list_strategies
from app.zapret_manager.ui.menus import (
    auto_setup_menu,
    extras_menu,
    service_menu,
    strategies_menu,
    test_menu,
)
from app.zapret_manager.features.singbox_menu import singbox_menu
from app.zapret_manager.utils.console import C, ask, clear, pause
from app.zapret_manager import __version__


log = logging.getLogger(__name__)


def _offer_repair_and_retry_start(ctx: AppContext, st) -> bool:
    """If winws fails to start, offer runtime repair and a single retry.

    Returns True if successfully started after retry.
    """
    from app.zapret_manager.features.runtime_assets import repair_runtime_assets

    try:
        start_zapret_interactive(ctx, st)
        return True
    except WinwsStartError as e:
        clear()
        print(f"{C.RED}winws не запустился (preflight).{C.RESET}\n")
        print(str(e)[:1800])
        print()
        ans = ask("Repair runtime assets и повторить запуск? (Y/n): ").strip().lower()
        if ans not in {"", "y", "yes"}:
            return False
        items = repair_runtime_assets(ctx)
        clear()
        print(f"{C.MAGENTA}Repair runtime assets{C.RESET}\n")
        for it in items:
            color = C.GREEN if it.status in {"OK", "CREATED", "COPIED"} else C.RED
            print(f"- {color}{it.status}{C.RESET} {it.name} {C.DIM}{it.details}{C.RESET}")
        pause("\nEnter чтобы повторить запуск...")
        start_zapret_interactive(ctx, st)
        return True


def _startup_baseline_prompt(ctx: AppContext) -> None:
    """On first run (or when list is empty), offer baseline test without zapret."""
    try:
        from app.zapret_manager.features.problem_domains import load_problem_domains
        from app.zapret_manager.features.strategy_test import control_test_mode
        from app.zapret_manager.features.test_sets import DOMAIN_SETS, read_domain_set_file
    except Exception:
        return

    # Only when empty.
    if load_problem_domains(ctx):
        return

    clear()
    print(f"{C.MAGENTA}Первичная проверка доступности{C.RESET}\n")
    print("Список недоступных доменов ещё не собран.")
    print("Запустить быструю проверку без zapret?\n")
    print(f"{C.CYAN}1){C.RESET} Да, проверить популярные/все домены")
    print(f"{C.CYAN}2){C.RESET} Выбрать набор доменов")
    print(f"{C.CYAN}3){C.RESET} Пропустить")
    c = ask(f"\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
    if not c or c == "3":
        return

    # Baseline must be without zapret.
    try:
        stop_zapret(ctx)
    except Exception:
        pass

    # Pick domain set.
    domains: list[str] = []
    if c == "1":
        # default is a good baseline; 'all' would be too long for first run.
        ds = next((d for d in DOMAIN_SETS if d.key == "default"), DOMAIN_SETS[0])
        domains = read_domain_set_file(ds.file_path(ctx))
    elif c == "2":
        # Simple chooser inline (do not depend on ui.menus to avoid import loops)
        for i, ds in enumerate(DOMAIN_SETS, start=1):
            print(f"{i}) {ds.title}")
        s = ask(f"\n{C.YELLOW}Номер набора:{C.RESET} ").strip()
        if s.isdigit() and 1 <= int(s) <= len(DOMAIN_SETS):
            ds = DOMAIN_SETS[int(s) - 1]
            if ds.key == "all":
                # all is computed in test menu; keep first-run simple.
                ds = next((d for d in DOMAIN_SETS if d.key == "default"), DOMAIN_SETS[0])
            domains = read_domain_set_file(ds.file_path(ctx))

    if not domains:
        print(f"\n{C.YELLOW}Набор доменов пуст. Пропускаю baseline.{C.RESET}\n")
        pause()
        return

    print(f"\n{C.YELLOW}Режим проверки:{C.RESET}")
    print(f"{C.CYAN}1){C.RESET} Быстрая (рекомендуется)")
    print(f"{C.CYAN}2){C.RESET} Полная диагностика")
    mode = "quick" if ask(f"\n{C.YELLOW}Выберите режим:{C.RESET} ").strip() == "1" else "full"

    print(f"\n{C.MAGENTA}Baseline test (без zapret):{C.RESET} доменов={len(domains)}, mode={mode}\n")
    control_test_mode(ctx, domains, mode=mode, parallel=8, progress=True)
    print(f"\n{C.GREEN}Готово. Проблемные домены сохранены.{C.RESET}\n")
    pause()


def _status_lines(ctx: AppContext) -> list[str]:
    detect_runtime_files(ctx)
    lines: list[str] = []

    h = runtime_health(ctx)
    if h.get("core_ok"):
        lines.append(f"{C.YELLOW}Runtime(core):{C.RESET} {C.GREEN}OK{C.RESET}")
    else:
        lines.append(f"{C.YELLOW}Runtime(core):{C.RESET} {C.RED}MISSING/BROKEN{C.RESET}")

    zap = ctx.state.zapret
    zapret_state = (
        f"{C.GREEN}RUNNING{C.RESET} pid={zap.pid}" if zap.running and zap.pid else f"{C.RED}STOPPED{C.RESET}"
    )
    lines.append(f"{C.YELLOW}Zapret:{C.RESET} {zapret_state}")

    strategy = (zap.selected_strategy or zap.base_strategy or "").strip()
    if strategy:
        # assets preflight is helpful but can be slow; keep best-effort.
        assets = f"{C.DIM}n/a{C.RESET}"
        try:
            st = _load_selected_strategy(ctx)
            if st:
                probs = validate_strategy_assets(ctx, st)
                assets = f"{C.RED}BAD{C.RESET}" if probs else f"{C.GREEN}OK{C.RESET}"
        except Exception:
            pass
        lines.append(f"{C.YELLOW}Strategy:{C.RESET} {C.CYAN}{strategy}{C.RESET}  assets={assets}")
    else:
        lines.append(f"{C.YELLOW}Strategy:{C.RESET} {C.RED}NOT SET{C.RESET}")

    # Compact profiles
    extras: list[str] = []
    if zap.youtube_layer:
        extras.append(f"YT={zap.youtube_layer}")
    if zap.discord_layer:
        extras.append(f"DV={zap.discord_layer}")
    if zap.discord_script:
        extras.append(f"DS={zap.discord_script}")
    if zap.games_profile:
        extras.append(f"G={zap.games_profile}")
    if zap.rkn_enabled:
        extras.append("RKN")
    if zap.wssize_enabled:
        extras.append("WSSIZE")
    if extras:
        lines.append(f"{C.YELLOW}Layers:{C.RESET} {C.CYAN}{' '.join(extras)}{C.RESET}")

    if ctx.state.doh.enabled:
        lines.append(f"{C.YELLOW}DoH:{C.RESET} {C.GREEN}ON{C.RESET} ({ctx.state.doh.profile})")

    if quic_rule_exists():
        lines.append(f"{C.YELLOW}QUIC block:{C.RESET} {C.GREEN}ON{C.RESET}")

    # Problem domains quick indicator (non-fatal).
    try:
        from app.zapret_manager.features.problem_domains import load_problem_domains

        pd = load_problem_domains(ctx)
        if pd:
            lines.append(f"{C.YELLOW}Problem domains:{C.RESET} {C.CYAN}{len(pd)}{C.RESET}")
    except Exception:
        pass

    # sing-box status (best-effort; does not require binary to exist).
    try:
        from app.zapret_manager.core.current_state import load_current_state

        cur = load_current_state(ctx.paths.data_dir / "state" / "current.json")
        p = cur.processes.get("singbox")
        if p and p.running and p.pid:
            lines.append(f"{C.YELLOW}sing-box:{C.RESET} {C.GREEN}running{C.RESET} (pid={p.pid})")
        else:
            lines.append(f"{C.YELLOW}sing-box:{C.RESET} {C.DIM}stopped{C.RESET}")
    except Exception:
        # Do not spam; if file doesn't exist yet just skip.
        pass

    return lines


def _show_status_summary(ctx: AppContext) -> None:
    lines = _status_lines(ctx)
    for ln in lines:
        print(ln)
    print()


def run_main_menu(ctx: AppContext) -> int:
    """Simplified main menu with status-first approach."""
    # One-time baseline prompt before showing the main loop.
    try:
        _startup_baseline_prompt(ctx)
    except Exception:
        # Must never block startup.
        pass
    while True:
        clear()
        _show_status_summary(ctx)
        
        print(
            "╔═══════════════════════════╗\n"
            f"║ {C.BLUE}DEDZAPRET (Windows){C.RESET}            ║\n"
            "╚═══════════════════════════╝\n"
            f" {C.DIM}v{__version__}{C.RESET} {C.DIM}inspired by bol-van / StressOzz / Flowseal{C.RESET}\n"
        )
        
        # Simplified main menu - 11 core items
        print(f"{C.CYAN}1){C.RESET} {C.GREEN}Старт / Стоп{C.RESET}")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}Быстрый статус{C.RESET}")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}Стратегии{C.RESET}")
        print(f"{C.CYAN}4){C.RESET} {C.GREEN}Тест стратегий{C.RESET}")
        print(f"{C.CYAN}5){C.RESET} {C.GREEN}Ноды / sing-box{C.RESET}")
        print(f"{C.CYAN}6){C.RESET} {C.GREEN}DNS / hosts / системные настройки{C.RESET}")
        print(f"{C.CYAN}7){C.RESET} {C.GREEN}Диагностика и ремонт{C.RESET}")
        print(f"{C.CYAN}8){C.RESET} {C.GREEN}Логи и bug report{C.RESET}")
        print(f"{C.CYAN}9){C.RESET} {C.GREEN}Обновления{C.RESET}")
        print(f"{C.CYAN}10){C.RESET} {C.GREEN}Настройки{C.RESET}")
        print(f"{C.CYAN}11){C.RESET} {C.GREEN}Advanced / Dev tools{C.RESET}")
        
        choice = ask(f"\n{C.CYAN}Enter){C.RESET} выход\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not choice:
            return 0

        try:
            if choice == "1":
                if ctx.state.zapret.running:
                    stop_zapret(ctx)
                    print(f"\n{C.GREEN}Zapret остановлен.{C.RESET}\n")
                    pause()
                else:
                    st = _load_selected_strategy(ctx)
                    if not st:
                        st = _ask_strategy_before_start(ctx)
                    if not st:
                        continue
                    ok = _offer_repair_and_retry_start(ctx, st)
                    if not ok:
                        continue
                    print(f"\n{C.GREEN}Zapret запущен.{C.RESET}")
                    print(f"{C.YELLOW}Стратегия:{C.RESET} {st.name}\n")
                    pause()
            elif choice == "2":
                from app.zapret_manager.ui.menus import auto_setup_menu
                auto_setup_menu(ctx)
            elif choice == "3":
                strategies_menu(ctx)
            elif choice == "4":
                test_menu(ctx)
            elif choice == "5":
                from app.zapret_manager.ui.menus import singbox_menu
                singbox_menu(ctx)
            elif choice == "6":
                from app.zapret_manager.ui.menus import hosts_menu
                hosts_menu(ctx)
            elif choice == "7":
                from app.zapret_manager.ui.menus import diagnostics_menu
                diagnostics_menu(ctx)
            elif choice == "8":
                from app.zapret_manager.ui.menus import logs_menu
                logs_menu(ctx)
            elif choice == "9":
                from app.zapret_manager.ui.menus import updates_menu
                updates_menu(ctx)
            elif choice == "10":
                from app.zapret_manager.ui.menus import settings_menu
                settings_menu(ctx)
            elif choice == "11":
                from app.zapret_manager.ui.menus import advanced_menu
                advanced_menu(ctx)
            else:
                continue
        except Exception as e:
            log.exception("menu action failed")
            print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
            pause()


def _all_strategies(ctx: AppContext):
    return (
        list_strategies(ctx, ctx.paths.strategies_builtin_dir)
        + list_strategies(ctx, ctx.paths.strategies_generated_dir)
        + list_strategies(ctx, ctx.paths.strategies_custom_dir)
    )


def _load_selected_strategy(ctx: AppContext):
    name = (ctx.state.zapret.selected_strategy or ctx.state.zapret.base_strategy or "").strip()
    if not name:
        return None
    for st in _all_strategies(ctx):
        if st.name == name:
            return st
    return None


def _find_strategy_by_name(ctx: AppContext, name: str):
    for st in _all_strategies(ctx):
        if st.name.lower() == name.lower():
            return st
    return None


def _ask_strategy_before_start(ctx: AppContext):
    clear()
    print(f"{C.MAGENTA}Запуск Zapret{C.RESET}\n")
    print(f"{C.YELLOW}Активная стратегия не выбрана.{C.RESET}")
    print("Перед запуском нужно выбрать стратегию.\n")
    print(f"{C.CYAN}1){C.RESET} Использовать рекомендуемую base v9")
    print(f"{C.CYAN}2){C.RESET} Открыть меню стратегий")
    print(f"{C.CYAN}3){C.RESET} Показать доступные стратегии")
    c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
    if not c:
        return None
    if c == "1":
        st = _find_strategy_by_name(ctx, "v9")
        if not st:
            print(f"\n{C.RED}v9 не найдена. Сделай sync стратегий или выбери другую стратегию.{C.RESET}\n")
            pause()
            return None
        ctx.state.zapret.base_strategy = st.name
        ctx.state.zapret.selected_strategy = st.name
        save_state(ctx.paths.state_file, ctx.state)
        return st
    if c == "2":
        strategies_menu(ctx)
        return _load_selected_strategy(ctx)
    if c == "3":
        strategies = _all_strategies(ctx)
        if not strategies:
            print(f"\n{C.RED}Стратегий нет. Сделай sync в системном меню или меню тестов.{C.RESET}\n")
            pause()
            return None
        clear()
        print(f"{C.MAGENTA}Доступные стратегии{C.RESET}\n")
        for i, st in enumerate(strategies, start=1):
            print(f"{i:03d}) {st.name} {C.DIM}({st.kind}/{st.engine}){C.RESET}")
        s = ask(f"\n{C.YELLOW}Номер стратегии:{C.RESET} ").strip()
        if not s.isdigit():
            return None
        idx = int(s)
        if not (1 <= idx <= len(strategies)):
            return None
        st = strategies[idx - 1]
        ctx.state.zapret.base_strategy = st.name
        ctx.state.zapret.selected_strategy = st.name
        save_state(ctx.paths.state_file, ctx.state)
        return st
    return None


def _hidden_888(ctx: AppContext) -> None:
    """Reserved hidden menu slot (not used in portable mode)."""
    return
