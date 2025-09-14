@echo off
title ClausoNet 4.0 Pro - Admin Environment Setup
echo ========================================
echo ClausoNet 4.0 Pro - Admin Environment Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available!
    echo Please reinstall Python with pip included
    pause
    exit /b 1
)

echo pip found:
pip --version
echo.

REM Install requirements
echo Installing required packages...
echo.

pip install customtkinter>=5.2.0
if errorlevel 1 (
    echo ERROR: Failed to install customtkinter
    pause
    exit /b 1
)

pip install pyinstaller>=5.13.0
if errorlevel 1 (
    echo ERROR: Failed to install pyinstaller
    pause
    exit /b 1
)

pip install pillow>=10.0.0
if errorlevel 1 (
    echo WARNING: Failed to install pillow (optional)
    echo This is not critical, continuing...
)

echo.
echo ========================================
echo SETUP COMPLETE!
echo ========================================
echo.
echo Next steps:
echo 1. Run: python build_admin_key_exe.py
echo 2. Or run: python admin_key_gui.py to test first
echo.
echo Press any key to exit...
pause >nul 