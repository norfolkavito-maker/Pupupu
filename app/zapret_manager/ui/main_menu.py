from __future__ import annotations

import logging

from zapret_manager.core.app_context import AppContext
from zapret_manager.core.state import save_state
from zapret_manager.features.system import quic_rule_exists
from zapret_manager.features.zapret_runtime import (
    detect_runtime_files,
    runtime_health,
    start_zapret_interactive,
    stop_zapret,
)
from zapret_manager.strategies.store import list_strategies
from zapret_manager.ui.menus import (
    discord_menu,
    doh_menu,
    game_launcher_menu,
    hosts_menu,
    strategies_menu,
    system_menu,
    test_menu,
    tg_menu,
)
from zapret_manager.utils.console import C, ask, clear, pause
from zapret_manager import __version__


log = logging.getLogger(__name__)


def _status_lines(ctx: AppContext) -> list[str]:
    detect_runtime_files(ctx)
    lines: list[str] = []

    h = runtime_health(ctx)
    if h.get("ok"):
        lines.append(f"{C.YELLOW}Runtime:{C.RESET} {C.GREEN}OK{C.RESET}")
    else:
        lines.append(f"{C.YELLOW}Runtime:{C.RESET} {C.RED}MISSING/BROKEN{C.RESET}")

    if ctx.state.zapret.running and ctx.state.zapret.pid:
        lines.append(f"{C.YELLOW}Zapret:{C.RESET} {C.GREEN}запущен{C.RESET} (pid={ctx.state.zapret.pid})")
    else:
        lines.append(f"{C.YELLOW}Zapret:{C.RESET} {C.RED}остановлен{C.RESET}")

    strategy = ctx.state.zapret.selected_strategy or ctx.state.zapret.base_strategy
    if strategy:
        lines.append(f"{C.YELLOW}Стратегия:{C.RESET} {C.CYAN}{strategy}{C.RESET}")
    else:
        lines.append(f"{C.YELLOW}Стратегия:{C.RESET} {C.RED}не выбрана{C.RESET}")

    if ctx.state.zapret.discord_profile:
        lines.append(f"{C.YELLOW}Discord профиль:{C.RESET} {C.CYAN}{ctx.state.zapret.discord_profile}{C.RESET}")
    if ctx.state.zapret.games_profile:
        lines.append(f"{C.YELLOW}Games профиль:{C.RESET} {C.CYAN}{ctx.state.zapret.games_profile}{C.RESET}")

    if ctx.state.doh.enabled:
        lines.append(f"{C.YELLOW}DoH:{C.RESET} {C.GREEN}включен{C.RESET} ({ctx.state.doh.profile})")

    if quic_rule_exists():
        lines.append(f"{C.YELLOW}Блокировка QUIC:{C.RESET} {C.GREEN}включена{C.RESET}")

    return lines


def run_main_menu(ctx: AppContext) -> int:
    while True:
        clear()
        print(
            "╔═══════════════════════════════╗\n"
            f"║ {C.BLUE}DEDZAPRET (Windows){C.RESET}            ║\n"
            "╚═══════════════════════════════╝\n"
            f" {C.DIM}v{__version__}{C.RESET} {C.DIM}inspired by bol-van / StressOzz / Flowseal{C.RESET}\n"
        )
        for ln in _status_lines(ctx):
            print(ln)
        print()

        print(f"{C.CYAN}1){C.RESET} {C.GREEN}Старт/Стоп{C.RESET} Zapret")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}Меню стратегий{C.RESET}")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}Меню тестирования стратегий{C.RESET}")
        print(f"{C.CYAN}4){C.RESET} {C.GREEN}Меню{C.RESET} TG WS Proxy")
        print(f"{C.CYAN}5){C.RESET} {C.GREEN}Меню{C.RESET} DNS over HTTPS")
        print(f"{C.CYAN}6){C.RESET} {C.GREEN}Меню настройки{C.RESET} Discord")
        print(f"{C.CYAN}7){C.RESET} {C.GREEN}Меню управления доменами в{C.RESET} hosts")
        print(f"{C.CYAN}8){C.RESET} {C.GREEN}Запустить игру / программу{C.RESET}")
        print(f"{C.CYAN}0){C.RESET} {C.GREEN}Системное меню{C.RESET}")
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
                    start_zapret_interactive(ctx, st)
                    print(f"\n{C.GREEN}Zapret запущен.{C.RESET}")
                    print(f"{C.YELLOW}Стратегия:{C.RESET} {st.name}\n")
                    pause()
            elif choice == "2":
                strategies_menu(ctx)
            elif choice == "3":
                test_menu(ctx)
            elif choice == "4":
                tg_menu(ctx)
            elif choice == "5":
                doh_menu(ctx)
            elif choice == "6":
                discord_menu(ctx)
            elif choice == "7":
                hosts_menu(ctx)
            elif choice == "8":
                game_launcher_menu(ctx)
            elif choice == "0":
                system_menu(ctx)
            else:
                continue
        except Exception as e:
            log.exception("menu action failed")
            print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
            pause()


def _all_strategies(ctx: AppContext):
    return (
        list_strategies(ctx.paths.strategies_builtin_dir)
        + list_strategies(ctx.paths.strategies_generated_dir)
        + list_strategies(ctx.paths.strategies_custom_dir)
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
