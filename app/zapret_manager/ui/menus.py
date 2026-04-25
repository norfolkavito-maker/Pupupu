from __future__ import annotations

import logging
from pathlib import Path

from zapret_manager.core.app_context import AppContext
from zapret_manager.core.state import save_state
from zapret_manager.features.blockcheck import run_blockcheck
from zapret_manager.features.key_setup import key_setup
from zapret_manager.features.lists import update_exclude, update_rkn
from zapret_manager.features.selection import find_strategy, list_bases, list_layers
from zapret_manager.features.strategy_test import (
    DEFAULT_TEST_DOMAINS,
    TestResult,
    control_test,
    test_strategy,
    test_session,
    write_results,
)
from zapret_manager.features.sysinfo import system_info_text
from zapret_manager.features.system import (
    backup,
    flush_dns,
    quic_block_disable,
    quic_block_enable,
    quic_rule_exists,
    restore,
    tcp_timestamps_disable,
    tcp_timestamps_enable,
)
from zapret_manager.features.tg_proxy import (
    install_go,
    install_rust,
    start_go,
    start_rust,
    stop_go,
    stop_rust,
    uninstall_go,
    uninstall_rust,
)
from zapret_manager.features.upstreams import (
    check_updates,
    sync_flowseal,
    sync_stressozz_strategies,
    sync_zapret_runtime,
)
from zapret_manager.features.hosts import (
    finland_discord_block,
    load_blocks_from_file,
    reset_hosts_windows,
    set_block_enabled,
    has_block,
    clear_all_manager_blocks,
)
from zapret_manager.features.zapret_runtime import start_zapret_interactive, stop_zapret
from zapret_manager.features.test_urls import prepare_urls
from zapret_manager.utils.console import C, ask, clear, pause

from zapret_manager.features.doh import PROFILES, start_doh, stop_doh
from zapret_manager.features.game_launcher import (
    add_profile,
    generate_bat,
    generate_shortcut,
    list_profiles,
    remove_profile,
    run_profile,
)


