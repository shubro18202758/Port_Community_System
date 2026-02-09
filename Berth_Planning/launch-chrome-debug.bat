@echo off
REM Launch Chrome with remote debugging enabled for Browser Agent control
REM The Browser Agent will be able to control THIS browser window!

echo =========================================
echo SmartBerth - Chrome Remote Debug Launcher
echo =========================================
echo.
echo This will launch Chrome with remote debugging enabled at port 9222.
echo The Browser Agent will be able to control this browser window directly!
echo.
echo IMPORTANT: All your actions in this browser will be visible to the agent.
echo.

REM Common Chrome paths
set CHROME_PATH=""

REM Try standard Chrome locations
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
    goto launch
)

if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    goto launch
)

if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
    goto launch
)

REM Try Edge as fallback (also supports CDP)
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    echo Chrome not found, using Microsoft Edge instead...
    set CHROME_PATH="C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    goto launch
)

if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    echo Chrome not found, using Microsoft Edge instead...
    set CHROME_PATH="C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    goto launch
)

echo ERROR: Could not find Chrome or Edge installation!
echo Please install Google Chrome or Microsoft Edge.
pause
exit /b 1

:launch
echo Launching browser with remote debugging...
echo Browser path: %CHROME_PATH%
echo.
echo Once Chrome opens:
echo   1. Navigate to http://localhost:5174 (SmartBerth frontend)
echo   2. Start the Browser Agent with connect_to_chrome=true
echo   3. Watch as the agent controls YOUR browser!
echo.

REM Create a separate user data directory to avoid conflicts with existing Chrome profile
set USER_DATA_DIR=%TEMP%\chrome-debug-profile

REM Launch Chrome with remote debugging
start "" %CHROME_PATH% --remote-debugging-port=9222 --user-data-dir="%USER_DATA_DIR%" --no-first-run http://localhost:5174

echo.
echo Chrome launched with remote debugging on port 9222
echo.
echo To start the Browser Agent in connected mode, use:
echo   POST http://localhost:8001/agent/start
echo   {
echo     "task": "Navigate to Vessels Tracking and show me the vessel list",
echo     "connect_to_chrome": true
echo   }
echo.
pause
