@echo off
chcp 65001 >nul
echo.
echo ========================================
echo    project_cortex Build System
echo ========================================
echo.

set GCC=C:\msys64\mingw64\bin\gcc.exe
set BUILD_DIR=build

echo [1] Creating directories...
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"
if not exist "src\c_core" mkdir "src\c_core"
if not exist "src\include" mkdir "src\include"

echo [2] Creating sample C files (if needed)...
if not exist "src\c_core\hotkey_daemon.c" (
    echo #include ^<stdio.h^> > "src\c_core\hotkey_daemon.c"
    echo int main^(^) { >> "src\c_core\hotkey_daemon.c"
    echo     printf^("Hotkey Daemon^n^"^); >> "src\c_core\hotkey_daemon.c"
    echo     return 0; >> "src\c_core\hotkey_daemon.c"
    echo } >> "src\c_core\hotkey_daemon.c"
)

echo [3] Building hotkey_daemon.exe...
"%GCC%" -Wall -Wextra -O2 -std=c99 -DWINDOWS ^
    "src\c_core\hotkey_daemon.c" ^
    -o "%BUILD_DIR%\hotkey_daemon.exe" ^
    -luser32 -lpsapi

if errorlevel 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo [4] Verifying build...
if exist "%BUILD_DIR%\hotkey_daemon.exe" (
    echo Success! File created.
    echo.
    echo To run: "%BUILD_DIR%\hotkey_daemon.exe"
    echo.
    echo Testing now...
    echo ==============
    "%BUILD_DIR%\hotkey_daemon.exe"
) else (
    echo ERROR: File not created!
)

echo.
pause
