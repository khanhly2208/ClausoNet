#!/bin/bash

# ClausoNet 4.0 Pro - Linux/macOS Installer

echo "========================================"
echo "ClausoNet 4.0 Pro - Unix Installer"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.8+ first"
    exit 1
fi

echo "🐍 Python detected"
python3 --version

echo
echo "🚀 Starting installation..."
echo

# Run the Python installer
python3 install.py

echo
echo "Installation script completed."
