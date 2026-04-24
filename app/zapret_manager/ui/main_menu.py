from __future__ import annotations

import logging

from zapret_manager.core.app_context import AppContext
from zapret_manager.core.state import save_state
from zapret_manager.features.doh import PROFILES
from zapret_manager.features.system import quic_rule_exists
from zapret_manager.features.upstreams import sync_flowseal, sync_stressozz_strategies, sync_zapret_runtime
from zapret_manager.features.zapret_runtime import detect_runtime_files, start_zapret_interactive, stop_zapret, uninstall_runtime
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
from zapret_manager.features.key_setup import key_setup
from zapret_manager.utils.console import C, ask, clear, pause


log = logging.getLogger(__name__)


def _status_lines(ctx: AppContext) -> list[str]:
    detect_runtime_files(ctx)
    lines: list[str] = []
    if ctx.state.runtime.installed:
        lines.append(f"{C.YELLOW}Zapret runtime:{C.RESET} {C.GREEN}установлен{C.RESET}")
    else:
        lines.append(f"{C.YELLOW}Zapret runtime:{C.RESET} {C.RED}не установлен{C.RESET}")

    if ctx.state.zapret.running and ctx.state.zapret.pid:
        lines.append(f"{C.YELLOW}Zapret:{C.RESET} {C.GREEN}запущен{C.RESET} (pid={ctx.state.zapret.pid})")
    else:
        lines.append(f"{C.YELLOW}Zapret:{C.RESET} {C.RED}остановлен{C.RESET}")

    if ctx.state.zapret.selected_strategy:
        lines.append(f"{C.YELLOW}Стратегия:{C.RESET} {C.CYAN}{ctx.state.zapret.selected_strategy}{C.RESET}")
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
            f"║ {C.BLUE}wow Manager (Windows){C.RESET}         ║\n"
            "╚═══════════════════════════════╝\n"
            f" {C.DIM}v0.2.0{C.RESET}\n"
        )
        for ln in _status_lines(ctx):
            print(ln)
        print()

        # пункт 1: install/update/uninstall
        if ctx.state.runtime.installed:
            action1 = "Удалить"
        else:
            action1 = "Установить/Обновить"

        print(f"{C.CYAN}1){C.RESET} {C.GREEN}{action1}{C.RESET} Zapret runtime")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}Старт/Стоп{C.RESET} Zapret")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}Меню стратегий{C.RESET}")
        print(f"{C.CYAN}4){C.RESET} {C.GREEN}Меню тестирования стратегий{C.RESET}")
        print(f"{C.CYAN}5){C.RESET} {C.GREEN}Меню{C.RESET} TG WS Proxy")
        print(f"{C.CYAN}6){C.RESET} {C.GREEN}Меню{C_RESET} DNS over HTTPS")
        print(f"{C.CYAN}7){C.RESET} {C.GREEN}Меню настройки{C_RESET} Discord")
        print(f"{C.CYAN}8){C.RESET} {C.GREEN}Меню управления доменами в{C_RESET} hosts")
        print(f"{C.CYAN}9){C.RESET} {C.GREEN}Удалить → установить → настроить{C_RESET} (под ключ)")
        print(f"{C.CYAN}10){C.RESET} {C.GREEN}Запустить игру / программу{C_RESET}")
        print(f"{C.CYAN}0){C.RESET} {C.GREEN}Системное меню{C_RESET}")
        choice = ask(f"\n{C.CYAN}Enter){C.RESET} выход\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not choice:
            return 0

        try:
            if choice == "1":
                if ctx.state.runtime.installed:
                    stop_zapret(ctx)
                    uninstall_runtime(ctx)
                    print(f"\n{C.GREEN}Runtime удалён.{C.RESET}\n")
                    pause()
                else:
                    print(f"\n{C.MAGENTA}Скачиваем и устанавливаем runtime...{C.RESET}")
                    sync_zapret_runtime(ctx)
                    detect_runtime_files(ctx)
                    print(f"\n{C.GREEN}Runtime установлен.{C.RESET}\n")
                    pause()
            elif choice == "2":
                if ctx.state.zapret.running:
                    stop_zapret(ctx)
                    print(f"\n{C.GREEN}Zapret остановлен.{C.RESET}\n")
                    pause()
                else:
                    # Load selected strategy from generated/custom
                    st = _load_selected_strategy(ctx)
                    if not st:
                        print(f"\n{C.RED}Стратегия не выбрана. Зайди в меню стратегий (3).{C.RESET}\n")
                        pause()
                        continue
                    start_zapret_interactive(ctx, st)
                    print(f"\n{C.GREEN}Zapret запущен.{C.RESET}\n")
                    pause()
            elif choice == "3":
                strategies_menu(ctx)
            elif choice == "4":
                test_menu(ctx)
            elif choice == "5":
                tg_menu(ctx)
            elif choice == "6":
                doh_menu(ctx)
            elif choice == "7":
                discord_menu(ctx)
            elif choice == "8":
                hosts_menu(ctx)
            elif choice == "10":
                game_launcher_menu(ctx)
            elif choice == "0":
                system_menu(ctx)
            elif choice == "9":
                lines = key_setup(ctx)
                print()
                for line in lines:
                    print(line)
                print()
                pause()
            elif choice == "888":
                # Hidden: полный сброс и переустановка
                _hidden_888(ctx)
            else:
                continue
        except Exception as e:
            log.exception("menu action failed")
            print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
            pause()


def _load_selected_strategy(ctx: AppContext):
    name = (ctx.state.zapret.selected_strategy or "").strip()
    if not name:
        return None
    for st in (
        list_strategies(ctx.paths.strategies_builtin_dir)
        + list_strategies(ctx.paths.strategies_generated_dir)
        + list_strategies(ctx.paths.strategies_custom_dir)
    ):
        if st.name == name:
            return st
    return None


def _hidden_888(ctx: AppContext) -> None:
    """Скрытый пункт 888: удалить → установить → настроить под ключ."""
    print(f"\n{C.MAGENTA}Полный сброс и переустановка...{C.RESET}\n")
    try:
        stop_zapret(ctx)
        uninstall_runtime(ctx)
    except Exception:
        pass
    sync_zapret_runtime(ctx)
    detect_runtime_files(ctx)
    sync_flowseal(ctx)
    sync_stressozz_strategies(ctx)
    # Применить стратегию v7 по умолчанию
    from zapret_manager.features.selection import find_strategy
    st = find_strategy(ctx, "v7", kind="base")
    if st:
        ctx.state.zapret.base_strategy = st.name
        ctx.state.zapret.selected_strategy = st.name
        save_state(ctx.paths.state_file, ctx.state)
        start_zapret_interactive(ctx, st)
    print(f"\n{C.GREEN}Готово. wow настроен под ключ.{C.RESET}\n")
    pause()
