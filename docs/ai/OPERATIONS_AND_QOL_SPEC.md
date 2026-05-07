# Operations and Quality of Life (QoL) Specification

Этот документ описывает операционные функции и улучшения качества жизни для DedZapret Manager. Фокус на user experience, удобстве использования и операционной эффективности.

---

## 1. User Experience Principles

### 1.1 Основные принципы
- **Clear over clever** — простые и понятные сообщения вместо "умных"
- **Progress over silence** — индикаторы прогресса для долгих операций
- **Safe over powerful** — безопасность важнее скорости
- **Helpful over technical** — пользовательские сообщения вместо технических ошибок

### 1.2 Уровни пользователя
- **Novice** — базовый функционал, минимум опций
- **Advanced** — полный контроль, все опции
- **Expert** — технические детали, логи, диагностика

---

## 2. Console UI Improvements

### 2.1 Dashboard
```
┌─────────────────────────────────────────────────────────────┐
│ DedZapret Manager v0.4.0                                    │
│                                                             │
│ Status: [●] Active (winws2 + sing-box)                    │
│ PID: 12345                                                  │
│ Strategy: v8-dns-tcp-udp                                  │
│ Proxy: Enabled (sing-box)                                  │
│                                                             │
│ ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│ │ 1. Tests   │ 2. Profiles │ 3. Settings │ 4. Exit    │  │
│ └─────────────┴─────────────┴─────────────┴─────────────┘  │
│                                                             │
│ Last test: Success (2026-05-07 04:05:23)                  │
│ Problems: 0                                                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Progress Indicators
- **Spinner** для операций (< 30 сек)
- **Progress bar** для долгих операций (> 30 сек)
- **Percentage** + **ETA** для операций с известным размером
- **Cancel button** для прерываемых операций

### 2.3 Error Handling
- **User-friendly messages** вместо traceback
- **Actionable suggestions** ("Try running as administrator")
- **Error codes** для поиска в документации
- **Copy to clipboard** для логов ошибок

### 2.4 Help System
- **Context-sensitive help** (F1 в любом меню)
- **Tooltips** для сложных опций
- **Examples** в командах
- **Wiki links** для документации

---

## 3. Tray Improvements

### 3.1 Status Icons
- **Green** — все работает
- **Yellow** — работает, но есть предупреждения
- **Red** — ошибки или неактивно
- **Gray** — не запущено

### 3.2 Context Menu
```
┌─────────────────────────────────────────────────────────────┐
│ DedZapret Manager                                          │
│                                                             │
│ ● Status: Active                                           │
│ ● Strategy: v8-dns-tcp-udp                                 │
│                                                             │
│ Start                                                      │
│ Stop                                                       │
│ Restart                                                     │
│ Test All Strategies...                                     │
│                                                             │
│ Profiles →                                                │
│   ┌ Home Gaming Work ┘                                       │
│                                                             │
│ Settings →                                                │
│   ┌ General Proxy Diagnostics ┘                             │
│                                                             │
│ View Logs                                                  │
│ Report Bug...                                              │
│ Exit                                                       │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Notifications
- **Toast notifications** для важных событий
- **Non-intrusive** — не прерывают работу
- **Auto-dismiss** через 5 секунд
- **Click to action** — открыть детали

---

## 4. Operations Workflow

