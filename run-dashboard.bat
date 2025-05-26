@echo off
cd /d %~dp0

rem Step 1: Start Docker Desktop
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

rem Step 2: Wait for Docker to fully start
timeout /t 10 >nul

rem Step 3: Set remote file URLs and local filenames
set DOCKERFILE=Dockerfile
set REQFILE=arequirements

set DOCKERFILE_URL=https://raw.githubusercontent.com/Mattia-V01/Unplanned_Events_and_Delays_in_Public_Transport/main/Dockerfile
set REQFILE_URL=https://raw.githubusercontent.com/Mattia-V01/Unplanned_Events_and_Delays_in_Public_Transport/main/arequirements

set DOCKERFILE_TEMP=Dockerfile.temp
set REQFILE_TEMP=arequirements.temp

rem Step 4: Download the latest versions to temporary files
echo Checking for updates...
powershell -Command "Invoke-WebRequest -Uri %DOCKERFILE_URL% -OutFile %DOCKERFILE_TEMP%"
powershell -Command "Invoke-WebRequest -Uri %REQFILE_URL% -OutFile %REQFILE_TEMP%"

rem Step 5: Compare Dockerfile
fc /b %DOCKERFILE% %DOCKERFILE_TEMP% >nul 2>&1
if %errorlevel%==0 (
    echo Dockerfile is up to date.
    del %DOCKERFILE_TEMP%
) else (
    echo Dockerfile has changed. Updating...
    del %DOCKERFILE%
    ren %DOCKERFILE_TEMP% Dockerfile
)

rem Step 6: Compare arequirements
fc /b %REQFILE% %REQFILE_TEMP% >nul 2>&1
if %errorlevel%==0 (
    echo arequirements is up to date.
    del %REQFILE_TEMP%
) else (
    echo arequirements has changed. Updating...
    del %REQFILE%
    ren %REQFILE_TEMP% arequirements
)

rem Step 7: Check if Docker image already exists
docker image inspect shiny-dashboard >nul 2>&1
if errorlevel 1 (
    echo Building Docker image...
    docker build -t shiny-dashboard .
) else (
    echo Docker image already exists. Skipping build.
)

rem Step 8: Open browser and run container
start http://localhost:8000
docker run -it --rm -p 8000:8000 shiny-dashboard

pause
