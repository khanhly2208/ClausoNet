#!/bin/bash
echo "======================================"
echo "ClausoNet 4.0 Pro - Unix Launcher"
echo "======================================"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Python
if command_exists python3; then
    PYTHON_CMD="python3"
elif command_exists python; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found!"
    echo "Please install Python 3.8+ from https://python.org/downloads/"
    echo "Or use your system package manager:"
    echo "  macOS: brew install python3"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Python version: $PYTHON_VERSION"

# Check minimum version (3.8)
if $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "✅ Python version compatible"
else
    echo "❌ Python 3.8+ required!"
    echo "Current version: $PYTHON_VERSION"
    echo "Please upgrade Python"
    exit 1
fi

# Make script executable (in case it wasn't)
chmod +x "$0"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Launch the application
echo "🚀 Starting ClausoNet 4.0 Pro..."
$PYTHON_CMD launch.py

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Application closed with error"
    echo "Press Enter to continue..."
    read
fi
