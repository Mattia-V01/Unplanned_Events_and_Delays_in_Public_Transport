@echo off
setlocal

:: === Configuration ===
set IMAGE_NAME=shiny-dashboard
set DESKTOP_PATH=%USERPROFILE%\Desktop

:: === Build Docker image ===
echo Building Docker image...
docker build -t %IMAGE_NAME% .

:: === Run container to generate the launcher on the desktop ===
echo Creating run-dashboard.bat on your Desktop...
docker run --rm -v "%DESKTOP_PATH%:C:\desktop" %IMAGE_NAME%

echo Done! You can now double-click "run-dashboard.bat" on your Desktop to start the app.
pause
endlocal
