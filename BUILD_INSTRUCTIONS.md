# project_cortex Build Instructions

## INSTALL PREREQUISITES
# Install Python 3.11.9 (recommended)
https://www.python.org/downloads/

# Install MSYS2 for C compilation
https://www.msys2.org/

# After MSYS2 installation, run in MSYS2 terminal:
pacman -Syu
pacman -S --needed base-devel mingw-w64-x86_64-toolchain

## ONE-COMMAND SETUP
# Copy & paste this in PowerShell:
python -m venv venv; .\venv\Scripts\activate.bat; Remove-Item Function:\python, Function:\pip -ErrorAction SilentlyContinue -Force; pip install -e .; python -c "from loguru import logger; print('Setup complete!')"

## BUILD INSTRUCTIONS
# Open MSYS2 MinGW64 terminal (C:\msys64\mingw64.exe)
cd /c/project_cortex
./build.sh

# If build.sh doesn't exist, run manually:
mkdir -p build
cd build
cmake -G "MinGW Makefiles" ..
make

## RUNNING THE SYSTEM
# Option A: Run AI System (Python)
# 1. Activate virtual environment
.\venv\Scripts\activate.bat

# 2. Run the AI system
python run_ai.py

# Option B: Run Individual Components
# Hotkey management
.\build\hotkey_daemon.exe

# System monitoring (as daemon)
.\build\system_monitor.exe --daemon

# Python AI bridge
.\build\py_bridge.exe "your query here"

# Interactive AI chat
python interactive_ai.py

# Option C: Test Everything
# Diagnostic check
python diagnostic.py

# Quick import test
python -c "from c_core.etw_monitor import SystemEvent; print('AI system ready!')