@echo off
echo ============================================
echo   Berth Planning System - Build
echo ============================================
echo.

:: Build API
echo [1/2] Building API...
cd /d %~dp0src\BerthPlanning.API
dotnet build --configuration Release
if %ERRORLEVEL% neq 0 (
    echo [ERROR] API build failed!
    pause
    exit /b 1
)
echo [OK] API build completed.
echo.

:: Build React Frontend
echo [2/2] Building React Frontend...
cd /d %~dp0frontend-react
call npm run build
if %ERRORLEVEL% neq 0 (
    echo [ERROR] React build failed!
    pause
    exit /b 1
)
echo [OK] React build completed.
echo.

echo ============================================
echo   Build completed successfully!
echo ============================================
echo.
echo API Output: src\BerthPlanning.API\bin\Release\net10.0
echo React Output: frontend-react\build
echo.
pause
