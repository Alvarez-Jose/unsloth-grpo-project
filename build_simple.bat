@echo off
setlocal enabledelayedexpansion
echo.
echo DYNAMIC BUILD SCRIPT
echo =====================
echo.

:: --- CONFIGURATION ---
set BUILD_DIR=build
:: Try to find Python via environment variables commonly set by Miniforge/Conda/System
if defined CONDA_PREFIX (
    set PYTHON_DIR=%CONDA_PREFIX%
) else (
    :: Fallback: try to find python in PATH and get its directory
    for /f "delims=" %%i in ('where python 2^>nul') do (
        set "PYTHON_EXE=%%i"
        for %%j in ("!PYTHON_EXE!") do set "PYTHON_DIR=%%~dpj"
        goto :found_python
    )
)
:found_python
:: Remove trailing backslash if present
if "%PYTHON_DIR:~-1%"=="\" set "PYTHON_DIR=%PYTHON_DIR:~0,-1%"

:: --- Step 1: Checking tools ---
echo Step 1: Checking tools...

where gcc >nul 2>nul
if errorlevel 1 (
    echo ERROR: gcc not found in PATH. 
    echo Please install MinGW/MSYS2 and add the bin folder to your system environment variables.
    pause
    exit /b 1
)
for /f "delims=" %%i in ('where gcc') do set GCC="%%i"
echo    GCC: Found at %GCC%

if "%PYTHON_DIR%"=="" (
    echo ERROR: Python directory could not be determined.
    pause
    exit /b 1
)
echo    Python: Found at %PYTHON_DIR%

:: --- Step 2: Creating build directory ---
echo Step 2: Creating build directory...
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

:: --- Step 3: Building ---
echo Step 3: Building hotkey_daemon.exe...
%GCC% -Wall -Wextra -O2 -std=c99 -DWINDOWS ^
      -Isrc\include ^
      -I"%PYTHON_DIR%\include" ^
      src\c_core\hotkey_daemon.c ^
      -o "%BUILD_DIR%\hotkey_daemon.exe" ^
      -luser32 -lpsapi

if errorlevel 1 (
    echo.
    echo ERROR: Failed to build hotkey_daemon.exe
    pause
    exit /b 1
)
echo    Success!

:: --- Step 4: Verifying output ---
echo Step 4: Verifying output...
if exist "%BUILD_DIR%\hotkey_daemon.exe" (
    echo    File created: %BUILD_DIR%\hotkey_daemon.exe
) else (
    echo ERROR: File not created!
)

echo.
echo Done.
pause