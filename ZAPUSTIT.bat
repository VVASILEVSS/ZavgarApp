@echo off
chcp 65001 >nul

echo ========================================
echo   ZavgarApp - Launcher
echo ========================================
echo.

REM Go to script directory
cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

REM Pull latest from repo
echo [1/3] Pulling updates from repo...
git pull origin main
if errorlevel 1 (
    echo WARNING: git pull failed, using local version
)
echo.

REM Setup venv
echo [2/3] Checking dependencies...
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
    pip install -q -r requirements.txt 2>nul
)
echo.

REM Launch app
echo [3/3] Starting ZavgarApp...
echo.
python -m zavgar_app.main

if errorlevel 1 (
    echo.
    echo ERROR: Application exited with error
)

pause
