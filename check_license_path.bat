@echo off
echo 🔍 ClausoNet 4.0 Pro - Find License Path
echo =======================================

echo 📍 Your license database should be placed at:
echo %LOCALAPPDATA%\ClausoNet4.0\admin_data\license_database.json
echo.
echo 📂 Full path on this machine:
echo %LOCALAPPDATA%\ClausoNet4.0\admin_data\
echo.

if exist "%LOCALAPPDATA%\ClausoNet4.0\admin_data\license_database.json" (
    echo ✅ License database found!
    dir "%LOCALAPPDATA%\ClausoNet4.0\admin_data\license_database.json"
) else (
    echo ❌ License database not found
    echo 💡 Please copy license_database.json to the path above
)

echo.
echo 📋 To open the folder in Explorer, run:
echo explorer "%LOCALAPPDATA%\ClausoNet4.0\admin_data"
echo.
pause
