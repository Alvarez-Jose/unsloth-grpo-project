# project_cortex Build Instructions

## Requirements
- MSYS2 with MinGW64 (gcc)
- Python 3.12+ (for py_bridge)

## Building
1. Open MinGW64 terminal (C:\msys64\mingw64.exe)
2. Navigate to project: `cd /c/project_cortex`
3. Run: `./build.sh`

## Running
Executables are in `build/` directory:
- `hotkey_daemon.exe` - Hotkey management
- `system_monitor.exe` --daemon - System monitoring
- `py_bridge.exe "query"` - Python integration bridge

## Notes
- Use MinGW64 terminal for building
- Use PowerShell or cmd for running executables
- Python bridge requires Python development files
