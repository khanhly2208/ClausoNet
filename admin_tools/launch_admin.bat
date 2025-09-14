@echo off
echo 🎯 ClausoNet 4.0 Pro - License Admin Launcher
echo ================================================

cd /d "%~dp0"

echo 📦 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo ✅ Python found!

echo 📦 Installing required packages...
pip install customtkinter pandas openpyxl

echo 🚀 Launching License Admin GUI...
python admin_license_gui.py

if errorlevel 1 (
    echo ❌ Failed to launch admin tool
    echo 🔧 Trying CLI version instead...
    python license_key_generator.py
)

pause
