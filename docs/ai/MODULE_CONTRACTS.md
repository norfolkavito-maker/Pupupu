# Module Contracts

Этот документ описывает контракты между модулями DedZapret Manager. Контракты определяют API, ответственность и взаимодействие между компонентами.

---

## 1. Core Layer Contracts

### 1.1 Paths Module (`core/paths.py`)

**Responsibility:** Управление путями в portable layout.

**API:**
```python
# Возвращает корневую директорию данных
get_data_dir() -> Path

# Возвращает директорию конфигурации
get_config_dir() -> Path

# Возвращает директорию состояния
get_state_dir() -> Path

# Возвращает директорию runtime
get_runtime_dir() -> Path

# Возвращает путь к файлу конфигурации
get_config_file() -> Path

# Возвращает путь к файлу состояния
get_state_file() -> Path

# Возвращает путь к файлу текущего состояния
get_current_file() -> Path

# Возвращает путь к директории логов
get_log_dir() -> Path

# Возвращает путь к файлу лога
get_log_file(component: str) -> Path
```

**Dependencies:** None

**Usage:**
```python
from core.paths import get_config_file
config_path = get_config_file()
```

### 1.2 Config Module (`core/config.py`)

**Responsibility:** Управление конфигурацией приложения.

**API:**
```python
# Загрузка конфигурации
load_config() -> Config

# Сохранение конфигурации
save_config(config: Config) -> None

# Валидация конфигурации
validate_config(config: Config) -> List[str]

# Получение значения с fallback
get_value(key: str, default: Any = None) -> Any

# Установка значения
set_value(key: str, value: Any) -> None

# Сброс конфигурации к значениям по умолчанию
reset_config() -> Config
```

**Dependencies:**
- `core.paths` для путей
- `core.audit` для логирования изменений

**Usage:**
```python
from core.config import load_config, get_value
config = load_config()
debug_mode = get_value('debug', False)
```

### 1.3 State Module (`core/state.py`)

**Responsibility:** Управление состоянием приложения.

**API:**
```python
# Загрузка состояния
load_state() -> State

# Сохранение состояния
save_state(state: State) -> None

# Получение значения состояния
get_state_value(key: str, default: Any = None) -> Any

# Установка значения состояния
set_state_value(key: str, value: Any) -> None

# Сброс состояния
reset_state() -> State
```

**Dependencies:**
- `core.paths` для путей
- `core.audit` для логирования изменений

**Usage:**
```python
from core.state import load_state, get_state_value
state = load_state()
active_strategy = get_state_value('active_strategy')
```

### 1.4 Current State Module (`core/current_state.py`)

**Responsibility:** Управление текущим активным состоянием.

**API:**
```python
# Загрузка текущего состояния
load_current() -> CurrentState

# Сохранение текущего состояния
save_current(current: CurrentState) -> None

# Обновление PID
update_pid(pid: int) -> None

# Обновление активной стратегии
update_active_strategy(strategy_id: str) -> None

# Обновление статуса прокси
update_proxy_status(status: bool) -> None

# Проверка активного состояния
is_active() -> bool
```

**Dependencies:**
- `core.paths` для путей
- `core.audit` для логирования изменений

**Usage:**
```python
from core.current_state import load_current, update_pid
current = load_current()
update_pid(12345)
```

### 1.5 Audit Module (`core/audit.py`)

**Responsibility:** Аудит и логирование действий.

**API:**
```python
# Логирование действия
log_action(action: str, component: str, success: bool, message: str, **kwargs) -> None

# Логирование ошибки
log_error(component: str, error: str, **kwargs) -> None

# Логирование безопасности
log_security(action: str, details: str) -> None

# Получение логов
get_logs(component: str = None, level: str = None, limit: int = 100) -> List[dict]

# Очистка старых логов
cleanup_logs(days: int = 30) -> None
```

**Dependencies:** None

**Usage:**
```python
from core.audit import log_action, log_error
log_action('start', 'runtime', True, 'Runtime started successfully')
log_error('config', 'Failed to load config file')
```

---

## 2. Strategy Layer Contracts

### 2.1 Strategy Model (`strategies/model.py`)

**Responsibility:** Модель данных для стратегий.

**API:**
```python
class Strategy:
    def __init__(self, id: str, name: str, type: str, config: dict)
    
    # Валидация стратегии
    def validate() -> List[str]
    
    # Проверка совместимости
    def is_compatible_with(other: 'Strategy') -> bool
    
    # Сериализация в JSON
    def to_dict() -> dict
    
    # Десериализация из JSON
    @classmethod
    def from_dict(cls, data: dict) -> 'Strategy'
```

**Dependencies:** None

**Usage:**
```python
from strategies.model import Strategy
strategy = Strategy('v1-basic', 'Basic Strategy', 'dns-tcp-udp', {})
errors = strategy.validate()
```

### 2.2 Strategy Registry (`strategies/registry.py`)

