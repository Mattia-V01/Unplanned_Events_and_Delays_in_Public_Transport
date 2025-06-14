@echo off
echo Starting the dashboard container...
start "" http://localhost:8000
docker run --rm -it -p 8000:8000 ^
  -v "%~dp0.":/app ^
  -w /app/App ^
  ghcr.io/mattia-v01/unplanned-delays-dashboard:latest ^
  uvicorn app:fastapi_app --host 0.0.0.0 --port 8000