@echo off
cd /d "%~dp0"
echo ========================================
echo   Stopping old service on port 5000
echo ========================================
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >NUL 2>NUL
)
echo.
echo ========================================
echo   Starting service
echo   http://localhost:5000
echo ========================================
echo.
python server.py
pause
