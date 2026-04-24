from __future__ import annotations

import json
import logging
import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import TYPE_CHECKING, List, Dict, Optional

from zapret_manager.core.state import save_state
from zapret_manager.utils.platform import is_admin, is_windows

if TYPE_CHECKING:
    from zapret_manager.core.app_context import AppContext


log = logging.getLogger(__name__)


DEFAULT_HOSTS_PATH = Path(r"C:\Windows\System32\drivers\etc\hosts")


@dataclass(frozen=True)
class HostsBlock:
    key: str
    title: str
    lines: list[str]


def _default_blocks() -> List[HostsBlock]:
    def map_domains(domains: list[str]) -> list[str]:
        return [f"0.0.0.0 {d}" for d in domains]

    return [
        HostsBlock("NALOG", "nalog.ru", map_domains(["nalog.ru", "www.nalog.ru"])),
        HostsBlock("RUTOR", "rutor.info", map_domains(["rutor.info", "www.rutor.info"])),
        HostsBlock("NTC", "ntc.party", map_domains(["ntc.party", "www.ntc.party"])),
        HostsBlock(
            "INSTAGRAM",
            "Instagram & Facebook",
            map_domains(["instagram.com", "www.instagram.com", "facebook.com", "www.facebook.com"]),
        ),
        HostsBlock("LIBRUSEC", "lib.rus.ec", map_domains(["lib.rus.ec", "www.lib.rus.ec"])),
        HostsBlock(
            "AI",
            "AI сервисы",
            map_domains(["chat.openai.com", "openai.com", "claude.ai", "gemini.google.com"]),
        ),
        HostsBlock("TWITCH", "Twitch", map_domains(["twitch.tv", "www.twitch.tv"])),
        HostsBlock("TGWEB", "Telegram Web", map_domains(["web.telegram.org"])),
        HostsBlock("SPOTIFY", "Spotify", map_domains(["spotify.com", "www.spotify.com"])),
        HostsBlock("SUPERCELL", "Supercell", map_domains(["store.supercell.com"])),
    ]


