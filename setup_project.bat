@echo off
chcp 65001 >nul
echo ========================================
echo    Project Cortex Setup
echo ========================================
echo.

REM Delete old venv if exists
if exist venv (
    echo Removing old virtual environment...
    rmdir /s /q venv
)

REM Create new venv
echo Creating virtual environment...
python -m venv venv

REM Activate
echo Activating environment...
call venv\Scripts\activate.bat

REM Verify
echo Verifying activation...
python -c "import sys; print('Virtual environment active:', sys.prefix != sys.base_prefix)"

REM Install
echo Installing project...
pip install -e .

echo.
echo ========================================
echo    SETUP COMPLETE!
echo ========================================
echo.
echo To run the project:
echo   1. Open Command Prompt
echo   2. cd /d "C:\project_cortex"
echo   3. venv\Scripts\activate.bat
echo   4. python -m src.main
echo.
pause