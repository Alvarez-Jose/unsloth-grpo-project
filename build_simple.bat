@echo off
echo.
echo MINIMAL BUILD SCRIPT
echo ====================
echo.

REM Use full paths - no environment variables
set GCC="C:\msys64\mingw64\bin\gcc.exe"
set PYTHON_DIR="D:\miniforge"
set BUILD_DIR="build"

echo Step 1: Checking tools...
if not exist %GCC% (
    echo ERROR: GCC not found at %GCC%
    pause
    exit /b 1
)
echo   GCC: OK

echo Step 2: Creating build directory...
if not exist %BUILD_DIR% mkdir %BUILD_DIR%

echo Step 3: Building hotkey_daemon.exe...
%GCC% -Wall -Wextra -O2 -std=c99 -DWINDOWS ^
      -Isrc\include ^
      -I%PYTHON_DIR%\include ^
      src\c_core\hotkey_daemon.c ^
      -o %BUILD_DIR%\hotkey_daemon.exe ^
      -luser32 -lpsapi

if errorlevel 1 (
    echo ERROR: Failed to build hotkey_daemon.exe
    pause
    exit /b 1
)
echo   Success!

echo Step 4: Verifying output...
if exist %BUILD_DIR%\hotkey_daemon.exe (
    echo   File created: %BUILD_DIR%\hotkey_daemon.exe
    dir /w %BUILD_DIR%\hotkey_daemon.exe
) else (
    echo ERROR: File not created!
)

echo.
echo ====================
echo If you see errors above, press any key to see details...
pause >nul

echo.
echo Debug information:
echo GCC command: %GCC% --version
%GCC% --version
echo.
echo Python include: %PYTHON_DIR%\include\Python.h
if exist %PYTHON_DIR%\include\Python.h (echo   EXISTS) else (echo   MISSING)
echo.
echo Source file: src\c_core\hotkey_daemon.c
if exist src\c_core\hotkey_daemon.c (echo   EXISTS) else (echo   MISSING)

echo.
pause
