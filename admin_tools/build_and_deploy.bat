@echo off
title ClausoNet 4.0 Pro - Build Admin Key Generator
echo ============================================
echo ClausoNet 4.0 Pro - Build Admin Key Generator
echo ============================================
echo.

REM Check if Python and required files exist
if not exist "admin_key_gui.py" (
    echo ERROR: admin_key_gui.py not found!
    echo Make sure you're running this from the admin_tools directory
    pause
    exit /b 1
)

if not exist "simple_key_generator.py" (
    echo ERROR: simple_key_generator.py not found!
    pause
    exit /b 1
)

if not exist "build_admin_key_exe.py" (
    echo ERROR: build_admin_key_exe.py not found!
    echo Please make sure all files are present
    pause
    exit /b 1
)

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH!
    echo Please install Python or run setup_admin_env.bat first
    pause
    exit /b 1
)

echo.
echo Starting build process...
echo.

REM Run the build script
python build_admin_key_exe.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Check the error messages above
    pause
    exit /b 1
)

echo.
echo ============================================
echo BUILD COMPLETE!
echo ============================================
echo.

REM Check if files were created
if exist "admin_key_package\ClausoNet_AdminKeyGenerator.exe" (
    echo SUCCESS: EXE file created successfully!
    echo Location: admin_key_package\ClausoNet_AdminKeyGenerator.exe
    echo.
    
    REM List package contents
    echo Package contents:
    dir /b admin_key_package\
    echo.
    
    REM Check for ZIP file
    for %%f in (ClausoNet_AdminKeyGenerator_*.zip) do (
        echo Deployment ZIP: %%f
        echo Ready to copy to admin machine!
    )
) else (
    echo WARNING: EXE file not found in admin_key_package directory
    echo Build may have failed - check error messages above
)

echo.
echo Next steps:
echo 1. Test the EXE by running admin_key_package\ClausoNet_AdminKeyGenerator.exe
echo 2. Copy the ZIP file to the admin machine
echo 3. Extract and run Start_AdminKeyGenerator.bat
echo.
pause 