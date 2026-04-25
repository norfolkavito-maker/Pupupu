# DedZapret for Windows (portable)

Консольный менеджер для Windows 10/11 x64 с меню, похожим на `Zapret-Manager.sh` (StressOzz), который:

- умеет подтягивать upstream стратегий (`Flowseal/zapret-discord-youtube`, `StressOzz/Zapret-Manager`);
- генерирует стратегии в `data/strategies/generated/` (не редактировать руками);
- хранит пользовательские стратегии отдельно в `data/strategies/custom/`;
- поддерживает Discord стратегии **Dv1–Dv17**, YouTube **Yv1–Yv4**, игры **Gv1–Gv4**;
- запускает игры/программы с автозапуском `winws` и генерацией `.bat`/`.lnk`;
- запускается из `run.bat` (dev-режим) или из `DedZapret.exe` (релиз).

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

Скачать готовую portable-сборку можно во вкладке **Releases**:
https://github.com/norfolkavito-maker/Pupupu/releases

## Важно

- Для управления `winws`/WinDivert и редактирования `hosts` нужны права администратора.
- Ты несёшь ответственность за соблюдение законов и правил твоей сети/провайдера.
- Upstream-архивы и бинарники должны загружаться только по HTTPS.
- Бэкапы и импортируемые zip-файлы перед применением должны считаться доверенными только из проверенного источника.

