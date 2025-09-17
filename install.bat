@echo off
echo ========================================
echo ClausoNet 4.0 Pro - Windows Installer
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo 🐍 Python detected
python --version

echo.
echo 🚀 Starting installation...
echo.

REM Run the Python installer
python install.py

echo.
echo Installation script completed.
pause
