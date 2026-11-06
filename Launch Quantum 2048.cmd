@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Set up the game first using the commands in README.md.
  echo Then double-click this launcher again.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" launch.py
if errorlevel 1 pause
