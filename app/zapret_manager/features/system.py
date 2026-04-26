from __future__ import annotations

import logging
import os
import platform
import secrets
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import requests

from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.paths import Paths
from app.zapret_manager.utils.fsx import safe_extract_zip
from app.zapret_manager.utils.platform import is_admin, is_windows


log = logging.getLogger(__name__)


def _run_text_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")


def _run_powershell(script: str) -> subprocess.CompletedProcess[str]:
    return _run_text_command(["powershell", "-NoProfile", "-Command", script])


class FirewallManager:
    """Менеджер работы с брандмауэром Windows через netsh."""
    
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        
    def allow_winws(self) -> bool:
        """Разрешает winws.exe в брандмауэре."""
        if not is_windows() or not is_admin():
            return False
            
        try:
            from app.zapret_manager.features.zapret_runtime import detect_runtime_files

            detect_runtime_files(self.ctx)
            winws_path = self.ctx.state.runtime.winws_path or ""
            if not winws_path:
                raise RuntimeError("winws.exe not found in bundled runtime")
            _run_text_command(
                [
                    "netsh",
                    "advfirewall",
                    "firewall",
                    "add",
                    "rule",
                    'name=wowManager (winws)',
                    "dir=in",
                    "action=allow",
                    f'program={winws_path}',
                    "enable=yes",
                ]
            )
            log.info("winws разрешен в брандмауэре")
            return True
            
        except Exception as e:
            log.error(f"Ошибка разрешения winws в брандмауэре: {e}")
            return False
            
    def block_quic(self) -> bool:
        """Блокирует QUIC трафик в брандмауэре."""
        if not is_windows() or not is_admin():
            return False
            
        try:
            _run_text_command(
                [
                    "netsh",
                    "advfirewall",
                    "firewall",
                    "add",
                    "rule",
                    'name=wowManager (Block QUIC)',
                    "dir=in",
                    "action=block",
                    "protocol=UDP",
                    "localport=443",
                ]
            )
            log.info("QUIC трафик заблокирован в брандмауэре")
            return True
            
        except Exception as e:
            log.error(f"Ошибка блокировки QUIC в брандмауэре: {e}")
            return False
            
    def show_rules(self) -> List[str]:
        """Показывает правила брандмауэра, связанные с wowManager."""
        if not is_windows():
            return []
            
        try:
            result = subprocess.run(
                ["netsh", "advfirewall", "firewall", "show", "rule", 'name=wowManager*'],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            return result.stdout.splitlines()
            
        except Exception as e:
            log.error(f"Ошибка получения правил брандмауэра: {e}")
            return []
            
    def remove_zapret_rules(self) -> bool:
        """Удаляет все правила wowManager из брандмауэра."""
        if not is_windows() or not is_admin():
            return False
            
        try:
            _run_text_command(["netsh", "advfirewall", "firewall", "delete", "rule", 'name=wowManager*'])
            log.info("Правила wowManager удалены из брандмауэра")
            return True
            
        except Exception as e:
            log.error(f"Ошибка удаления правил брандмауэра: {e}")
            return False


class DohManager:
    """Менеджер работы с DoH (DNS over HTTPS) в Windows."""
    
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        
    def set_profile(self, profile_name: str) -> bool:
        """Устанавливает профиль DoH через PowerShell."""
        if not is_windows() or not is_admin():
            return False
            
        try:
            ps_commands = [
                '$dnsClient = Get-DnsClient -InterfaceAlias "Ethernet" -ErrorAction SilentlyContinue',
                '$dnsClient | Set-DnsClient -DnsOverHttpsTrafficPolicy UseDnsOverHttps -ErrorAction SilentlyContinue',
                '$dnsServer = Get-DnsServerSetting -All -ErrorAction SilentlyContinue',
                '$dnsServer.SetDnsServerScavengingState($true) | Out-Null',
                '$dnsServer.SetDnsServerForwarders((New-Object -ComObject DnsServerForwarder)) | Out-Null',
                '$dnsServer.SetDnsServerForwarders((New-Object -ComObject DnsServerForwarder), "https://dns.google/dns-query") | Out-Null',
            ]

            _run_powershell("; ".join(ps_commands))
            log.info(f"Профиль DoH {profile_name} установлен")
            return True
            
        except Exception as e:
            log.error(f"Ошибка установки профиля DoH: {e}")
            return False
            
    def reset_to_dhcp(self) -> bool:
        """Сбрасывает настройки DoH на DHCP."""
        if not is_windows() or not is_admin():
            return False
            
        try:
            ps_commands = [
                '$dnsClient = Get-DnsClient -InterfaceAlias "Ethernet" -ErrorAction SilentlyContinue',
                '$dnsClient | Set-DnsClient -DnsOverHttpsTrafficPolicy NoEncryption -ErrorAction SilentlyContinue',
            ]

            _run_powershell("; ".join(ps_commands))
            log.info("Настройки DoH сброшены на DHCP")
            return True
            
        except Exception as e:
            log.error(f"Ошибка сброса DoH: {e}")
            return False
            
    def flush_dns(self) -> bool:
        """Очищает DNS кэш."""
        if not is_windows():
            return False
            
        try:
            subprocess.run(["ipconfig", "/flushdns"], check=True, capture_output=True)
            log.info("DNS кэш очищен")
            return True
        except Exception as e:
            log.error(f"Ошибка очистки DNS кэша: {e}")
            return False
            
    def get_status(self) -> Dict[str, str]:
        """Получает текущий статус DoH."""
        if not is_windows():
            return {}
            
        try:
            result = _run_powershell('Get-NetIPConfiguration -InterfaceAlias "Ethernet" | Select-Object DNSSuffix, DNSServers')
            return {"dns_config": result.stdout}
            
        except Exception as e:
            log.error(f"Ошибка получения статуса DoH: {e}")
            return {}


class TgProxyManager:
    """Менеджер работы с TG WS Proxy (Go/Rust)."""
    
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        
    def check_proxy_exists(self) -> bool:
        """Проверяет наличие TG WS Proxy."""
        proxy_path = self.ctx.paths.runtime_dir / "tg" / "tgws-proxy"
        return (proxy_path / "tgws-proxy.exe").exists() or \
               (proxy_path / "wsproxy.exe").exists()
               
    def start_proxy(self, listen_port: int = 443) -> bool:
        """Запускает TG WS Proxy."""
        if not is_windows() or not is_admin():
            return False
            
        try:
            proxy_path = self.ctx.paths.runtime_dir / "tg" / "tgws-proxy"
            exe_path = proxy_path / "tgws-proxy.exe"
            
            if not exe_path.exists():
                exe_path = proxy_path / "wsproxy.exe"
                if not exe_path.exists():
                    raise RuntimeError("TG WS Proxy не найден")
                    
            cmd = [str(exe_path), f"--listen", f"127.0.0.1:{listen_port}", "--mtproto"]
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            log.info(f"TG WS Proxy запущен на порту {listen_port}")
            return True
            
        except Exception as e:
            log.error(f"Ошибка запуска TG WS Proxy: {e}")
            return False
            
    def stop_proxy(self) -> bool:
        """Останавливает TG WS Proxy."""
        if hasattr(self, 'process') and self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                log.info("TG WS Proxy остановлен")
                return True
            except Exception:
                return False
        return True
        
    def get_status(self) -> Dict[str, str]:
        """Получает статус TG WS Proxy."""
        if not hasattr(self, 'process'):
            return {"running": False}
            
        return {
            "running": self.process.poll() is None,
            "pid": self.process.pid if self.process else None
        }
        
    def generate_mtproto_secret(self) -> str:
        """Генерирует MTProto секрет для proxy."""
        try:
            return secrets.token_hex(16)
        except Exception as e:
            log.error(f"Ошибка генерации MTProto секрета: {e}")
            return ""


class SystemInfo:
    """Сбор информации о системе."""
    
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        
    def get_info(self) -> Dict[str, str]:
        """Собирает полную информацию о системе."""
        info = {
            "os": "Windows" if is_windows() else "Other",
            "admin": is_admin(),
            "version": platform.version() if is_windows() else None,
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "username": os.getenv('USERNAME', 'Unknown'),
            "computer_name": os.getenv('COMPUTERNAME', 'Unknown')
        }
        
        # Добавляем информацию о сетевых адаптерах
        if is_windows():
            info["adapters"] = self._get_network_adapters()
            
        # Добавляем публичный IP
        info["public_ip"] = self._get_public_ip()
        
        return info
        
    def _get_network_adapters(self) -> List[Dict[str, str]]:
        """Получает информацию о сетевых адаптерах."""
        try:
            result = _run_powershell("Get-NetAdapter | Select-Object Name, Status, LinkSpeed")
            
            adapters = []
            for line in result.stdout.splitlines():
                if "Name" in line or "Status" in line or "LinkSpeed" in line:
                    continue
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        adapters.append({
                            "name": parts[0],
                            "status": parts[1],
                            "speed": parts[2]
                        })
            return adapters
            
        except Exception as e:
            log.error(f"Ошибка получения информации о адаптерах: {e}")
            return []
            
    def _get_public_ip(self) -> str:
        """Получает публичный IP адрес."""
        try:
            response = requests.get("https://api.ipify.org", timeout=10)
            response.raise_for_status()
            return response.text.strip()
        except Exception:
            return "Unknown"


def check_windivert() -> Dict[str, bool]:
    """Проверяет наличие WinDivert."""
    # v0.3.1 portable layout: runtime lives in DedZapretData/runtime/zapret
    # NOTE: This helper is legacy; runtime detection uses zapret_runtime.runtime_health.
    bundle_path = (Paths.detect_root() / "DedZapretData" / "runtime" / "zapret").resolve()
    result = {
        "windivert_dll_exists": (bundle_path / "WinDivert.dll").exists(),
        "windivert_sys_exists": (bundle_path / "WinDivert64.sys").exists(),
        "winws_exists": (bundle_path / "winws.exe").exists(),
    }
    return result


def enable_tcp_timestamps() -> bool:
    """Включает TCP timestamps."""
    if not is_windows() or not is_admin():
        return False
        
    try:
        _run_text_command(["netsh", "int", "tcp", "set", "global", "timestamps=enabled"])
        log.info("TCP timestamps включены")
        return True
    except Exception as e:
        log.error(f"Ошибка включения TCP timestamps: {e}")
        return False


def disable_tcp_timestamps() -> bool:
    """Отключает TCP timestamps."""
    if not is_windows() or not is_admin():
        return False
        
    try:
        _run_text_command(["netsh", "int", "tcp", "set", "global", "timestamps=disabled"])
        log.info("TCP timestamps отключены")
        return True
    except Exception as e:
        log.error(f"Ошибка отключения TCP timestamps: {e}")
        return False


def show_tcp_timestamp_status() -> str:
    """Показывает статус TCP timestamps."""
    if not is_windows():
        return "Not Windows"
        
    try:
        result = subprocess.run(
            ["netsh", "int", "tcp", "show", "global"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        
        # Ищем строку с timestamps
        for line in result.stdout.splitlines():
            if "Timestamps" in line:
                return line.strip()
                
        return "Not found"
    except Exception as e:
        log.error(f"Ошибка получения статуса TCP timestamps: {e}")
        return "Error"


def quic_rule_exists() -> bool:
    if not is_windows():
        return False
    result = subprocess.run(
        ["netsh", "advfirewall", "firewall", "show", "rule", 'name=wowManager (Block QUIC)'],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return "No rules match" not in result.stdout and "Нет правил" not in result.stdout


def quic_block_enable() -> bool:
    if not is_windows() or not is_admin():
        return False
    return subprocess.run(
        [
            "netsh",
            "advfirewall",
            "firewall",
            "add",
            "rule",
            'name=wowManager (Block QUIC)',
            "dir=in",
            "action=block",
            "protocol=UDP",
            "localport=443",
        ],
        capture_output=True,
    ).returncode == 0


def quic_block_disable() -> bool:
    if not is_windows() or not is_admin():
        return False
    return subprocess.run(
        ["netsh", "advfirewall", "firewall", "delete", "rule", 'name=wowManager (Block QUIC)'],
        capture_output=True,
    ).returncode == 0


def tcp_timestamps_enable() -> bool:
    return enable_tcp_timestamps()


def tcp_timestamps_disable() -> bool:
    return disable_tcp_timestamps()


def flush_dns() -> bool:
    if not is_windows():
        return False
    return subprocess.run(["ipconfig", "/flushdns"], capture_output=True).returncode == 0


def backup(ctx: AppContext) -> Path:
    backup_dir = ctx.paths.data_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    archive = backup_dir / f"zapret_manager_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        if ctx.paths.config_file.exists():
            zf.write(ctx.paths.config_file, arcname="config.yaml")
        if ctx.paths.data_dir.exists():
            for p in ctx.paths.data_dir.rglob("*"):
                if p.is_file() and backup_dir not in p.parents:
                    zf.write(p, arcname=str(Path("data") / p.relative_to(ctx.paths.data_dir)))
    return archive


def restore(ctx: AppContext, archive_path: Path) -> None:
    if not archive_path.exists():
        raise RuntimeError(f"Бэкап не найден: {archive_path}")
    with zipfile.ZipFile(archive_path, "r") as zf:
        safe_extract_zip(zf, ctx.root)