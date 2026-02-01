#!/bin/bash
echo "=== project_cortex Build Script ==="

# Clean
rm -rf build
mkdir -p build

# Build function
build_component() {
    local name=$1
    local source=$2
    local extra_flags=$3
    
    echo "Building $name..."
    gcc -Wall -Wextra -O2 -std=c99 -DWINDOWS \
        $extra_flags \
        "src/c_core/$source" \
        -o "build/$name.exe" \
        -luser32 -lpsapi
    
    if [ -f "build/$name.exe" ]; then
        echo "  ✓ Success"
    else
        echo "  ✗ Failed"
    fi
}

# Build components
build_component "hotkey_daemon" "hotkey_daemon.c" ""
build_component "system_monitor" "system_monitor.c" ""

# Python bridge with Python libs
echo "Building py_bridge..."
gcc -Wall -Wextra -O2 -std=c99 -DWINDOWS \
    -I/d/miniforge/include \
    src/c_core/py_bridge.c \
    -o build/py_bridge.exe \
    -L/d/miniforge/libs -lpython312 \
    -luser32 -lpsapi

if [ -f "build/py_bridge.exe" ]; then
    echo "  ✓ Success"
else
    echo "  ✗ Failed (Python library issue?)"
fi

echo ""
echo "=== Build Results ==="
ls -la build/*.exe 2>/dev/null || echo "No executables built"

echo ""
echo "To run:"
echo "  ./build/hotkey_daemon.exe"
echo "  ./build/system_monitor.exe --daemon"
echo "  ./build/py_bridge.exe \"Your query\""
