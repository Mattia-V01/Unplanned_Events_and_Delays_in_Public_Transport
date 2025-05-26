@echo off
setlocal

rem === SET YOUR TOKEN HERE ===
set GITHUB_TOKEN=ghp_yourGitHubTokenHere1234567890abcdef
set GITHUB_USER=Mattia-V01

rem === Configuration ===
set ROOT_DIR=C:\Unplanned_Events_and_Delays_in_Public_Transport
set REPO_NAME=Unplanned_Events_and_Delays_in_Public_Transport
set REPO_URL=https://%GITHUB_USER%:%GITHUB_TOKEN%@github.com/%GITHUB_USER%/%REPO_NAME%.git
set DOCKERFILE_URL=https://raw.githubusercontent.com/%GITHUB_USER%/%REPO_NAME%/main/Dockerfile
set REQFILE_URL=https://raw.githubusercontent.com/%GITHUB_USER%/%REPO_NAME%/main/requirements

set DOCKERFILE=%ROOT_DIR%\Dockerfile
set DOCKERFILE_TEMP=%ROOT_DIR%\Dockerfile.temp
set REQFILE=%ROOT_DIR%\requirements
set REQFILE_TEMP=%ROOT_DIR%\requirements.temp

rem === Step 1: Create root folder if needed ===
if not exist "%ROOT_DIR%" (
    mkdir "%ROOT_DIR%"
)

rem === Step 2: Start Docker Desktop (adjust path if needed) ===
echo Starting Docker Desktop...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
timeout /t 10 >nul

rem === Step 3: Download Dockerfile and requirements with token ===
echo Checking for updated Dockerfile and requirements...

powershell -Command "(New-Object Net.WebClient).Headers.Add('Authorization', 'token %GITHUB_TOKEN%'); (New-Object Net.WebClient).DownloadFile('%DOCKERFILE_URL%', '%DOCKERFILE_TEMP%')"
powershell -Command "(New-Object Net.WebClient).Headers.Add('Authorization', 'token %GITHUB_TOKEN%'); (New-Object Net.WebClient).DownloadFile('%REQFILE_URL%', '%REQFILE_TEMP%')"

fc /b "%DOCKERFILE%" "%DOCKERFILE_TEMP%" >nul 2>&1
if %errorlevel%==0 (
    echo Dockerfile is up to date.
    del "%DOCKERFILE_TEMP%"
) else (
    echo Updating Dockerfile...
    del "%DOCKERFILE%"
    ren "%DOCKERFILE_TEMP%" Dockerfile
)

fc /b "%REQFILE%" "%REQFILE_TEMP%" >nul 2>&1
if %errorlevel%==0 (
    echo requirements is up to date.
    del "%REQFILE_TEMP%"
) else (
    echo Updating requirements...
    del "%REQFILE%"
    ren "%REQFILE_TEMP%" requirements
)

rem === Step 4: Clone the repo with token if not already cloned ===
cd /d "%ROOT_DIR%"
if not exist "App\" (
    echo Cloning repository with token...
    git clone %REPO_URL% tempclone
    xcopy /E /I /Y tempclone\* .\
    rmdir /S /Q tempclone
) else (
    echo Repository already exists. Skipping clone.
)

rem === Step 5: Build Docker image if needed ===
docker image inspect shiny-dashboard >nul 2>&1
if errorlevel 1 (
    echo Building Docker image...
    docker build -t shiny-dashboard .
) else (
    echo Docker image already exists. Skipping build.
)

rem === Step 6: Run app and open browser ===
start http://localhost:8000
docker run -it --rm -p 8000:8000 shiny-dashboard

pause
endlocal
