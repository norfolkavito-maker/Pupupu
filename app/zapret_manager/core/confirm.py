from __future__ import annotations

from app.zapret_manager.utils.console import ask
from app.zapret_manager.ui.colors import C


def confirm_phrase(*, prompt: str, phrase: str) -> bool:
    """Require explicit phrase entry.

    Designed to prevent accidental destructive actions.
    """
    s = ask(f"\n{C.RED}{prompt}{C.RESET}\nВведите {C.YELLOW}{phrase}{C.RESET} чтобы продолжить: ").strip()
    return s == phrase


def confirm_yes(prompt: str = "Подтвердите действие") -> bool:
    return confirm_phrase(prompt=prompt, phrase="YES")


def confirm_restore() -> bool:
    return confirm_phrase(prompt="Восстановление может перезаписать файлы.", phrase="RESTORE")


def confirm_reset() -> bool:
    return confirm_phrase(prompt="Сброс может удалить/перезаписать настройки.", phrase="RESET")


def confirm_enable_tun() -> bool:
    return confirm_phrase(prompt="TUN mode экспериментальный и опасный.", phrase="ENABLE TUN")
