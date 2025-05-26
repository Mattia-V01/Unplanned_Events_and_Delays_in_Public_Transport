@echo off
cd /d %~dp0

rem Step 1: Start Docker Desktop
rem Assumes Docker is installed in the default location
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

rem Step 2: Wait 10 seconds to allow Docker to fully start
timeout /t 10 >nul

rem Step 3: Define local and remote file names
set LOCAL_FILE=Dockerfile
set REMOTE_URL=https://raw.githubusercontent.com/Mattia-V01/Unplanned_Events_and_Delays_in_Public_Transport/main/Dockerfile
set TEMP_FILE=Dockerfile.temp

rem Step 4: Download the latest Dockerfile to a temporary file
echo Checking for Dockerfile updates...
powershell -Command "Invoke-WebRequest -Uri %REMOTE_URL% -OutFile %TEMP_FILE%"

rem Step 5: Compare local Dockerfile with downloaded version
fc /b %LOCAL_FILE% %TEMP_FILE% >nul 2>&1

if %errorlevel%==0 (
    echo Dockerfile is up to date. No need to re-download.
    del %TEMP_FILE%
) else (
    echo Dockerfile has changed. Updating...
    del %LOCAL_FILE%
    ren %TEMP_FILE% Dockerfile
)

rem Step 6: Check if the image already exists
docker image inspect shiny-dashboard >nul 2>&1
if errorlevel 1 (
    echo Building Docker image...
    docker build -t shiny-dashboard .
) else (
    echo Docker image already exists. Skipping build.
)

rem Step 7: Open the app in the browser
start http://localhost:8000

rem Step 8: Run the container and forward port 8000
docker run -it --rm -p 8000:8000 shiny-dashboard

rem Step 9: Keep the window open after it finishes
pause
