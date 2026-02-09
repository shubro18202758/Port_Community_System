@echo off
echo ============================================
echo   Berth Planning API - Publish
echo ============================================
echo.

set PUBLISH_DIR=%~dp0publish\api

:: Clean publish directory
echo Cleaning publish directory...
if exist "%PUBLISH_DIR%" rmdir /s /q "%PUBLISH_DIR%"
mkdir "%PUBLISH_DIR%"
echo.

:: Publish API
echo Publishing API...
cd /d %~dp0src\BerthPlanning.API
dotnet publish -c Release -o "%PUBLISH_DIR%"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] API publish failed!
    pause
    exit /b 1
)

echo.
echo ============================================
echo   API Publish completed successfully!
echo ============================================
echo.
echo Published to: %PUBLISH_DIR%
echo.
echo To run: cd "%PUBLISH_DIR%" ^&^& BerthPlanning.API.exe
echo.
pause
