@echo off
echo ===================================================
echo     401k Payment Management System Launcher
echo ===================================================
echo.

REM Set the root directory to the current directory
set ROOT_DIR=%CD%

REM Launch the backend server
echo Starting backend server...
start cmd /k "cd %ROOT_DIR%\backend && echo Activating virtual environment... && call venv\Scripts\activate && echo Installing dependencies... && pip install -r requirements.txt && echo Starting backend server... && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a moment to ensure the backend starts first
timeout /t 5 /nobreak > nul

REM Launch the frontend server
echo Starting frontend server...
start cmd /k "cd %ROOT_DIR%\frontend && echo Installing dependencies... && npm install && echo Starting frontend development server... && npm run dev"

echo.
echo ===================================================
echo     Servers are starting in separate windows
echo.
echo     BACKEND: http://localhost:8000
echo     FRONTEND: http://localhost:3000
echo.
echo     Press any key to close this window...
echo ===================================================
echo.

pause > nul 