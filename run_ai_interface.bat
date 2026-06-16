@echo off
setlocal EnableDelayedExpansion

echo Launching Evil-Force-JWT AI Interface...

:: Create necessary directories if they don't exist
if not exist "data" mkdir data
if not exist "logs" mkdir logs
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
python -c "import tkinter" > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing tkinter...
    pip install tk
)

python -c "import PIL" > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing pillow...
    pip install pillow
)

:: Run the AI interface
python gui/ai_interface.py

:: Deactivate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\deactivate.bat
)

echo.
echo AI Interface closed.
pause 