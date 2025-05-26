@echo off
cd /d %~dp0
echo Building Docker image...
docker build -t shiny-dashboard .
echo Starting the app...
start http://localhost:8000
docker run -it --rm -p 8000:8000 shiny-dashboard
pause