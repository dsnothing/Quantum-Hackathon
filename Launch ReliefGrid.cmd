@echo off
cd /d "%~dp0"
if exist "reliefgrid\.venv\Scripts\python.exe" (
  "reliefgrid\.venv\Scripts\python.exe" "reliefgrid\launch.py" %*
) else (
  where py >nul 2>nul
  if errorlevel 1 (
    python "reliefgrid\launch.py" %*
  ) else (
    py -3.12 "reliefgrid\launch.py" %*
  )
)
if errorlevel 1 pause