### 4.1 Strategy Selection
```
┌─────────────────────────────────────────────────────────────┐
│ Select Strategy                                            │
│                                                             │
│ ┌ Built-in ──────────────────────────────────────────────┐ │
│ │ 1. v1-basic (Recommended for beginners)                │ │
│ │ 2. v2-dns (DNS-based bypass)                           │ │
│ │ 3. v3-tcp (TCP-based bypass)                           │ │
│ │ 4. v4-udp (UDP-based bypass)                           │ │
│ │ 5. v5-combo (Combined DNS+TCP+UDP)                    │ │
│ │ 6. v6-dns-tcp (DNS+TCP)                               │ │
│ │ 7. v7-dns-udp (DNS+UDP)                               │ │
│ │ 8. v8-dns-tcp-udp (All-in-one)                         │ │
│ │ 9. v9-gaming (Optimized for games)                     │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌ Custom ────────────────────────────────────────────────┐ │
│ │ 10. Import Flowseal...                                 │ │
│ │ 11. Import StressOzz...                                │ │
│ │ 12. Create Custom...                                    │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [?] Help  [q] Quit                                         │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Test Workflow
```
┌─────────────────────────────────────────────────────────────┐
│ Testing Strategies (3/12)                                  │
│                                                             │
│ ● v1-basic: Success (2.3s)                                 │
│ ● v2-dns: Success (1.8s)                                   │
│ ● v3-tcp: Success (3.1s)                                   │
│ ● v4-udp: Failed (Timeout)                                 │
│ ○ v5-combo: Testing... (45%) ETA: 2m 15s                   │
│                                                             │
│ Progress: ████████████████████░░░░░░░░░░░░░░░░░ 45%         │
│ Time: 00:02:30 / ETA: 00:05:15                            │
│                                                             │
│ [p] Pause  [c] Cancel  [l] View Logs                       │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Profile Management
```
┌─────────────────────────────────────────────────────────────┐
│ Profile Management                                         │
│                                                             │
│ ┌ Profiles ────────────────────────────────────────────────┐ │
│ │ 1. [●] Home (Active)                                   │ │
│ │ 2. [ ] Gaming                                          │ │
│ │ 3. [ ] Work                                            │ │
│ │ 4. + New Profile...                                     │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Profile: Home                                              │
│ Strategy: v8-dns-tcp-udp                                   │
│ Autostart: Enabled                                         │
│ Watcher: Enabled                                           │
│                                                             │
│ [e] Edit  [d] Delete  [s] Set Active  [a] Autostart         │
│                                                             │
│ [q] Back                                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Quality of Life Features

### 5.1 Auto-recovery
- **Last working profile** — автоматический запуск последнего рабочего профиля
- **Crash recovery** — восстановление после падения
- **Network change detection** — перезапуск при смене сети

### 5.2 Smart Defaults
- **Recommended strategy** — выбор стратегии по умолчанию
- **Auto-test** — автоматическое тестирование при выборе новой стратегии
- **Auto-save** — сохранение профиля после изменений

### 5.3 Keyboard Shortcuts
- **F1** — контекстная помощь
- **Ctrl+S** — сохранение профиля
- **Ctrl+Q** — выход
- **Esc** — отмена/назад

### 5.4 Mouse Support
- **Click navigation** — поддержка мыши в консоли
- **Hover tooltips** — всплывающие подсказки
- **Drag and drop** — импорт стратегий/профилей

---

## 6. Diagnostics and Debugging

### 6.1 Built-in Diagnostics
- **System info** — ОС, версия, права администратора
- **Network status** — интерфейсы, DNS, прокси
- **Binary check** — наличие и версии winws2.exe, sing-box.exe
- **Dependencies** — проверка зависимостей

### 6.2 Log Management
- **Auto-rotation** — автоматическое сжатие старых логов
- **Filtering** — фильтрация по уровню, модулю, времени
- **Export** — выборка логов в файл
- **Real-time** — просмотр логов в реальном времени

### 6.3 Debug Mode
- **Verbose logging** — детальные логи
- **Step mode** — пошаговое выполнение
- **Breakpoints** — остановки в коде
- **Memory usage** — мониторинг памяти

---

## 7. Performance Optimizations

### 7.1 Fast Startup
- **Lazy loading** — загрузка только необходимых модулей
- **Background initialization** — инициализация в фоновом режиме
- **Cache** — кэширование стратегий и профилей

### 7.2 Memory Management
- **Object pooling** — переиспользование объектов
- **Weak references** — избегание утечек памяти
- **Garbage collection** — ручной вызов GC при необходимости

### 7.3 Network Optimization
- **Connection pooling** — пул соединений
- **Timeout handling** — разумные таймауты
- **Parallel testing** — параллельное тестирование стратегий

---

## 8. Configuration Management

### 8.1 Configuration File
```yaml
# config.yaml
general:
  language: "ru"
  theme: "default"
  auto_update: true
  debug: false

