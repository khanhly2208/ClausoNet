@echo off
echo 🔄 ClausoNet 4.0 Pro - License Database Copy Tool
echo ================================================

REM Get the source file path
set "SOURCE_FILE=C:\project\videoai\ClausoNet4.0\admin_data\license_database.json"

REM Get the target directory
set "TARGET_DIR=%LOCALAPPDATA%\ClausoNet4.0\admin_data"
set "TARGET_FILE=%TARGET_DIR%\license_database.json"

echo 📂 Source: %SOURCE_FILE%
echo 📁 Target: %TARGET_FILE%
echo.

REM Check if source file exists
if not exist "%SOURCE_FILE%" (
    echo ❌ Error: Source file not found!
    echo    Please make sure the admin license database exists.
    pause
    exit /b 1
)

REM Create target directory if it doesn't exist
if not exist "%TARGET_DIR%" (
    echo 📁 Creating target directory...
    mkdir "%TARGET_DIR%"
    if errorlevel 1 (
        echo ❌ Error: Could not create target directory!
        pause
        exit /b 1
    )
    echo ✅ Target directory created
)

REM Backup existing file if it exists
if exist "%TARGET_FILE%" (
    echo 💾 Backing up existing license database...
    copy "%TARGET_FILE%" "%TARGET_FILE%.backup.%date:~10,4%%date:~4,2%%date:~7,2%"
    if errorlevel 1 (
        echo ⚠️ Warning: Could not create backup
    ) else (
        echo ✅ Backup created
    )
)

REM Copy the file
echo 🔄 Copying license database...
copy "%SOURCE_FILE%" "%TARGET_FILE%"
if errorlevel 1 (
    echo ❌ Error: Could not copy license database!
    pause
    exit /b 1
)

echo ✅ License database copied successfully!
echo.
echo 🎯 ClausoNet 4.0 Pro should now be able to validate licenses on this machine.
echo 📍 License database location: %TARGET_FILE%
echo.
pause
