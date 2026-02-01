# First, delete the corrupted make.bat
Remove-Item make.bat -ErrorAction SilentlyContinue

# Create clean make.bat
$makeBatContent = @'
@echo off
setlocal enabledelayedexpansion

echo.
echo project_cortex Build System
echo ===========================
echo.

REM Configuration
set BUILD_DIR=build
set BIN_DIR=%BUILD_DIR%\bin
set OBJ_DIR=%BUILD_DIR%\obj
set SRC_DIR=src\c_core
set INCLUDE_DIR=src\include
set PYTHON_DIR=D:\miniforge
set GCC_PATH=C:\msys64\mingw64\bin\gcc.exe

echo [1] Checking dependencies...
if not exist "%GCC_PATH%" (
    echo ERROR: gcc not found at %GCC_PATH%
    pause
    exit /b 1
)
echo   GCC: OK

if not exist "%PYTHON_DIR%\include\Python.h" (
    echo ERROR: Python.h not found
    pause
    exit /b 1
)
echo   Python: OK

echo [2] Creating directories...
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"
if not exist "%OBJ_DIR%" mkdir "%OBJ_DIR%"

echo [3] Building executables...

REM Compiler flags
set CFLAGS=-Wall -Wextra -O2 -std=c99 -DWINDOWS -I"%INCLUDE_DIR%" -I"%PYTHON_DIR%\include"
set LDFLAGS=-luser32 -lpsapi
set PYTHON_LIBS=-L"%PYTHON_DIR%\libs" -lpython312

REM Build hotkey_daemon
echo   Building hotkey_daemon.exe...
"%GCC_PATH%" %CFLAGS% "%SRC_DIR%\hotkey_daemon.c" -o "%BIN_DIR%\hotkey_daemon.exe" %LDFLAGS%
if errorlevel 1 goto error

REM Build system_monitor
echo   Building system_monitor.exe...
"%GCC_PATH%" %CFLAGS% "%SRC_DIR%\system_monitor.c" -o "%BIN_DIR%\system_monitor.exe" %LDFLAGS%
if errorlevel 1 goto error

REM Build py_bridge
echo   Building py_bridge.exe...
"%GCC_PATH%" %CFLAGS% "%SRC_DIR%\py_bridge.c" -o "%BIN_DIR%\py_bridge.exe" %PYTHON_LIBS% %LDFLAGS%
if errorlevel 1 goto error

echo.
echo ===========================
echo BUILD SUCCESSFUL!
echo ===========================
echo.
echo Files created in %BIN_DIR%:
dir /B "%BIN_DIR%\*.exe"
echo.
echo To run:
echo   %BIN_DIR%\hotkey_daemon.exe
echo   %BIN_DIR%\system_monitor.exe --daemon
echo   %BIN_DIR%\py_bridge.exe "Test query"
echo.
pause
goto end

:error
echo.
echo BUILD FAILED!
echo.
pause
exit /b 1

:end
'@

# Save the clean make.bat
$makeBatContent | Out-File -FilePath make.bat -Encoding ascii
Write-Host "Created clean make.bat" -ForegroundColor Green