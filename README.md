# DedZapret (Windows)

Portable менеджер для **zapret / winws** (DPI-desync) под Windows 10/11 x64.
Интерфейс — консольное меню в стиле `Zapret-Manager.sh` (StressOzz).

## Скачать

Готовая сборка лежит в **Releases**:
https://github.com/norfolkavito-maker/Pupupu/releases

Там два архива:
- **DedZapret-portable.zip** — для обычных пользователей (DedZapret.exe + DedZapretData/)
- **DedZapret-dev-source.zip** — исходники/скрипты для разработки

## Быстрый старт (portable)

1) Распакуй `DedZapret-portable.zip`.
2) Запусти `DedZapret.exe` **от имени администратора**.
3) Не удаляй папку `DedZapretData` рядом с exe — там настройки, логи и runtime.

Если что-то падает при запуске — смотри `DedZapretData\data\logs\crash.log`.

## Где что лежит

```
DedZapret/
  DedZapret.exe
  README_FIRST.txt
  DedZapretData/
    config.yaml
    sources.yaml
    runtime/
      zapret/
    data/
      strategies/
        builtin/
        generated/
        custom/        <- пользовательские стратегии
      logs/            <- логи (в т.ч. crash.log)
      state/           <- state.json
      backups/
      profiles/
```

## Возможности

- Sync стратегий из upstream (`Flowseal/zapret-discord-youtube`, `StressOzz/Zapret-Manager`).
- Генерация стратегий в `.../strategies/generated/` (не редактировать руками).
- Пользовательские стратегии — в `.../strategies/custom/`.
- Поддержка наборов: Discord **Dv1–Dv17**, YouTube **Yv1–Yv4**, игры **Gv1–Gv4**.
- Тестирование стратегий, pin top5.
- TG WS Proxy (Go/Rust), DNS-over-HTTPS, hosts-блоки.

## Credits

Этот проект вдохновлён и опирается на работы:

- **bol-van / zapret** — `winws` + WinDivert и механики DPI desync (runtime движок).
  https://github.com/bol-van/zapret
- **StressOzz / Zapret-Manager** — UX/меню и набор стратегий (основа сценариев).
  https://github.com/StressOzz/Zapret-Manager
- **Flowseal / zapret-discord-youtube** — дополнительные стратегии.
  https://github.com/Flowseal/zapret-discord-youtube

Runtime в релизе поставляется **в комплекте** (portable), пользователю не нужно ничего скачивать отдельно.

## Запуск (dev)

1) Установи Python 3.11+  
2) Запусти `run.bat`

## Тесты

- Базовые unit-тесты: `PYTHONPATH=app python -m unittest discover -s tests -p "*_unittest.py"`
- После установки зависимостей также доступен `pytest`: `PYTHONPATH=app python -m pytest -q`

## Релиз (.exe)

Сборка делается через GitHub Actions на Windows (PyInstaller). См. `.github/workflows/build.yml`.
В релиз кладутся 2 архива: portable и dev/source.

## Patch list / Changelog

См. [CHANGELOG.md](CHANGELOG.md).

## Диагностическая сессия (тотальный лог)

Можно включить режим, который записывает **все взаимодействия** (ввод в меню + запуск процессов/команд) в файл сессии и на выходе предлагает сформировать zip-отчёт.

В `DedZapretData/config.yaml`:

```yaml
diagnostics:
  enabled: true
  record_console_io: true
  record_subprocess: true
  max_text_len: 8000
  redact_paths: false
  reporting:
    mode: github_issue
    github_repo: norfolkavito-maker/Pupupu
```

Файлы:
- `DedZapretData/data/logs/session_*.jsonl`
- `DedZapretData/data/logs/report_*.zip` (создаётся после подтверждения на выходе)

## Важно

- Для управления `winws`/WinDivert и редактирования `hosts` нужны права администратора.
- Ты несёшь ответственность за соблюдение законов и правил твоей сети/провайдера.
- Upstream-архивы и бинарники должны загружаться только по HTTPS.
- Бэкапы и импортируемые zip-файлы перед применением должны считаться доверенными только из проверенного источника.

