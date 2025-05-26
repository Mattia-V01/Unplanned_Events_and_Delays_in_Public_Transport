@echo off
start http://127.0.0.1:8000
docker run -it --rm -p 8000:8000 -w /app/App shiny-dashboard uvicorn app:fastapi_app --host 0.0.0.0 --port 8000 --reload
pause
