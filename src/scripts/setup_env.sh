#!/bin/bash

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -e .[dev]

# Install system dependencies based on OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Linux detected"
    # Install Linux dependencies
    sudo apt-get update
    sudo apt-get install -y build-essential python3-dev
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macOS detected"
    # Install macOS dependencies
    brew install python3
fi

echo "Setup complete! Activate with: source venv/bin/activate"