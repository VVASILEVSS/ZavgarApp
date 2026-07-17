@echo off
chcp 65001 >nul
echo ========================================
echo   ZavgarApp — Запуск...
echo ========================================
echo.

:: Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    echo Установите Python 3.10+ с https://python.org
    pause
    exit /b 1
)

:: Установка зависимостей (если нужно)
if not exist ".venv" (
    echo Создание виртуального окружения...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

:: Запуск приложения
echo.
echo Запуск ZavgarApp...
python -m zavgar_app.main

pause
