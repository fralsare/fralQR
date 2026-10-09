@echo off
REM --------------------------------------------------------------------------
REM Build the fralQR Windows release artifacts:
REM   - portable single .exe : dist\fralQR-1.0.0-windows-portable.exe
REM   - installer .exe       : dist\fralQR-Setup-1.0.0.exe  (via Inno Setup)
REM
REM Run from a normal Command Prompt (it cd's to the repo root itself):
REM   packaging\build_windows.bat
REM
REM Needs: Python 3.10+ on PATH. For the installer, Inno Setup 6 (ISCC) on
REM PATH - install with:  choco install innosetup
REM --------------------------------------------------------------------------
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0.."

set VERSION=1.0.0
set APP=fralQR

echo == fralQR %VERSION% (Windows) ==

where py >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found on PATH. Install Python 3.10+ and re-run.
  exit /b 1
)

if not exist ".build-venv\Scripts\pyinstaller.exe" (
  echo == creating build venv ==
  py -m venv .build-venv
  ".build-venv\Scripts\python.exe" -m pip install --upgrade pip
  ".build-venv\Scripts\python.exe" -m pip install pyinstaller pillow
)
set PYI=.build-venv\Scripts\pyinstaller.exe

REM ---- 1) portable single-file .exe --------------------------------------
echo == PyInstaller (onefile) - portable ==
if exist "dist\%APP%.exe" del /f /q "dist\%APP%.exe"
"%PYI%" --clean --noconfirm --onefile --noconsole --name %APP% %APP%.py
if not exist "dist\%APP%.exe" (
  echo [ERROR] onefile build failed
  exit /b 1
)
copy /y "dist\%APP%.exe" "dist\%APP%-%VERSION%-windows-portable.exe" >nul

REM ---- 2) installer (onedir + Inno Setup) --------------------------------
echo == PyInstaller (onedir) + Inno Setup ==
"%PYI%" --clean --noconfirm packaging\%APP%.spec
if not exist "dist\%APP%\%APP%.exe" (
  echo [ERROR] onedir build failed
  exit /b 1
)

REM Locate ISCC: try PATH first, then the standard Inno Setup 6 install dirs.
REM (Chocolatey may not have put it on PATH for this shell yet.)
set "ISCC="
for /f "delims=" %%i in ('where iscc 2^>nul') do if not defined ISCC set "ISCC=%%i"
if not defined ISCC if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"

if not defined ISCC (
  echo [ERROR] Inno Setup compiler ISCC.exe was not found.
  echo         Install it with: choco install innosetup
  echo         or download it from https://jrsoftware.org/isdl.php
  echo [NOTE]  The portable single-file exe above was still built.
  exit /b 1
)

echo == Inno Setup installer ==
call "%ISCC%" packaging\%APP%.iss
if errorlevel 1 (
  echo [ERROR] Inno Setup failed to compile the installer.
  exit /b 1
)
if not exist "dist\%APP%-Setup-%VERSION%.exe" (
  echo [ERROR] installer file was not created in dist.
  exit /b 1
)

echo == done.
dir /b "dist\%APP%-*.*"

endlocal
