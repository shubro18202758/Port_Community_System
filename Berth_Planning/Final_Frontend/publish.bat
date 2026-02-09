@echo off
echo ============================================
echo   Berth Planning System - Publish
echo ============================================
echo.

set PUBLISH_DIR=%~dp0publish
set API_PUBLISH=%PUBLISH_DIR%\api
set FRONTEND_PUBLISH=%PUBLISH_DIR%\frontend

:: Clean publish directory
echo Cleaning publish directory...
if exist "%PUBLISH_DIR%" rmdir /s /q "%PUBLISH_DIR%"
mkdir "%PUBLISH_DIR%"
mkdir "%API_PUBLISH%"
mkdir "%FRONTEND_PUBLISH%"
echo.

:: Publish API
echo [1/2] Publishing API...
cd /d %~dp0src\BerthPlanning.API
dotnet publish -c Release -o "%API_PUBLISH%"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] API publish failed!
    pause
    exit /b 1
)
echo [OK] API published to: %API_PUBLISH%
echo.

:: Build and copy React Frontend
echo [2/2] Building and publishing React Frontend...
cd /d %~dp0frontend-react
call npm run build
if %ERRORLEVEL% neq 0 (
    echo [ERROR] React build failed!
    pause
    exit /b 1
)
xcopy /s /e /y "build\*" "%FRONTEND_PUBLISH%\"
echo [OK] Frontend published to: %FRONTEND_PUBLISH%
echo.

echo ============================================
echo   Publish completed successfully!
echo ============================================
echo.
echo Published files location:
echo   API:      %API_PUBLISH%
echo   Frontend: %FRONTEND_PUBLISH%
echo.
echo To deploy to IIS:
echo   1. Copy 'publish\api' folder to IIS virtual directory
echo   2. Copy 'publish\frontend' folder to web root
echo.
pause
