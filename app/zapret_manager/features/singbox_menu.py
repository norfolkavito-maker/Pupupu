from __future__ import annotations

import logging
from pathlib import Path

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.current_state import load_current_state, save_current_state
from app.zapret_manager.core.menu_actions import menu_handler
from app.zapret_manager.core.process_supervisor import ProcessSupervisor
from app.zapret_manager.core.singbox.binary import detect_singbox_binary, singbox_version
from app.zapret_manager.core.singbox.config_builder import SingBoxBuildOptions, build_config, write_config
from app.zapret_manager.core.singbox.health import singbox_health_summary
from app.zapret_manager.core.singbox.nodes import import_node_from_link, load_nodes, save_nodes
from app.zapret_manager.core.singbox.subscriptions import (
    add_subscription,
    download_subscription_text,
    load_subscriptions,
    masked_subscription_label,
    merge_subscription_nodes,
    parse_subscription_payload,
    parse_subscription_payload_detailed,
    save_subscriptions,
)
from app.zapret_manager.core.singbox.system_proxy_win import (
    enable_local_proxy_with_backup,
    restore_system_proxy,
)
from app.zapret_manager.core.singbox.process import SingBoxProcess
from app.zapret_manager.features.singbox_health import build_singbox_health_report, format_singbox_health_text
from app.zapret_manager.ui.colors import C
from app.zapret_manager.utils.console import ask, clear, pause, safe_print


log = logging.getLogger(__name__)


def singbox_menu(ctx: AppContext) -> None:
    """Experimental sing-box local proxy menu (opt-in)."""
    while True:
        clear()
        cur_path = (ctx.paths.data_dir / "state" / "current.json").resolve()
        cur = load_current_state(cur_path)
        proc = cur.processes.get("singbox")
        running = bool(proc and proc.running)
        # short status line
        bin = detect_singbox_binary(ctx.paths.root)
        nodes_count = len(load_nodes(_nodes_path(ctx)))
        active_yes = "yes" if (cur.active_singbox_node_id or "").strip() else "no"
        installed = "installed" if bin else "missing"
        running_yes = "yes" if running else "no"

        print(f"{C.MAGENTA}sing-box (experimental, local proxy){C.RESET}\n")
        print(f"sing-box: {installed} | nodes: {nodes_count} | active: {active_yes} | running: {running_yes}\n")
        print(f"{C.YELLOW}Status:{C.RESET} {'RUNNING' if running else 'STOPPED'} pid={proc.pid if proc else '-'}")
        print(f"{C.YELLOW}Active node:{C.RESET} {cur.active_singbox_node_id or '-'}")
        print(f"{C.YELLOW}DNS mode:{C.RESET} {cur.singbox_dns_mode}\n")
        print(f"{C.CYAN}1){C.RESET} Диагностика sing-box / Health check")
        print(f"{C.CYAN}2){C.RESET} Status / diagnostics")
        print(f"{C.CYAN}3){C.RESET} Import single link (vless/vmess/trojan/ss)")
        print(f"{C.CYAN}4){C.RESET} Add subscription URL")
        print(f"{C.CYAN}5){C.RESET} Update subscriptions")
        print(f"{C.CYAN}6){C.RESET} List nodes")
        print(f"{C.CYAN}7){C.RESET} Select active node")
        print(f"{C.CYAN}8){C.RESET} Generate config preview")
        print(f"{C.CYAN}9){C.RESET} Start local proxy")
        print(f"{C.CYAN}10){C.RESET} Enable system proxy (explicit confirm)")
        print(f"{C.CYAN}11){C.RESET} Restore system proxy")
        print(f"{C.CYAN}12){C.RESET} Stop sing-box")
        print(f"{C.CYAN}13){C.RESET} Restart sing-box")
        c = ask(f"\n{C.CYAN}Enter){C.RESET} назад\n\n{C.YELLOW}Выберите пункт:{C.RESET} ").strip()
        if not c:
            return
        if c == "1":
            _sb_health_check(ctx)
        elif c == "2":
            _sb_status(ctx)
        elif c == "3":
            _sb_import_link(ctx)
        elif c == "4":
            _sb_add_subscription(ctx)
        elif c == "5":
            _sb_update_subscriptions(ctx)
        elif c == "6":
            _sb_list_nodes(ctx)
        elif c == "7":
            _sb_select_node(ctx)
        elif c == "8":
            _sb_preview_config(ctx)
        elif c == "9":
            _sb_start(ctx)
        elif c == "10":
            _sb_enable_system_proxy(ctx)
        elif c == "11":
            _sb_restore_system_proxy(ctx)
        elif c == "12":
            _sb_stop(ctx)
        elif c == "13":
            _sb_restart(ctx)


