# Makefile for project_cortex
CC = gcc
CFLAGS = -Wall -Wextra -O2 -std=c99 -DWINDOWS
LDFLAGS = -luser32 -lpsapi -ladvapi32
PYTHON_DIR = /d/miniforge
PYTHON_CFLAGS = -I$(PYTHON_DIR)/include
PYTHON_LIBS = -L$(PYTHON_DIR)/libs -lpython312

BUILD_DIR = build
SRC_DIR = src/c_core
INCLUDE_DIR = src/include

TARGETS = $(BUILD_DIR)/hotkey_daemon.exe \
          $(BUILD_DIR)/system_monitor.exe \
          $(BUILD_DIR)/py_bridge.exe

.PHONY: all clean run-hotkey run-monitor test-bridge help

all: $(TARGETS)

$(BUILD_DIR)/hotkey_daemon.exe: $(SRC_DIR)/hotkey_daemon.c
	@echo "Building hotkey_daemon..."
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) $< -o $@ $(LDFLAGS)
	@echo "  ✓ Built: $@"

$(BUILD_DIR)/system_monitor.exe: $(SRC_DIR)/system_monitor.c
	@echo "Building system_monitor..."
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) $< -o $@ $(LDFLAGS)
	@echo "  ✓ Built: $@"

$(BUILD_DIR)/py_bridge.exe: $(SRC_DIR)/py_bridge.c
	@echo "Building py_bridge..."
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) $(PYTHON_CFLAGS) $< -o $@ $(PYTHON_LIBS) $(LDFLAGS)
	@echo "  ✓ Built: $@"

clean:
	@echo "Cleaning build directory..."
	rm -rf $(BUILD_DIR)
	@echo "  ✓ Cleaned"

run-hotkey: $(BUILD_DIR)/hotkey_daemon.exe
	@echo "Running hotkey daemon (Ctrl+C to exit)..."
	./$(BUILD_DIR)/hotkey_daemon.exe

run-monitor: $(BUILD_DIR)/system_monitor.exe
	@echo "Running system monitor..."
	./$(BUILD_DIR)/system_monitor.exe --daemon

test-bridge: $(BUILD_DIR)/py_bridge.exe
	@echo "Testing Python bridge..."
	./$(BUILD_DIR)/py_bridge.exe "What's using my memory?"

help:
	@echo "=== project_cortex Build Commands ==="
	@echo "make all          - Build all executables"
	@echo "make clean        - Remove build files"
	@echo "make run-hotkey   - Build and run hotkey daemon"
	@echo "make run-monitor  - Build and run system monitor"
	@echo "make test-bridge  - Build and test Python bridge"
	@echo "make help         - Show this help"
EOF