@echo off
echo ============================================
echo   Berth Planning API - Run
echo ============================================
echo.
echo Starting API at https://localhost:7185 (HTTPS) and http://localhost:5185 (HTTP)
echo Scalar UI: https://localhost:7185/scalar/v1
echo.

cd /d %~dp0src\BerthPlanning.API
dotnet run --launch-profile https
