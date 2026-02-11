.PHONY: install setup build clean test

install:
    pip install -e .[dev]

setup:
    @echo "Detecting OS..."
    @if [ "$(OS)" = "Windows_NT" ]; then \
        powershell -ExecutionPolicy Bypass -File scripts/setup_env.ps1; \
    else \
        chmod +x scripts/setup_env.sh && ./scripts/setup_env.sh; \
    fi

build:
    python setup.py build_ext --inplace

clean:
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info/
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -delete

test:
    python -m pytest tests/ -v

run:
    python -m src.main

help:
    @echo "Available commands:"
    @echo "  make setup    - Set up development environment"
    @echo "  make install  - Install Python dependencies"
    @echo "  make build    - Build C extensions"
    @echo "  make clean    - Clean build artifacts"
    @echo "  make test     - Run tests"
    @echo "  make run      - Run the application"