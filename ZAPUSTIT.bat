@echo off
chcp 65001 >nul
echo ========================================
echo   ZavgarApp — Запуск...
echo ========================================
echo.

:: Переход в директорию скрипта
cd /d "%~dp0"

:: Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    echo Установите Python 3.10+ с https://python.org
    pause
    exit /b 1
)

:: Обновление из репозитория
echo [1/3] Обновление из репозитория...
git pull origin main
if errorlevel 1 (
    echo ВНИМАНИЕ: не удалось обновить из репозитория, запуск с локальной версией...
)
echo.

:: Установка/обновление зависимостей (если нужно)
echo [2/3] Проверка зависимостей...
if not exist ".venv" (
    echo Создание виртуального окружения...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
    pip install -q -r requirements.txt 2>nul
)
echo.

:: Запуск приложения
echo [3/3] Запуск ZavgarApp...
echo.
python -m zavgar_app.main

if errorlevel 1 (
    echo.
    echo ========================================
    echo   ОШИБКА: приложение завершилось с ошибкой
    echo ========================================
)

pause
