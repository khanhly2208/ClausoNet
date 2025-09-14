@echo off
title ClausoNet 4.0 Pro - Admin Key Generator
echo Starting ClausoNet Admin Key Generator...
echo.

REM Check if EXE exists
if not exist "ClausoNet_AdminKeyGenerator.exe" (
    echo ERROR: ClausoNet_AdminKeyGenerator.exe not found!
    echo Please make sure this batch file is in the same directory as the EXE.
    pause
    exit /b 1
)

REM Check admin_data directory
if not exist "admin_data" (
    echo Creating admin_data directory...
    mkdir admin_data
)

REM Start the application
echo Launching Admin Key Generator...
start "" "ClausoNet_AdminKeyGenerator.exe"

REM Wait a moment then close this window
timeout /t 2 /nobreak >nul
exit
