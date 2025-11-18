@echo off
REM --------------------------------------
REM Albert PBIAssistant - Start Backend
REM --------------------------------------

REM Change directory to the backend folder
cd /d "%~dp0\backend"

echo Starting Albert's Power BI Assistant backend...
echo.

REM Start Uvicorn with auto-reload in a new CMD window
start cmd /k "python -m uvicorn main:app --reload"

echo.
echo Backend started. You can close this window, the backend runs in the new CMD window.
pause
