# DedZapret Manager — Product Overview

**Версия:** 0.4.0  
**Статус:** Rebuild  
**Платформа:** Windows (portable)  
**Лицензия:详见 LICENSE**

---

## 1. Что такое DedZapret Manager?

DedZapret Manager — это портативная утилита для управления обходом DPI (Deep Packet Inspection) с помощью техники DPI-desync. Она служит "менеджером" для нескольких технологий:

- **zapret/winws2** — основная технология обхода DPI
- **Flowseal/StressOzz** — стратегии обхода из других проектов
- **sing-box** — proxy/VPN nodes для дополнительного обхода
- **Диагностика и тестирование** — проверка работоспособности
- **Профили и автозапуск** — автоматизация сценариев использования

---

## 2. Целевая аудитория

### Основные пользователи:
- **Технические пользователи**, знающие о DPI и обходе
- **Игроки**, нуждающиеся в обходе для онлайн-игр
- **Пользователи с ограниченным доступом к интернету**

### Требования к пользователям:
- Базовые технические навыки
- Права администратора для установки/работы
- Понимание рисков использования обхода DPI

---

## 3. Ключевые возможности

### 3.1 Управление стратегиями
- Импорт стратегий из Flowseal/StressOzz
- Встроенные стратегии (v1-v9)
- Классификация по типам и совместимости
- Редактирование и кастомизация

### 3.2 Тестирование и диагностика
- Автоматическое тестирование всех стратегий
- Проверка доменов и сетевых возможностей
- Мониторинг состояния runtime
- Генерация отчетов и логов

### 3.3 Proxy/VPN интеграция
- Поддержка sing-box nodes
- Импорт подписок
- Системный proxy
- Превью без активации

### 3.4 Автоматизация
- Профили для разных сценариев
- Автозапуск через Task Scheduler
- Process watcher
- Last working profile recovery

### 3.5 Интерфейсы
- Console UI (основной)
- System tray (опционально)
- Progress indicators
- User-friendly сообщения

---

## 4. Архитектура продукта

### 4.1 Слои приложения
```
┌─────────────────────────────────┐
│          UI Layer               │  ← Console + Tray
├─────────────────────────────────┤
│        Command Layer            │  ← Menu actions + CLI
├─────────────────────────────────┤
│      Feature Layer             │  ← Tests, Diagnostics, Profiles
├─────────────────────────────────┤
│    Strategy Registry           │  ← Strategy management
├─────────────────────────────────┤
│ Runtime Management Layer       │  ← winws2 + sing-box
├─────────────────────────────────┤
│      Core Foundation           │  ← Config, State, Paths
└─────────────────────────────────┘
```

### 4.2 Ключевые модули
- **`core/`** — Foundation (config, state, paths, audit)
- **`features/`** — Business logic (tests, diagnostics, profiles)
- **`strategies/`** — Strategy management
- **`core/singbox/`** — Proxy/VPN management
- **`ui/`** — Console UI
- **`tray/`** — System tray (optional)

### 4.3 Data Flow
1. Пользователь выбирает стратегию/профиль
2. Strategy Registry validates и готовит стратегию
3. Runtime Layer запускает winws2/sing-box
4. Test Engine проверяет работоспособность
5. UI показывает статус и результаты

---

## 5. Технологический стек

### 5.1 Язык и платформа
- **Python 3.10+** — основной язык
- **Windows-only** — специфичные Windows API
- **Portable** — no installation required

### 5.2 Зависимости
- **pywin32** — Windows API
- **PyYAML** — configuration parsing
- **requests** — HTTP requests
- **psutil** — process management
- **rich** — enhanced console UI

### 5.3 Внешние бинарники
- **winws2.exe** — основной обходчик
- **sing-box.exe** — proxy/VPN (опционально)
- **WinDivert** — network capturing

---

## 6. Безопасность и конфиденциальность

### 6.1 Принципы безопасности
- **No hardcoded secrets** — все конфиденциальные данные в конфиге
- **Admin checks** — явные проверки прав администратора
- **Safe operations** — backup/rollback для всех изменений
- **Audit logging** — все действия логируются
- **Secret masking** — токены и пароли маскируются в логах

### 6.2 Защита данных
- **Portable layout** — данные хранятся в DedZapretData
- **Encryption** — чувствительные данные шифруются
- **No telemetry** — нет отправки данных разработчикам
- **Local only** — все операции локальные

---

## 7. Тестирование

### 7.1 Подход к тестированию
- **Characterization testing** — тесты для существующего поведения
- **Unit tests** — тесты для отдельных модулей
- **Integration tests** — тесты для взаимодействия компонентов
- **E2E tests** — тесты полного workflow
- **Snapshot testing** — для стратегий и конфигов

### 7.2 Инструменты
- **pytest** — основной фреймворк
- **unittest.mock** — мокирование зависимостей
- **freezegun** — тестирование времени
- **responses** — мокирование HTTP

---

## 8. Развертывание и распространение

### 8.1 Формат распространения
- **Portable ZIP** — включает все бинарники
- **Installer (опционально)** — для удобства установки
- **Auto-update** — встроенный механизм обновлений

### 8.2 Требования к системе
- **Windows 10+**
- **Администраторские права**
- **.NET Framework** (для winws2)
- **WinPcap/WinDivert** (для сетевого захвата)

---

## 9. Жизненный цикл разработки

### 9.1 Workflow
1. **Documentation** — создание/обновление документации
2. **Characterization tests** — тесты текущего поведения
3. **Implementation** — написание кода
4. **Testing** — модульные и интеграционные тесты
5. **Verification** — проверка скриптами
6. **Documentation update** — обновление документации

### 9.2 Quality gates
- Все тесты должны проходить
- Нет новых блокеров
- Документация актуальна
- Verification скрипты проходят

---

## 10. История и контекст

### 10.1 Происхождение проекта
Проект основан на:
- **bol-van/zapret** — техническая основа
- **Flowseal/zapret-discord-youtube** — Windows runtime
- **StressOzz/Zapret-Manager** — workflow и стратегии

### 10.2 Ключевые уроки
- Не делать миграцию на месте — fresh build
- Сохранять полезное поведение, но не структуру
- Тестировать перед рефакторингом
- User-friendly сообщения вместо технических ошибок

---

## 11. Ресурсы

### 11.1 Внутренние ресурсы
- **PROGRAM_BLUEPRINT.md** — архитектурная карта
- **IMPLEMENTATION_ORDER.md** — порядок разработки
- **CONTEXT_MAP.md** — карта контекста
- **REGRESSION_PREVENTION_CHECKLIST.md** — регрессии

### 11.2 Внешние ресурсы
- **GitHub Issues** — баги и фичи
- **Discussions** — обсуждения
- **Wiki** — подробная документация
- **Changelog** — история изменений

---

## 12. Вопросы и ответы

### Q: Почему не используется Docker?
A: Потому что DPI bypass требует прямого доступа к сетевым интерфейсам Windows, что невозможно в Docker.

### Q: Почему portable, а не installer?
A: Для удобства разработки и тестирования, а также чтобы пользователи не имели прав на установку.

### Q: Как обеспечить безопасность?
A: Через explicit admin checks, atomic writes, audit logging и backup/rollback механизмы.

---

**Документация обновлена:** 2026-05-07  
**Версия документа:** 1.0  
**Автор:** DedZapret Team