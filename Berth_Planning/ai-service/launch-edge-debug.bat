@echo off
REM Launch Microsoft Edge with CDP (Chrome DevTools Protocol) debugging enabled
REM This allows the Browser Agent to control your visible Edge browser

echo Starting Microsoft Edge with remote debugging enabled on port 9222...
echo.
echo IMPORTANT: Close all existing Edge windows first for best results!
echo.

start msedge --remote-debugging-port=9222 http://localhost:5174

echo.
echo Edge launched with debugging enabled.
echo The Browser Agent can now control your browser!
echo.
echo To use: Make sure "Control my browser" is checked in the Browser Agent panel.
pause
