@echo off
rem fralQR launcher (Windows). Double-click me to start the app.
cd /d "%~dp0"
python fralQR.py %*
if errorlevel 1 (
  echo.
  echo Python not found. Install Python 3.9+ from python.org
  echo Tick "Add python.exe to PATH" during install, then try again.
)
pause
