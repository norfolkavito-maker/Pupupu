from __future__ import annotations

import os
import platform as _platform
import subprocess
import sys
from typing import Optional, Sequence

import logging


def _ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def is_windows() -> bool:
    return os.name == "nt" or _platform.system().lower() == "windows"


def is_admin() -> bool:
    if not is_windows():
        return False
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_self_as_admin() -> bool:
    """Try to re-launch current process elevated via UAC.

    Returns True if ShellExecuteW succeeded (process spawned). If user cancels
    UAC prompt, returns False.
    """
    if not is_windows():
        return False
    try:
        import ctypes

        frozen = bool(getattr(sys, "frozen", False))
        exe = sys.executable

        # Keep original args.
        # NOTE: ShellExecuteW expects a single command-line string.
        # For frozen exe: relaunch same exe with same argv.
        # For dev runs: we don't try to elevate python invocation because env
        # (venv/PYTHONPATH) may not be preserved. run.bat handles elevation.
        if frozen:
            params = " ".join(f'"{a}"' if " " in a else a for a in sys.argv[1:])
        else:
            return False
        # 32 is SW_SHOW
        rc = int(ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 32))
        # rc <= 32 indicates error. In some cases cancel may show as 1223.
        if rc == 1223:
            return False
        return rc > 32
    except Exception:
        return False


def ensure_admin_or_relaunch(*, message: str | None = None) -> None:
    """Ensure current process has admin rights.

    - If already admin: logs `Admin rights: yes`.
    - If not admin: logs `Admin rights: no` and `Relaunch requested via UAC`,
      prints a friendly message, attempts self-relaunch via UAC.
      If user cancels UAC, exits with clear text.
    """
    log = logging.getLogger(__name__)
    if not is_windows():
        return

    if is_admin():
        log.info("Admin rights: yes")
        return

    log.info("Admin rights: no")
    log.info("Relaunch requested via UAC")

    if not message:
        message = (
            "Нужны права администратора. Сейчас появится запрос UAC.\n"
            "Если вы нажмёте 'Нет', программа завершится."
        )
    print("\n" + message + "\n")

    ok = relaunch_self_as_admin()
    if ok:
        # Exit current (non-elevated) instance.
        raise SystemExit(0)

    # User likely canceled UAC (or dev run without elevation).
    print("\nЗапуск отменён пользователем (UAC) или запуск без прав.\n")
    raise SystemExit(1)


def run_as_admin(command: str | Sequence[str], wait: bool = True) -> Optional[int]:
    """Запускает команду от имени администратора на Windows без shell=True."""
    if not is_windows():
        return None

    if isinstance(command, str):
        file_path = command
        arg_list = []
    else:
        cmd_list = [str(x) for x in command]
        if not cmd_list:
            return None
        file_path = cmd_list[0]
        arg_list = cmd_list[1:]

    if is_admin():
        if wait:
            return subprocess.run([file_path, *arg_list], check=False).returncode
        subprocess.Popen([file_path, *arg_list])
        return None

    arg_items = ", ".join(_ps_quote(a) for a in arg_list)
    ps_script = (
        "Start-Process "
        f"-FilePath {_ps_quote(file_path)} "
        f"-ArgumentList @({arg_items}) "
        "-Verb RunAs"
    )
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        check=False,
    )
    return proc.returncode if wait else None


def get_windows_version() -> str:
    """Возвращает версию Windows."""
    if not is_windows():
        return "Unknown"
    try:
        import platform
        return platform.version()
    except Exception:
        return "Unknown"


def get_system_info() -> dict:
    """Собирает информацию о системе."""
    info = {
        "os": "Windows" if is_windows() else "Other",
        "admin": is_admin(),
        "version": get_windows_version() if is_windows() else None,
        "architecture": _platform.machine(),
        "python_version": sys.version,
    }
    return info