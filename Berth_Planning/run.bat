@echo off
echo ============================================
echo   Berth Planning System - Run Development
echo ============================================
echo.
echo Starting API and React Frontend...
echo.
echo Press Ctrl+C to stop both servers.
echo.

:: Start API in background
echo [1/2] Starting API Server...
start "Berth Planning API" cmd /c "cd /d %~dp0src\BerthPlanning.API && dotnet run"

:: Wait a moment for API to start
timeout /t 3 /nobreak > nul

:: Start React Frontend
echo [2/2] Starting React Frontend...
cd /d %~dp0frontend-react
call npm start
