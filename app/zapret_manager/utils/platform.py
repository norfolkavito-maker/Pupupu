from __future__ import annotations

import os
import platform as _platform
import subprocess
import sys
from typing import Optional, Sequence


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