class HostsManager:
    """Менеджер работы с файлом hosts для Windows."""
    
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.hosts_path = Path(ctx.config.paths.hosts_file)
        
    def backup(self) -> str:
        """Создает бэкап файла hosts."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(self.ctx.config.paths.backup_dir) / "hosts"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_file = backup_dir / f"hosts_backup_{timestamp}.txt"
        
        if self.hosts_path.exists():
            shutil.copy2(self.hosts_path, backup_file)
            log.info(f"Бэкап hosts сохранен в {backup_file}")
            return str(backup_file)
        else:
            log.warning("Файл hosts не существует, бэкап не создан")
            return ""
            
    def restore(self, backup_file: str) -> bool:
        """Восстанавливает файл hosts из бэкапа."""
        backup_path = Path(backup_file)
        if not backup_path.exists():
            log.error(f"Файл бэкапа не найден: {backup_path}")
            return False
            
        try:
            # Проверяем права администратора
            if not is_windows() or not is_admin():
                raise RuntimeError("Нужны права администратора для восстановления hosts")
                
            shutil.copy2(backup_path, self.hosts_path)
            log.info(f"Hosts восстановлен из {backup_path}")
            
            # Сбрасываем DNS кэш
            self.flush_dns()
            return True
            
        except Exception as e:
            log.error(f"Ошибка восстановления hosts: {e}")
            return False
            
    def flush_dns(self) -> bool:
        """Очищает DNS кэш Windows."""
        if not is_windows():
            return False
            
        try:
            subprocess.run(["ipconfig", "/flushdns"], check=True, capture_output=True)
            log.info("DNS кэш очищен")
            return True
        except Exception as e:
            log.error(f"Ошибка очистки DNS кэша: {e}")
            return False
            
    def get_blocks(self) -> List[HostsBlock]:
        """Возвращает предопределенные блоки для hosts."""
        return _default_blocks()
        
    def add_block(self, key: str, custom_lines: Optional[List[str]] = None) -> bool:
        """Добавляет блок в файл hosts."""
        if not is_windows() or not is_admin():
            raise RuntimeError("Нужны права администратора для изменения hosts")
            
        b = self._marker_begin(key)
        e = self._marker_end(key)
        
        lines = self._read_hosts()
        
        # Удаляем существующий блок, если есть
        out = []
        skip = False
        for ln in lines:
            if ln.strip() == b:
                skip = True
                continue
            if skip and ln.strip() == e:
                skip = False
                continue
            if not skip:
                out.append(ln)
        
        # Добавляем новый блок
        if custom_lines:
            block_lines = custom_lines
        else:
            block = next((x for x in self.get_blocks() if x.key == key), None)
            if not block:
                raise RuntimeError(f"Unknown hosts block: {key}")
            block_lines = block.lines
            
        if out and out[-1].strip() != "":
            out.append("")
        out.append(b)
        out.extend(block_lines)
        out.append(e)
        
        self._write_hosts(out)
        log.info(f"Блок {key} добавлен в hosts")
        
        # Обновляем состояние
        self.ctx.state.hosts.blocks[key] = True
        save_state(self.ctx.paths.state_file, self.ctx.state)
        
        # Сбрасываем DNS кэш
        if self.ctx.config.network.flush_dns_after_hosts_change:
            self.flush_dns()
            
        return True
        
    def remove_block(self, key: str) -> bool:
        """Удаляет блок из файла hosts."""
        if not is_windows() or not is_admin():
            raise RuntimeError("Нужны права администратора для изменения hosts")
            
        b = self._marker_begin(key)
        e = self._marker_end(key)
        
        lines = self._read_hosts()
        out: list[str] = []
        skip = False
        
        for ln in lines:
            if ln.strip() == b:
                skip = True
                continue
            if skip and ln.strip() == e:
                skip = False
                continue
            if not skip:
                out.append(ln)
                
        self._write_hosts(out)
        log.info(f"Блок {key} удален из hosts")
        
        # Обновляем состояние
        self.ctx.state.hosts.blocks[key] = False
        save_state(self.ctx.paths.state_file, self.ctx.state)
        
        # Сбрасываем DNS кэш
        if self.ctx.config.network.flush_dns_after_hosts_change:
            self.flush_dns()
            
        return True
        
    def get_block_status(self, key: str) -> bool:
        """Проверяет, включен ли блок в hosts."""
        b = self._marker_begin(key)
        e = self._marker_end(key)
        
        lines = self._read_hosts()
        try:
            i = lines.index(b)
            j = lines.index(e)
            return i < j
        except ValueError:
            return False
            
    def list_blocks(self) -> Dict[str, bool]:
        """Возвращает словарь со статусом всех блоков."""
        blocks = self.get_blocks()
        return {block.key: self.get_block_status(block.key) for block in blocks}
        
    def clear_all_manager_blocks(self) -> bool:
        """Удаляет все блоки ZAPRET-MANAGER из hosts."""
        if not is_windows() or not is_admin():
            raise RuntimeError("Нужны права администратора для изменения hosts")
            
        lines = self._read_hosts()
        out: list[str] = []
        skip = False
        
        for ln in lines:
            if ln.startswith("# === ZAPRET-MANAGER BEGIN "):
                skip = True
                continue
            if skip and ln.startswith("# === ZAPRET-MANAGER END "):
                skip = False
                continue
            if not skip:
                out.append(ln)
                
        self._write_hosts(out)
        log.info("Все блоки ZAPRET-MANAGER удалены из hosts")
        
        # Сбрасываем состояние
        for key in self.ctx.state.hosts.blocks:
            self.ctx.state.hosts.blocks[key] = False
        save_state(self.ctx.paths.state_file, self.ctx.state)
        
        # Сбрасываем DNS кэш
        if self.ctx.config.network.flush_dns_after_hosts_change:
            self.flush_dns()
            
        return True
        
    def _marker_begin(self, key: str) -> str:
        return f"# === ZAPRET-MANAGER BEGIN {key} ==="
        
    def _marker_end(self, key: str) -> str:
        return f"# === ZAPRET-MANAGER END {key} ==="
        
    def _read_hosts(self) -> List[str]:
        """Читает файл hosts."""
        if not self.hosts_path.exists():
            return []
        txt = self.hosts_path.read_text(encoding="utf-8", errors="replace")
        return txt.splitlines()
        
    def _write_hosts(self, lines: List[str]) -> None:
        """Записывает файл hosts."""
        text = "\n".join(lines).rstrip() + "\n"
        self.hosts_path.write_text(text, encoding="utf-8")


# Сохраняем существующие функции для обратной совместимости
def blocks() -> List[HostsBlock]:
    """Возвращает предопределенные блоки hosts (для обратной совместимости)."""
    return _default_blocks()


def ensure_admin_windows(*, require_admin: bool = True) -> None:
    """Проверяет права администратора для Windows."""
    if not require_admin:
        return
    if not is_windows():
        raise RuntimeError("Windows-only")
    if not is_admin():
        raise RuntimeError("Нужны права администратора для изменения hosts.")


def _marker_begin(key: str) -> str:
    return f"# === ZAPRET-MANAGER BEGIN {key} ==="


def _marker_end(key: str) -> str:
    return f"# === ZAPRET-MANAGER END {key} ==="


def read_hosts(path: Path = DEFAULT_HOSTS_PATH) -> List[str]:
    """Читает файл hosts (для обратной совместимости)."""
    if not path.exists():
        return []
    txt = path.read_text(encoding="utf-8", errors="replace")
    return txt.splitlines()


def write_hosts(lines: List[str], path: Path = DEFAULT_HOSTS_PATH) -> None:
    """Записывает файл hosts (для обратной совместимости)."""
    text = "\n".join(lines).rstrip() + "\n"
    path.write_text(text, encoding="utf-8")


def has_block(key: str, *, path: Path = DEFAULT_HOSTS_PATH) -> bool:
    """Проверяет наличие блока в hosts (для обратной совместимости)."""
    b = _marker_begin(key)
    e = _marker_end(key)
    lines = read_hosts(path)
    try:
        i = lines.index(b)
        j = lines.index(e)
        return i < j
    except ValueError:
        return False


def set_block_enabled(
    key: str,
    enabled: bool,
    *,
    path: Path = DEFAULT_HOSTS_PATH,
    require_admin: bool = True,
) -> None:
    """Включает/выключает блок в hosts (для обратной совместимости)."""
    ensure_admin_windows(require_admin=require_admin)

    b = _marker_begin(key)
    e = _marker_end(key)
    lines = read_hosts(path)

    # Remove existing block
    out: List[str] = []
    skip = False
    for ln in lines:
        if ln.strip() == b:
            skip = True
            continue
        if skip and ln.strip() == e:
            skip = False
            continue
        if not skip:
            out.append(ln)

    if enabled:
        block = next((x for x in blocks() if x.key == key), None)
        if not block:
            raise RuntimeError(f"Unknown hosts block: {key}")
        if out and out[-1].strip() != "":
            out.append("")
        out.append(b)
        out.extend(block.lines)
        out.append(e)

    write_hosts(out, path)
    log.info("hosts block %s enabled=%s", key, enabled)


def clear_all_manager_blocks(*, path: Path = DEFAULT_HOSTS_PATH, require_admin: bool = True) -> None:
    """Удаляет все блоки ZAPRET-MANAGER из hosts (для обратной совместимости)."""
    ensure_admin_windows(require_admin=require_admin)
    lines = read_hosts(path)
    out: List[str] = []
    skip = False
    for ln in lines:
        if ln.startswith("# === ZAPRET-MANAGER BEGIN "):
            skip = True
            continue
        if skip and ln.startswith("# === ZAPRET-MANAGER END "):
            skip = False
            continue
        if not skip:
            out.append(ln)
    write_hosts(out, path)


def finland_discord_block() -> HostsBlock:
    return HostsBlock(
        "DISCORD_FINLAND",
        "Discord Finland",
        [
            "31.13.72.36 discord.media",
            "31.13.73.36 discord.media",
            "31.13.74.36 discord.media",
        ],
    )


def load_blocks_from_file(path: Path) -> List[HostsBlock]:
    if not path.exists():
        return blocks()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("blocks", [])
        out: List[HostsBlock] = []
        for item in items:
            out.append(
                HostsBlock(
                    key=str(item.get("key", "")),
                    title=str(item.get("title", item.get("key", ""))),
                    lines=[str(x) for x in item.get("lines", [])],
                )
            )
        return [b for b in out if b.key]
    except Exception:
        return blocks()


def reset_hosts_windows(path: Path = DEFAULT_HOSTS_PATH) -> None:
    ensure_admin_windows()
    if not path.exists():
        path.write_text("127.0.0.1 localhost\n::1 localhost\n", encoding="utf-8")
        return
    clear_all_manager_blocks(path=path)