@menu_handler("singbox.health_check")
def _sb_health_check(ctx: AppContext) -> None:
    clear()
    rep = build_singbox_health_report(data_dir=ctx.paths.data_dir, root_dir=ctx.paths.root)
    safe_print("\n" + format_singbox_health_text(rep))
    pause()


@menu_handler("singbox.status")
def _sb_status(ctx: AppContext) -> None:
    clear()
    hs = singbox_health_summary((ctx.paths.data_dir / "state" / "current.json").resolve())
    bin = detect_singbox_binary(ctx.paths.root)
    if not bin:
        safe_print(f"\n{C.RED}sing-box.exe не найден.{C.RESET}\nОжидается: bin/sing-box/sing-box.exe\n")
        safe_print(f"Health: running={hs.get('running')} pid={hs.get('pid')} ports={hs.get('ports')}\n")
        pause()
        return
    v = singbox_version(bin.path)
    safe_print(f"\n{C.GREEN}sing-box found:{C.RESET} {bin.path}\n")
    safe_print(v + "\n")
    safe_print(f"Health: running={hs.get('running')} pid={hs.get('pid')} ports={hs.get('ports')} ok={hs.get('ok')}\n")
    pause()


def _nodes_path(ctx: AppContext) -> Path:
    return (ctx.paths.data_dir / "singbox" / "nodes.json").resolve()


def _config_path(ctx: AppContext) -> Path:
    return (ctx.paths.data_dir / "singbox" / "generated_config.json").resolve()


def _subscriptions_path(ctx: AppContext) -> Path:
    return (ctx.paths.data_dir / "singbox" / "subscriptions.json").resolve()


def _system_proxy_backup_path(ctx: AppContext) -> Path:
    return (ctx.paths.data_dir / "singbox" / "system_proxy_backup.json").resolve()


@menu_handler("singbox.enable_system_proxy")
def _sb_enable_system_proxy(ctx: AppContext) -> None:
    clear()
    ans = ask("\nВключить системный прокси 127.0.0.1:2081? (y/N): ").strip().lower()
    if ans not in {"y", "yes", "д", "да"}:
        return
    try:
        enable_local_proxy_with_backup(_system_proxy_backup_path(ctx), host="127.0.0.1", port=2081)
        safe_print(f"\n{C.GREEN}System proxy включен.{C.RESET}\n")
    except Exception as e:
        safe_print(f"\n{C.RED}Не удалось включить system proxy:{C.RESET} {e}\n")
    pause()


@menu_handler("singbox.restore_system_proxy")
def _sb_restore_system_proxy(ctx: AppContext) -> None:
    clear()
    try:
        restore_system_proxy(_system_proxy_backup_path(ctx))
        safe_print(f"\n{C.GREEN}System proxy восстановлен.{C.RESET}\n")
    except Exception as e:
        safe_print(f"\n{C.RED}Не удалось восстановить system proxy:{C.RESET} {e}\n")
    pause()


@menu_handler("singbox.add_subscription")
def _sb_add_subscription(ctx: AppContext) -> None:
    clear()
    name = ask("\nИмя подписки: ").strip()
    url = ask("URL подписки: ").strip()
    if not name or not url:
        return
    subs = load_subscriptions(_subscriptions_path(ctx))
    subs = add_subscription(subs, name=name, url=url)
    save_subscriptions(_subscriptions_path(ctx), subs)
    safe_print(f"\n{C.GREEN}Добавлено:{C.RESET} {name}\n")
    pause()


