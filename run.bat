@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
cd /d "%~dp0"

REM Dev runner: creates venv, installs deps, runs app.

if not exist ".venv" (
  echo [*] Creating virtual environment...
  py -3 -m venv .venv
  if errorlevel 1 exit /b 1
)

call .venv\Scripts\activate
if errorlevel 1 exit /b 1

echo [*] Installing dependencies...
python -m pip install --upgrade pip > nul
if errorlevel 1 exit /b 1
pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo [*] Running wow Manager...
set PYTHONPATH=%CD%\app
python -m zapret_manager
pause

