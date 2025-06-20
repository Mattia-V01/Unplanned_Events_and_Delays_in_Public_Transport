@echo off
echo Starting the dashboard container...

REM Check if the Docker image already exists locally
docker image inspect ghcr.io/mattia-v01/unplanned-delays-dashboard:latest >nul 2>&1
IF ERRORLEVEL 1 (
    echo Docker image not found locally. Pulling from GitHub Container Registry...
    docker pull ghcr.io/mattia-v01/unplanned-delays-dashboard:latest
) ELSE (
    echo Docker image found locally.
)

REM Open the app in the default web browser
start "" http://localhost:8000

REM Run the container with volume mounting and correct working directory
docker run --rm -it -p 8000:8000 ^
  -v "%~dp0.":/app ^
  -w /app/App ^
  ghcr.io/mattia-v01/unplanned-delays-dashboard:latest ^
  uvicorn app:fastapi_app --host 0.0.0.0 --port 8000

pause
