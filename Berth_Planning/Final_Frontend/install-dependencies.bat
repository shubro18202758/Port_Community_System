@echo off
echo ============================================
echo   Berth Planning System - Install Dependencies
echo ============================================
echo.

:: Restore .NET packages
echo [1/2] Restoring .NET packages...
cd /d %~dp0src\BerthPlanning.API
dotnet restore
if %ERRORLEVEL% neq 0 (
    echo [ERROR] .NET restore failed!
    pause
    exit /b 1
)
echo [OK] .NET packages restored.
echo.

:: Install npm packages
echo [2/2] Installing npm packages...
cd /d %~dp0frontend-react
call npm install
if %ERRORLEVEL% neq 0 (
    echo [ERROR] npm install failed!
    pause
    exit /b 1
)
echo [OK] npm packages installed.
echo.

echo ============================================
echo   Dependencies installed successfully!
echo ============================================
echo.
pause