**Responsibility:** Реестр всех стратегий.

**API:**
```python
# Инициализация реестра
init_registry() -> None

# Получение стратегии по ID
get_strategy(strategy_id: str) -> Strategy

# Получение всех стратегий
get_all_strategies() -> List[Strategy]

# Добавление стратегии
add_strategy(strategy: Strategy) -> None

# Удаление стратегии
remove_strategy(strategy_id: str) -> None

# Поиск стратегий по фильтрам
search_strategies(filters: dict) -> List[Strategy]
```

**Dependencies:**
- `strategies.model` для модели стратегии
- `core.audit` для логирования

**Usage:**
```python
from strategies.registry import get_strategy, get_all_strategies
strategy = get_strategy('v1-basic')
all_strategies = get_all_strategies()
```

### 2.3 Strategy Loader (`strategies/loader.py`)

**Responsibility:** Загрузка стратегий из разных источников.

**API:**
```python
# Загрузка встроенных стратегий
load_builtin_strategies() -> List[Strategy]

# Загрузка стратегии из файла
load_strategy_from_file(file_path: Path) -> Strategy

# Загрузка стратегии из строки
load_strategy_from_string(content: str) -> Strategy

# Импорт Flowseal стратегии
import_flowseal_strategy(content: str) -> Strategy

# Импорт StressOzz стратегии
import_stressozz_strategy(content: str) -> Strategy
```

**Dependencies:**
- `strategies.model` для модели стратегии
- `strategies.registry` для регистрации
- `core.audit` для логирования

**Usage:**
```python
from strategies.loader import load_strategy_from_file
strategy = load_strategy_from_file(Path('strategy.yaml'))
```

---

## 3. Runtime Layer Contracts

### 3.1 WinWS2 Detector (`runtime/detector.py`)

**Responsibility:** Поиск winws2.exe в разных locations.

**API:**
```python
# Поиск winws2.exe
find_winws2() -> Optional[Path]

# Проверка версии
get_version(winws2_path: Path) -> str

# Проверка доступности
is_available() -> bool
```

**Dependencies:** None

**Usage:**
```python
from runtime.detector import find_winws2
winws2_path = find_winws2()
```

### 3.2 Command Model (`runtime/command.py`)

**Responsibility:** Модель аргументов для winws2.

**API:**
```python
class Command:
    def __init__(self, winws2_path: Path, strategy: Strategy)
    
    # Генерация аргументов
    def build_args() -> List[str]
    
    # Проверка команды
    def validate() -> List[str]
    
    # Сериализация
    def to_dict() -> dict
```

**Dependencies:**
- `strategies.model` для стратегии
- `runtime.detector` для пути

**Usage:**
```python
from runtime.command import Command
command = Command(winws2_path, strategy)
args = command.build_args()
```

### 3.3 Process Manager (`runtime/process.py`)

**Responsibility:** Управление процессами winws2.

**API:**
```python
# Запуск процесса
start(command: Command) -> int

# Остановка процесса
stop(pid: int) -> bool

# Проверка активности
is_running(pid: int) -> bool

# Получение статуса
get_status(pid: int) -> dict

# Перезапуск процесса
restart(pid: int) -> int
```

**Dependencies:**
- `runtime.command` для команды
- `core.audit` для логирования

**Usage:**
```python
from runtime.process import start, stop
pid = start(command)
stop(pid)
```

---

## 4. Test Layer Contracts

### 4.1 Test Engine (`tests/engine.py`)

**Responsibility:** Движок для тестирования стратегий.

**API:**
```python
# Инициализация тестов
init_tests() -> None

# Запуск теста
run_test(strategy_id: str) -> dict

# Запуск всех тестов
run_all_tests(parallel: bool = True) -> dict

# Получение результатов теста
get_test_result(strategy_id: str) -> dict

# Получение всех результатов
get_all_results() -> dict
```

**Dependencies:**
- `strategies.registry` для стратегий
- `core.audit` для логирования

**Usage:**
```python
from tests.engine import run_test, get_test_result
result = run_test('v1-basic')
status = get_test_result('v1-basic')
```

### 4.2 Test Probes (`tests/probes.py`)

**Responsibility:** Сетевые пробы для тестирования.

**API:**
```python
# DNS проба
dns_probe(domain: str) -> dict

# TCP проба
tcp_probe(domain: str, port: int) -> dict

# UDP проба
udp_probe(domain: str, port: int) -> dict

# HTTP проба
http_probe(url: str) -> dict
```

**Dependencies:** None

**Usage:**
```python
from tests.probes import dns_probe, tcp_probe
dns_result = dns_probe('example.com')
tcp_result = tcp_probe('example.com', 80)
```

---

## 5. UI Layer Contracts

### 5.1 Console UI (`ui/console.py`)

**Responsibility:** Консольный интерфейс.

