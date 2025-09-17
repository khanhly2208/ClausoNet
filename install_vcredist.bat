@echo off
echo Installing Microsoft Visual C++ Redistributable...
echo This fixes VCRUNTIME140.dll errors when running ClausoNet 4.0 Pro

:: Check if already installed
reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" >nul 2>&1
if %errorlevel% equ 0 (
    echo VC++ Redistributable x64 is already installed.
    goto :end
)

:: Download and install VC++ Redistributable
echo Downloading Microsoft Visual C++ Redistributable...
powershell -Command "& {Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile 'vc_redist.x64.exe'}"

if exist "vc_redist.x64.exe" (
    echo Installing VC++ Redistributable (this may take a few minutes)...
    vc_redist.x64.exe /quiet /norestart
    del vc_redist.x64.exe
    echo Installation completed!
) else (
    echo Failed to download VC++ Redistributable
    echo Please download manually from: https://aka.ms/vs/17/release/vc_redist.x64.exe
)

:end
echo.
echo You can now run ClausoNet4.0Pro.exe without VCRUNTIME140.dll errors
pause
