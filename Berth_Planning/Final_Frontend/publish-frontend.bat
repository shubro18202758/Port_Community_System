@echo off
echo ============================================
echo   Berth Planning React Frontend - Publish
echo ============================================
echo.

set PUBLISH_DIR=%~dp0publish\frontend

:: Clean publish directory
echo Cleaning publish directory...
if exist "%PUBLISH_DIR%" rmdir /s /q "%PUBLISH_DIR%"
mkdir "%PUBLISH_DIR%"
echo.

:: Build React
echo Building React Frontend...
cd /d %~dp0frontend-react
call npm run build
if %ERRORLEVEL% neq 0 (
    echo [ERROR] React build failed!
    pause
    exit /b 1
)

:: Copy build files
echo Copying build files...
xcopy /s /e /y "build\*" "%PUBLISH_DIR%\"

echo.
echo ============================================
echo   Frontend Publish completed successfully!
echo ============================================
echo.
echo Published to: %PUBLISH_DIR%
echo.
echo To deploy: Copy contents to your web server
echo.
pause
