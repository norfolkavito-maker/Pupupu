@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
cd /d "%~dp0"

REM Dev runner: creates venv, installs deps, runs app.

REM Require admin rights
net session >nul 2>&1
if not %errorlevel%==0 (
  echo.
  echo [!] Запустите run.bat от имени администратора
  echo [*] Запрашиваю права администратора через UAC...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b 1
)

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

echo [*] Running DedZapret...
set PYTHONPATH=%CD%\app
python -m zapret_manager
pause

