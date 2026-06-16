@echo off
echo Building protected version of EVIL_JWT_FORCE...

REM Activate virtual environment if it exists
if exist "evil_jwt_env\Scripts\activate.bat" (
    call evil_jwt_env\Scripts\activate.bat
)

REM Install required packages
python -m pip install -r requirements.txt

REM Run the protected build
python scripts/build_protected.py

REM Check if build was successful
if %ERRORLEVEL% EQU 0 (
    echo Build completed successfully!
    echo Protected version is available in build_protected directory
) else (
    echo Build failed!
    exit /b 1
)

REM Deactivate virtual environment if it was activated
if exist "evil_jwt_env\Scripts\deactivate.bat" (
    call evil_jwt_env\Scripts\deactivate.bat
) 