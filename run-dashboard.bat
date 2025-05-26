@echo off
setlocal

rem Define main folder on C:
set ROOT_DIR=C:\Unplanned_Events_and_Delays_in_Public_Transport

rem Create folder if it does not exist
if not exist "%ROOT_DIR%" (
    mkdir "%ROOT_DIR%"
)

rem Step 1: Start Docker Desktop
start "" "C:\Program Files\Docker\Docker Desktop.exe"
timeout /t 10 >nul

rem Step 2: Download and update Dockerfile and arequirements
set DOCKERFILE=%ROOT_DIR%\Dockerfile
set REQFILE=%ROOT_DIR%\arequirements

set DOCKERFILE_URL=https://raw.githubusercontent.com/Mattia-V01/Unplanned_Events_and_Delays_in_Public_Transport/main/Dockerfile
set REQFILE_URL=https://raw.githubusercontent.com/Mattia-V01/Unplanned_Events_and_Delays_in_Public_Transport/main/arequirements

set DOCKERFILE_TEMP=%ROOT_DIR%\Dockerfile.temp
set REQFILE_TEMP=%ROOT_DIR%\arequirements.temp

echo Checking for Dockerfile updates...
powershell -Command "Invoke-WebRequest -Uri %DOCKERFILE_URL% -OutFile %DOCKERFILE_TEMP%"
powershell -Command "Invoke-WebRequest -Uri %REQFILE_URL% -OutFile %REQFILE_TEMP%"

fc /b "%DOCKERFILE%" "%DOCKERFILE_TEMP%" >nul 2>&1
if %errorlevel%==0 (
    del "%DOCKERFILE_TEMP%"
    echo Dockerfile is up to date.
) else (
    del "%DOCKERFILE%"
    ren "%DOCKERFILE_TEMP%" Dockerfile
    echo Dockerfile updated.
)

fc /b "%REQFILE%" "%REQFILE_TEMP%" >nul 2>&1
if %errorlevel%==0 (
    del "%REQFILE_TEMP%"
    echo arequirements is up to date.
) else (
    del "%REQFILE%"
    ren "%REQFILE_TEMP%" arequirements
    echo arequirements updated.
)

rem Step 3: Clone GitHub repo inside C:\Unplanned_Events_and_Delays_in_Public_Transport if missing
cd /d "%ROOT_DIR%"
if not exist "App\" (
    echo Cloning full repository into C...
    git clone https://github.com/Mattia-V01/Unplanned_Events_and_Delays_in_Public_Transport.git tempclone
    xcopy /E /I /Y tempclone\* .\
    rmdir /S /Q tempclone
) else (
    echo Repository already exists. Skipping clone.
)

rem Step 4: Build image if not already built
docker image inspect shiny-dashboard >nul 2>&1
if errorlevel 1 (
    echo Building Docker image...
    docker build -t shiny-dashboard .
) else (
    echo Docker image already exists. Skipping build.
)

rem Step 5: Run app and open browser
start http://localhost:8000
docker run -it --rm -p 8000:8000 shiny-dashboard

pause
endlocal
