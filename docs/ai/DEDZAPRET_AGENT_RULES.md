# DedZapret Agent Rules

Правила безопасности для DedZapret Manager.

---

## 1. Общие принципы

### 1.1 Безопасность прежде всего
- **Никогда не компромисс безопасности**
- **Zero Trust** — ничего и никто не доверять
- **Defense in depth** — многоуровневая защита

### 1.2 Принципы разработки
- **Fresh build** — всегда fresh build, не migration
- **Preserve behavior** — сохранять полезное поведение
- **Extract intent** — извлекать намерение

---

## 2. Правила безопасности

### 2.1 Никаких секретов в коде
- **Hardcoded secrets** — API ключи, токены, пароли
- **Configuration files** — все настройки в конфигурационных файлах
- **Environment variables** — использование переменных окружения
- **Masking** — маскировка секретов в логах

### 2.2 Проверка прав администратора
- **Explicit checks** — явные проверки is_admin()
- **User confirmation** — запрос прав у пользователя
- **Audit logging** — логирование использования прав
- **Minimum privilege** — использовать только необходимые права

### 2.3 Безопасное выполнение процессов
- **No shell=True** — только list argv, не shell=True
- **Parameter validation** — валидация параметров
- **Process isolation** — изоляция процессов

---

## 3. Правила разработки

### 3.1 Fresh build vs Migration
- **Fresh build** — всегда fresh build
- **Extract intent** — извлечение намерения
- **Clean implementation** — чистая реализация

### 3.2 Изучение upstream источников
- **Read and understand** — читать и понимать
- **Extract patterns** — извлекать паттерны
- **Adapt, don't copy** — адаптировать, не копировать

---

## 4. Тестирование и валидация

### 4.1 Characterization tests
- **Capture current behavior** — захват текущего поведения
- **Test all scenarios** — тестирование всех сценариев

### 4.2 Unit tests
- **Test public API** — тестирование публичного API
- **Edge cases** — тестирование крайних случаев

---

## 5. Обработка ошибок

### 5.1 User-friendly messages
- **Clear language** — понятный язык
- **Actionable suggestions** — полезные советы
- **Error codes** — коды ошибок

### 5.2 Error handling patterns
- **Graceful degradation** — плавное degradation
- **Safe fallback** — безопасные альтернативы

---

## 6. Логирование и аудит

### 6.1 Audit logging
- **All actions** — все действия
- **Structured format** — структурированный формат
- **No sensitive data** — нет чувствительных данных

### 6.2 Secret masking
- **API keys** — API ключи
- **Tokens** — токены
- **Passwords** — пароли

---

**Документация обновлена:** 2026-05-07  
**Версия документа:** 1.0  
**Автор:** DedZapret Team