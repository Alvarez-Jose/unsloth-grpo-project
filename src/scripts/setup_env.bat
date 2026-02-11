@echo off

REM Create virtual environment
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install Python dependencies
pip install -e .

REM Install Windows build tools if needed
where cl >nul 2>nul
if errorlevel 1 (
    echo Installing Microsoft Build Tools...
    REM Add commands to install VS Build Tools
)

echo Setup complete! Activate with: venv\Scripts\activate.bat