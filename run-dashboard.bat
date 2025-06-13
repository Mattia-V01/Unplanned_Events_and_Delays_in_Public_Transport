@echo off
echo Starting the dashboard container...
echo.

:: Check if Docker is running
docker info >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker is not running or not installed.
    pause
    exit /b 1
)

:: Wait 3 seconds before opening the browser
timeout /t 3 /nobreak >nul
start "" http://localhost:8000

:: Run the Docker image
docker run --rm -it -p 8000:8000 ghcr.io/mattia-v01/unplanned-delays-dashboard:latest

pause