**API:**
```python
# Инициализация UI
init_ui() -> None

# Отрисовка дашборда
render_dashboard() -> None

# Отрисовка меню
render_menu(options: List[str]) -> int

# Отрисовка прогресса
render_progress(current: int, total: int) -> None

# Показ сообщения
show_message(message: str, type: str = 'info') -> None

# Запрос ввода
prompt_input(prompt: str) -> str
```

**Dependencies:** None

**Usage:**
```python
from ui.console import init_ui, render_dashboard, show_message
init_ui()
render_dashboard()
show_message('Hello, World!', 'info')
```

### 5.2 Main Menu (`ui/main_menu.py`)

**Responsibility:** Основное меню приложения.

**API:**
```python
# Показ главного меню
show_main_menu() -> None

# Показ меню тестов
show_tests_menu() -> None

# Показ меню профилей
show_profiles_menu() -> None

# Показ меню настроек
show_settings_menu() -> None
```

**Dependencies:**
- `ui.console` для отрисовки
- `strategies.registry` для стратегий
- `tests.engine` для тестов

**Usage:**
```python
from ui.main_menu import show_main_menu
show_main_menu()
```

---

## 6. Integration Layer Contracts

### 6.1 Profile Manager (`profiles/manager.py`)

**Responsibility:** Управление профилями.

**API:**
```python
# Загрузка профилей
load_profiles() -> List[Profile]

# Сохранение профилей
save_profiles(profiles: List[Profile]) -> None

# Создание профиля
create_profile(name: str, strategy_id: str) -> Profile

# Активация профиля
activate_profile(profile_id: str) -> None
```

**Dependencies:**
- `strategies.registry` для стратегий
- `core.state` для состояния

**Usage:**
```python
from profiles.manager import load_profiles, create_profile
profiles = load_profiles()
profile = create_profile('Home', 'v1-basic')
```

### 6.2 System Integration (`system/integration.py`)

**Responsibility:** Интеграция с системой Windows.

**API:**
```python
# Проверка прав администратора
is_admin() -> bool

# Установка автозапуска
set_autostart(enabled: bool) -> None

# Управление hosts
manage_hosts(add: bool, entries: List[str]) -> None

# Управление DNS
manage_dns(doh_servers: List[str]) -> None
```

**Dependencies:** None

**Usage:**
```python
from system.integration import is_admin, set_autostart
if is_admin():
    set_autostart(True)
```

---

## 7. Error Handling Contracts

### 7.1 Error Codes

| Код | Компонент | Описание |
|-----|----------|----------|
| E001 | Core | Ошибка загрузки конфигурации |
| E002 | Core | Ошибка сохранения состояния |
| E003 | Strategy | Стратегия не найдена |
| E004 | Runtime | WinWS2 не найден |
| E005 | Test | Ошибка теста |
| E006 | UI | Ошибка интерфейса |
| E007 | Profile | Ошибка профиля |
| E008 | System | Ошибка системной операции |

### 7.2 Error Handling

```python
class DedZapretError(Exception):
    def __init__(self, code: str, message: str, details: str = None)
    
    @property
    def user_message(self) -> str
    
    @property
    def help_url(self) -> str
```

**Usage:**
```python
try:
    # Some operation
except Exception as e:
    raise DedZapretError('E001', 'Failed to load config')
```

---

## 8. Logging Contracts

### 8.1 Log Levels

| Уровень | Описание | Пример |
|--------|----------|--------|
| DEBUG | Детальная отладочная информация | Variable values, function calls |
| INFO | Общая информация о работе приложения | App start/stop, major operations |
| WARNING | Предупреждения | Non-critical errors, deprecated features |
| ERROR | Ошибки | Failed operations, exceptions |
| CRITICAL | Критические ошибки | System failures, data corruption |

### 8.2 Log Format

```json
{
    "timestamp": "2026-05-07T04:12:00Z",
    "level": "INFO",
    "component": "runtime",
    "action": "start",
    "message": "Runtime started successfully",
    "details": {
        "pid": 12345,
        "strategy": "v1-basic"
    }
}
```

---

## 9. Testing Contracts

### 9.1 Unit Tests

Каждый модуль должен иметь:
- Тесты для публичного API
- Тесты для крайних случаев
- Тесты для ошибок

**Example:**
```python
# tests/test_config.py
def test_load_config():
    config = load_config()
    assert isinstance(config, Config)
    
def test_get_value():
    value = get_value('debug', False)
    assert isinstance(value, bool)
```

### 9.2 Integration Tests

Тесты для взаимодействия между модулями:
- Стратегия → Runtime
- Runtime → Process
- Test Engine → Probes
- UI → Core

**Example:**
```python
# tests/test_integration.py
def test_strategy_runtime():
    strategy = get_strategy('v1-basic')
    command = Command(winws2_path, strategy)
    args = command.build_args()
    assert isinstance(args, list)
```

---

**Документация обновлена:** 2026-05-07  
**Версия документа:** 1.0  
**Автор:** DedZapret Team