ui:
  console_width: 80
  console_height: 24
  show_advanced: false
  animations: true

network:
  auto_test: true
  test_timeout: 30
  parallel_tests: 4

security:
  admin_required: true
  backup_enabled: true
  audit_logging: true

paths:
  data_dir: "DedZapretData"
  config_dir: "DedZapretData/config"
  state_dir: "DedZapretData/state"
```

### 8.2 Settings Menu
```
┌─────────────────────────────────────────────────────────────┐
│ Settings                                                   │
│                                                             │
│ ┌ General ─────────────────────────────────────────────────┐ │
│ │ Language: [Russian]                                      │ │
│ │ Theme: [Default]                                          │ │
│ │ Auto-update: [●] Enabled                                 │ │
│ │ Debug mode: [ ] Disabled                                 │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌ UI ──────────────────────────────────────────────────────┐ │
│ │ Console width: [80]                                       │ │
│ │ Show advanced: [ ] Disabled                               │ │
│ │ Animations: [●] Enabled                                 │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌ Network ─────────────────────────────────────────────────┐ │
│ │ Auto-test: [●] Enabled                                   │ │
│ │ Test timeout: [30] seconds                                │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [s] Save  [r] Reset  [q] Back                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Integration and Automation

### 9.1 Command Line Interface
```bash
# Запуск с профилем
dedzapret --profile "Gaming"

# Тестирование стратегий
dedzapret --test --parallel 8

# Экспорт конфигурации
dedzapret --export-config backup.yaml

# Импорт стратегии
dedzapret --import strategy.yaml
```

### 9.2 Windows Integration
- **Start Menu shortcut** — ярлык в меню Пуск
- **File association** — .dedzapret файлы
- **Context menu** — правый клик по файлам
- **Task Scheduler** — задачи планировщика

### 9.3 API Interface
```python
# Пример использования API
from dedzapret import DedZapretManager

dz = DedZapretManager()
dz.load_profile("Gaming")
dz.start()
dz.test_strategy("v8-dns-tcp-udp")
```

---

## 10. Documentation and Help

### 10.1 Built-in Help
- **Quick start guide** — пошаговое начало
- **FAQ** — ответы на частые вопросы
- **Troubleshooting** — решение проблем
- **Command reference** — все команды и опции

### 10.2 External Resources
- **Wiki** — подробная документация
- **Video tutorials** — видео инструкции
- **Community forum** — обсуждения
- **Bug tracker** — система багов

### 10.3 Context Help
- **Help button** в каждом меню
- **Tooltip hints** для сложных опций
- **Examples** в конфигурационных файлах
- **Error codes documentation**

---

## 11. Testing and Validation

### 11.1 Automated Testing
- **Unit tests** — тесты отдельных модулей
- **Integration tests** — тесты взаимодействия
- **UI tests** — тесты интерфейса
- **Performance tests** — тесты производительности

### 11.2 Manual Testing
- **Usability testing** — тестирование удобства использования
- **Compatibility testing** — тестирование на разных системах
- **Regression testing** — тестирование регрессий
- **Localization testing** — тестирование перевода

### 11.3 User Feedback
- **In-app feedback** — кнопка "Отзыв"
- **Analytics** — анонимная статистика использования
- **Beta testing** — бета тестирование
- **A/B testing** — тестирование разных интерфейсов

---

**Документация обновлена:** 2026-05-07  
**Версия документа:** 1.0  
**Автор:** DedZapret Team