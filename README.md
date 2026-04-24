# wow Manager for Windows (portable)

Консольный менеджер для Windows 10/11 x64 с меню, похожим на `Zapret-Manager.sh`, который:

- умеет подтягивать upstream (`bol-van/zapret-win-bundle`, `Flowseal/zapret-discord-youtube`, `stressOzz/zapret-discord-youtube`);
- генерирует стратегии в `data/strategies/generated/` (не редактировать руками);
- хранит пользовательские стратегии отдельно в `data/strategies/custom/`;
- поддерживает Discord стратегии **Dv1–Dv17**, YouTube **Yv1–Yv4**, игры **Gv1–Gv4**;
- запускает игры/программы с автозапуском `winws` и генерацией `.bat`/`.lnk`;
- запускается из `run.bat` (dev-режим) или из `wowManager.exe` (релиз).

## Запуск (dev)

1) Установи Python 3.11+  
2) Запусти `run.bat`

## Тесты

- Базовые unit-тесты: `PYTHONPATH=app python -m unittest discover -s tests -p "*_unittest.py"`
- После установки зависимостей также доступен `pytest`: `PYTHONPATH=app python -m pytest -q`

## Релиз (.exe)

Сборка делается через GitHub Actions на Windows (PyInstaller). См. `.github/workflows/build.yml`.

## Важно

- Для управления `winws`/WinDivert и редактирования `hosts` нужны права администратора.
- Ты несёшь ответственность за соблюдение законов и правил твоей сети/провайдера.
- Upstream-архивы и бинарники должны загружаться только по HTTPS.
- Бэкапы и импортируемые zip-файлы перед применением должны считаться доверенными только из проверенного источника.