log = logging.getLogger(__name__)


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
        base = ctx.state.zapret.base_strategy or "-"
        yv = ctx.state.zapret.youtube_layer or "-"
        dv = ctx.state.zapret.discord_layer or "-"
        rkn = "ON" if ctx.state.zapret.rkn_enabled else "OFF"
        gv = ctx.state.zapret.games_profile or "-"
        wss = "ON" if ctx.state.zapret.wssize_enabled else "OFF"
        print(f"{C.MAGENTA}Меню стратегий{C.RESET}\n")
        print(f"{C.YELLOW}Base:{C.RESET} {C.CYAN}{base}{C.RESET}")
        print(f"{C.YELLOW}YouTube:{C.RESET} {C.CYAN}{yv}{C.RESET}")
        print(f"{C.YELLOW}Discord:{C.RESET} {C.CYAN}{dv}{C.RESET}")
        print(f"{C.YELLOW}RKN:{C.RESET} {C.CYAN}{rkn}{C.RESET}")
        print(f"{C.YELLOW}Games:{C.RESET} {C.CYAN}{gv}{C.RESET}")
        print(f"{C.YELLOW}wssize:{C.RESET} {C.CYAN}{wss}{C.RESET}\n")

        print(f"{C.CYAN}1){C.RESET} {C.GREEN}Выбрать и установить стратегию v1-v9{C.RESET}")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}Выбрать и установить стратегию от Flowseal{C.RESET}")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}Выбрать и установить стратегию для YouTube{C.RESET}")
        print(f"{C.CYAN}4){C.RESET} {C.GREEN}Выбрать и установить стратегию для игр{C.RESET}")
        print(f"{C.CYAN}5){C.RESET} {C.GREEN}Включить / Выключить обход по спискам РКН{C.RESET}")
        print(f"{C.CYAN}6){C.RESET} {C.GREEN}Обновить список исключений{C.RESET}")
        print(f"{C.CYAN}7){C.RESET} {C.GREEN}Добавить / Удалить блок с --wssize 1:6{C.RESET}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        try:
            if c == "1":
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
            else:
                continue
        except Exception as e:
            log.exception("strategies_menu failed")
            print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
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
        print(f"{C.MAGENTA}Меню тестирования стратегий{C.RESET}\n")
        print(f"{C.CYAN}1){C.RESET} {C.GREEN}Тестировать стратегии v{C.RESET}")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}Тестировать стратегии Flowseal{C.RESET}")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}Тестировать v и Flowseal стратегии{C.RESET}")
        print(f"{C.CYAN}4){C.RESET} {C.GREEN}Тестировать текущую стратегию{C.RESET}")
        print(f"{C.CYAN}5){C.RESET} {C.GREEN}Тестировать стратегии по домену{C.RESET}")
        print(f"{C.CYAN}6){C.RESET} {C.GREEN}Тестировать стратегии для YouTube{C.RESET}")
        if have_results:
            print(f"{C.CYAN}9){C.RESET} {C.GREEN}Результаты тестирования стратегий{C.RESET}")
            print(f"{C.CYAN}0){C.RESET} {C.GREEN}Удалить результаты тестирования{C.RESET}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        try:
            if c == "1":
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
            elif c == "9" and have_results:
                _show_results(ctx)
            elif c == "0" and have_results:
                for p in ctx.paths.results_dir.glob("results_*.txt"):
                    p.unlink(missing_ok=True)  # type: ignore[arg-type]
                print(f"\n{C.GREEN}Удалено.{C.RESET}\n")
                pause()
        except Exception as e:
            log.exception("test_menu failed")
            print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
            pause()


def _bases_v(ctx: AppContext):
    return [b for b in list_bases(ctx) if b.name.lower().startswith("v") and b.name[1:].isdigit()]


def _bases_flowseal(ctx: AppContext):
    return [b for b in list_bases(ctx) if (b.upstream or "").lower() == "flowseal"]


def _run_test_group(ctx: AppContext, *, group: str) -> None:
    urls = prepare_urls(include_suite=True)
    domains = [u.url for u in urls]
    parallel = 8
    results: list[TestResult] = [control_test(domains, parallel=parallel)]

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
        ensure_runtime=True,
        ensure_flowseal=ensure_flowseal,
        ensure_stressozz=True,
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
        raise RuntimeError("Базовая стратегия не выбрана.")
    domains = [u.url for u in prepare_urls(include_suite=True)]
    r = test_strategy(ctx, base, domains, parallel=8)
    out = write_results(ctx, [r], "results_current.txt")
    print(f"\n{C.GREEN}Результат:{C.RESET} {r.ok}/{r.total}\n{C.DIM}{out}{C.RESET}\n")
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
    results: list[TestResult] = [control_test(domains, parallel=8)]
    strategies = _bases_v(ctx) + _bases_flowseal(ctx)
    if not strategies:
        raise RuntimeError("Стратегий нет. Сделай sync.")
    for st in strategies:
        print(f"\n{C.CYAN}Тест:{C.RESET} {st.name}")
        results.append(test_strategy(ctx, st, domains, parallel=8))
    out = write_results(ctx, results, "results_domain.txt")
    print(f"\n{C.GREEN}Готово:{C.RESET} {out}\n")
    pause()


def _youtube_auto_test(ctx: AppContext) -> None:
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
        r = test_strategy(ctx, base, DEFAULT_TEST_DOMAINS, parallel=4)
        print(f"{C.YELLOW}Результат:{C.RESET} {r.ok}/{r.total}")
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
        print(f"{C.YELLOW}QUIC block:{C.RESET} {'on' if quic_rule_exists() else 'off'}\n")
        print(f"{C.CYAN}1){C.RESET} {C.GREEN}Системная информация{C.RESET}")
        print(f"{C.CYAN}2){C.RESET} {C.GREEN}Проверить обновления upstream{C.RESET}")
        print(f"{C.CYAN}3){C.RESET} {C.GREEN}Применить обновления (sync runtime/стратегии){C.RESET}")
        print(f"{C.CYAN}4){C.RESET} {C.GREEN}Запустить blockcheck{C.RESET}")
        print(f"{C.CYAN}5){C.RESET} {C.GREEN}Запустить blockcheck2{C.RESET}")
        print(f"{C.CYAN}6){C.RESET} {C.GREEN}Вкл/выкл блокировку QUIC (UDP 443){C.RESET}")
        print(f"{C.CYAN}7){C.RESET} {C.GREEN}TCP timestamps: enabled{C.RESET}")
        print(f"{C.CYAN}8){C.RESET} {C.GREEN}TCP timestamps: disabled{C.RESET}")
        print(f"{C.CYAN}9){C.RESET} {C.GREEN}Flush DNS{C.RESET}")
        print(f"{C.CYAN}10){C.RESET} {C.GREEN}Бэкап (zip){C.RESET}")
        print(f"{C.CYAN}11){C.RESET} {C.GREEN}Восстановить из бэкапа (zip){C.RESET}")
        print(f"{C.CYAN}12){C.RESET} {C.GREEN}Обновить exclude + RKN list{C.RESET}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        try:
            if c == "1":
                print("\n" + system_info_text(ctx) + "\n")
                pause()
            elif c == "2":
                res = check_updates(ctx)
                print()
                for name, (changed, msg) in res.items():
                    flag = f"{C.GREEN}update{C.RESET}" if changed else f"{C.DIM}ok{C.RESET}"
                    print(f"- {name}: {flag} ({msg})")
                print()
                pause()
            elif c == "3":
                print(f"\n{C.MAGENTA}Sync runtime...{C.RESET}")
                sync_zapret_runtime(ctx)
                print(f"{C.MAGENTA}Sync Flowseal...{C.RESET}")
                sync_flowseal(ctx)
                print(f"{C.MAGENTA}Sync StressOzz...{C.RESET}")
                sync_stressozz_strategies(ctx)
                print(f"\n{C.GREEN}Готово.{C.RESET}\n")
                pause()
            elif c == "4":
                run_blockcheck(ctx, variant="1")
            elif c == "5":
                run_blockcheck(ctx, variant="2")
            elif c == "6":
                if quic_rule_exists():
                    quic_block_disable()
                else:
                    quic_block_enable()
                pause()
            elif c == "7":
                tcp_timestamps_enable()
                pause()
            elif c == "8":
                tcp_timestamps_disable()
                pause()
            elif c == "9":
                flush_dns()
                pause()
            elif c == "10":
                p = backup(ctx)
                print(f"\n{C.GREEN}Бэкап создан:{C.RESET} {p}\n")
                pause()
            elif c == "11":
                p = ask("\nПуть к zip бэкапу: ").strip()
                if p:
                    restore(ctx, Path(p))
                    print(f"\n{C.GREEN}Восстановлено.{C.RESET}\n")
                    pause()
            elif c == "12":
                p1 = update_exclude(ctx)
                p2 = update_rkn(ctx)
                print(f"\n{C.GREEN}OK:{C.RESET} {p1}\n{C.GREEN}OK:{C.RESET} {p2}\n")
                pause()
        except Exception as e:
            log.exception("system_menu failed")
            print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
            pause()


def _restart_if_running(ctx: AppContext) -> None:
    if not ctx.state.zapret.running:
        return
    base = find_strategy(ctx, ctx.state.zapret.base_strategy, kind="base")
    if not base:
        return
    youtube = find_strategy(ctx, ctx.state.zapret.youtube_layer, kind="youtube")
    discord = find_strategy(ctx, ctx.state.zapret.discord_layer, kind="discord")
    stop_zapret(ctx)
    start_zapret_interactive(ctx, base, youtube=youtube, discord=discord)


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


def doh_menu(ctx: AppContext) -> None:
    """Меню DNS over HTTPS."""
    while True:
        clear()
        print(f"{C.MAGENTA}Меню DNS over HTTPS{C.RESET}\n")
        print(f"{C.YELLOW}Статус:{C.RESET} {'ON' if ctx.state.doh.enabled else 'OFF'} ({ctx.state.doh.profile})\n")
        for i, (name, url) in enumerate(PROFILES.items(), start=1):
            mark = "*" if ctx.state.doh.profile == name and ctx.state.doh.enabled else " "
            print(f"{mark} {C.CYAN}{i}){C.RESET} {name} {C.DIM}({url}){C.RESET}")
        print(f"\n{C.CYAN}0){C.RESET} {C.GREEN}Сбросить DNS на DHCP{C.RESET}")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите профиль (1-{len(PROFILES)}) или 0 для сброса:{C.RESET} ").strip()
        if not c:
            return
        try:
            if c == "0":
                stop_doh(ctx)
                print(f"\n{C.GREEN}DNS сброшен на DHCP.{C.RESET}\n")
                pause()
            elif c.isdigit():
                idx = int(c)
                if 1 <= idx <= len(PROFILES):
                    profile_name = list(PROFILES.keys())[idx - 1]
                    if ctx.state.doh.enabled:
                        stop_doh(ctx)
                    start_doh(ctx, profile_name)
                    print(f"\n{C.GREEN}DoH запущен: {profile_name}{C.RESET}\n")
                    pause()
        except Exception as e:
            log.exception("doh_menu failed")
            print(f"\n{C.RED}Ошибка:{C.RESET} {e}\n")
            pause()

