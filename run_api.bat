@echo off
setlocal EnableDelayedExpansion

echo Launching Evil-Force-JWT API Server...

:: Create necessary directories if they don't exist
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "api" mkdir api
if not exist "ai_system\logs" mkdir ai_system\logs

:: Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo Virtual environment activated.
) else (
    echo No virtual environment found. Continuing without activation.
)

:: Check Python installation
python --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in the PATH.
    echo Please install Python 3.7 or higher.
    pause
    exit /b 1
)

:: Install required packages if missing
echo Checking required packages...
python -c "import flask" > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing Flask...
    pip install flask flask-cors
)

:: Set port (default: 5000)
set PORT=5000
if not "%1"=="" set PORT=%1

:: Run the API server
echo Starting API server on port %PORT%...
set PORT=%PORT%
python api/jwt_api.py

:: Deactivate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\deactivate.bat
)

echo.
echo API Server stopped.
pause 