@menu_handler("singbox.update_subscriptions")
def _sb_update_subscriptions(ctx: AppContext) -> None:
    clear()
    subs = load_subscriptions(_subscriptions_path(ctx))
    if not subs:
        safe_print(f"\n{C.YELLOW}Нет подписок.{C.RESET}\n")
        pause()
        return

    nodes = load_nodes(_nodes_path(ctx))
    total_imported = 0
    total_skipped = 0
    total_errors = 0
    total_unsupported = 0
    updated: list = []

    cur_path = (ctx.paths.data_dir / "state" / "current.json").resolve()
    cur = load_current_state(cur_path)

    for s in subs:
        if not s.enabled:
            updated.append(s)
            continue
        try:
            txt = download_subscription_text(s.url)
            links, counters, last_err = parse_subscription_payload_detailed(txt)
            nodes, stats = merge_subscription_nodes(current_nodes=nodes, links=links)
            total_imported += stats.get("imported", 0)
            total_skipped += stats.get("skipped", 0)
            total_errors += stats.get("errors", 0)
            total_unsupported += counters.get("unsupported_lines", 0)
            if stats.get("imported", 0) == 0 and not links:
                # fully unsupported/empty payload
                raise RuntimeError(last_err or "unsupported subscription payload")
            updated.append(type(s)(
                subscription_id=s.subscription_id,
                name=s.name,
                url=s.url,
                enabled=s.enabled,
                last_update_at="ok",
                last_error="",
                node_count=len(links),
            ))
        except Exception as e:
            updated.append(type(s)(
                subscription_id=s.subscription_id,
                name=s.name,
                url=s.url,
                enabled=s.enabled,
                last_update_at=s.last_update_at,
                last_error=str(e),
                node_count=s.node_count,
            ))
            total_errors += 1

    save_nodes(_nodes_path(ctx), nodes)
    save_subscriptions(_subscriptions_path(ctx), updated)

    # Auto-select active node if empty and we imported anything.
    if total_imported > 0 and not (cur.active_singbox_node_id or "").strip():
        # pick the first node from the just-saved list
        if nodes:
            cur.active_singbox_node_id = nodes[0].node_id
            save_current_state(cur_path, cur)

    safe_print(f"\n{C.GREEN}Subscriptions updated.{C.RESET}")
    safe_print(
        f"Imported: {total_imported}, skipped: {total_skipped}, errors: {total_errors}, unsupported_lines: {total_unsupported}"
    )
    for s in updated:
        safe_print(f"- {masked_subscription_label(s)}")
    safe_print("")
    pause()


@menu_handler("singbox.import_link")
def _sb_import_link(ctx: AppContext) -> None:
    clear()
    link = ask("\nВставьте ссылку (vless/vmess/trojan/ss): ").strip()
    if not link:
        return
    if link.startswith("http://") or link.startswith("https://"):
        safe_print(
            "\nПохоже, это subscription URL, а не одиночная нода. "
            "Используй: Add subscription URL -> Update subscriptions.\n"
        )
        pause()
        return
    node = import_node_from_link(link)
    nodes = load_nodes(_nodes_path(ctx))
    nodes = [n for n in nodes if n.node_id != node.node_id] + [node]
    save_nodes(_nodes_path(ctx), nodes)
    safe_print(f"\n{C.GREEN}Импортировано:{C.RESET} {node.masked_summary()}\n")
    pause()


@menu_handler("singbox.list_nodes")
def _sb_list_nodes(ctx: AppContext) -> None:
    clear()
    nodes = load_nodes(_nodes_path(ctx))
    if not nodes:
        safe_print(f"\n{C.YELLOW}nodes.json пуст.{C.RESET}\n")
        pause()
        return
    safe_print(f"{C.MAGENTA}Nodes:{C.RESET}\n")
    for i, n in enumerate(nodes, start=1):
        safe_print(f"{i:02d}) {n.masked_summary()} id={n.node_id}")
    safe_print("\n")
    pause()


