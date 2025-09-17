@echo off
chcp 65001 >nul
echo 🔧 VEO WORKFLOW DEBUG TOOLS
echo ===============================
echo.

:menu
echo Select debug tool:
echo 1. Quick Element Tester (60s test)
echo 2. Step-by-Step Debugger (interactive)
echo 3. Full Workflow Debugger (comprehensive)
echo 4. Exit
echo.

set /p choice="Enter choice (1-4): "

if "%choice%"=="1" goto quick_test
if "%choice%"=="2" goto step_debug
if "%choice%"=="3" goto full_debug
if "%choice%"=="4" goto end
goto menu

:quick_test
echo.
echo 🚀 Starting Quick Element Tester...
echo This will test selectors and keep browser open for 60 seconds
echo.
python quick_veo_test.py
echo.
pause
goto menu

:step_debug
echo.
echo 🎯 Starting Step-by-Step Debugger...
echo This is an interactive tool - follow the prompts
echo Screenshots will be saved to debug_screenshots folder
echo.
python step_by_step_debug.py
echo.
pause
goto menu

:full_debug
echo.
echo 🔧 Starting Full Workflow Debugger...
echo This will run comprehensive debugging with interactive mode
echo.
python debug_veo_workflow.py
echo.
pause
goto menu

:end
echo.
echo 👋 Debug tools closed. Check debug_screenshots folder for results.
pause