@menu_handler("singbox.select_node")
def _sb_select_node(ctx: AppContext) -> None:
    nodes = load_nodes(_nodes_path(ctx))
    if not nodes:
        safe_print(f"\n{C.YELLOW}Нет нод. Сначала импортируйте ссылку.{C.RESET}\n")
        pause()
        return
    clear()
    safe_print(f"{C.MAGENTA}Выбор active node{C.RESET}\n")
    for i, n in enumerate(nodes, start=1):
        safe_print(f"{i}) {n.masked_summary()}")
    s = ask("\nНомер: ").strip()
    if not s.isdigit():
        return
    idx = int(s)
    if not (1 <= idx <= len(nodes)):
        return
    cur_path = (ctx.paths.data_dir / "state" / "current.json").resolve()
    cur = load_current_state(cur_path)
    cur.active_singbox_node_id = nodes[idx - 1].node_id
    save_current_state(cur_path, cur)
    safe_print(f"\n{C.GREEN}Выбрано:{C.RESET} {nodes[idx - 1].masked_summary()}\n")
    pause()


def _active_node(ctx: AppContext):
    cur_path = (ctx.paths.data_dir / "state" / "current.json").resolve()
    cur = load_current_state(cur_path)
    nodes = load_nodes(_nodes_path(ctx))
    node = next((n for n in nodes if n.node_id == cur.active_singbox_node_id), None)
    return cur, node


@menu_handler("singbox.preview_config")
def _sb_preview_config(ctx: AppContext) -> None:
    clear()
    cur, node = _active_node(ctx)
    if not node:
        safe_print(f"\n{C.YELLOW}Active node не выбрана.{C.RESET}\n")
        pause()
        return
    opt = SingBoxBuildOptions(dns_mode=cur.singbox_dns_mode)
    cfg = build_config(node=node, opt=opt)
    txt = str(cfg)
    safe_print(f"{C.CYAN}Preview (python dict):{C.RESET}\n")
    safe_print(txt[:12000] + ("\n... <truncated>\n" if len(txt) > 12000 else "\n"))
    pause()


@menu_handler("singbox.start")
def _sb_start(ctx: AppContext) -> None:
    bin = detect_singbox_binary(ctx.paths.root)
    if not bin:
        raise RuntimeError("sing-box.exe не найден (ожидается bin/sing-box/sing-box.exe)")

    cur, node = _active_node(ctx)
    if not node:
        raise RuntimeError("Active node не выбрана")

    cfg_path = _config_path(ctx)
    opt = SingBoxBuildOptions(dns_mode=cur.singbox_dns_mode)
    cfg = build_config(node=node, opt=opt)
    write_config(cfg_path, cfg)

    sup = ProcessSupervisor(current_state_file=(ctx.paths.data_dir / "state" / "current.json").resolve())
    proc = SingBoxProcess(
        supervisor=sup,
        bin_path=bin.path,
        config_path=cfg_path,
        log_file=(ctx.paths.logs_dir / "singbox.log").resolve(),
    )
    pid = proc.start()
    safe_print(f"\n{C.GREEN}sing-box запущен:{C.RESET} pid={pid}\n")
    safe_print("Local proxy:")
    safe_print("- SOCKS: 127.0.0.1:2080")
    safe_print("- HTTP/mixed: 127.0.0.1:2081\n")
    pause()


@menu_handler("singbox.stop")
def _sb_stop(ctx: AppContext) -> None:
    cur_path = (ctx.paths.data_dir / "state" / "current.json").resolve()
    cur = load_current_state(cur_path)
    pid = None
    if cur.processes.get("singbox"):
        pid = cur.processes["singbox"].pid
    bin = detect_singbox_binary(ctx.paths.root)
    if not bin:
        # even if binary missing, clear state
        sup = ProcessSupervisor(current_state_file=cur_path)
        sup.set_process("singbox", pid=None, running=False)
        safe_print(f"\n{C.YELLOW}sing-box binary отсутствует, состояние очищено.{C.RESET}\n")
        pause()
        return
    sup = ProcessSupervisor(current_state_file=cur_path)
    proc = SingBoxProcess(
        supervisor=sup,
        bin_path=bin.path,
        config_path=_config_path(ctx),
        log_file=(ctx.paths.logs_dir / "singbox.log").resolve(),
    )
    proc.stop(pid)
    try:
        # rollback path: restore previous proxy settings if backup exists
        restore_system_proxy(_system_proxy_backup_path(ctx))
    except Exception:
        pass
    safe_print(f"\n{C.GREEN}sing-box остановлен.{C.RESET}\n")
    pause()


@menu_handler("singbox.restart")
def _sb_restart(ctx: AppContext) -> None:
    _sb_stop(ctx)
    _sb_start(ctx)
