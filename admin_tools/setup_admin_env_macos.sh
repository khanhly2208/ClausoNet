#!/bin/bash
# ClausoNet 4.0 Pro - Admin Environment Setup for macOS

echo "🍎 ========================================"
echo "🍎 ClausoNet 4.0 Pro - macOS Admin Setup"
echo "🍎 ========================================"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script must be run on macOS!"
    exit 1
fi

echo "🖥️  Platform: macOS $(sw_vers -productVersion)"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "💡 Please install Python 3.8+ from:"
    echo "   - https://python.org"
    echo "   - or use Homebrew: brew install python"
    exit 1
fi

echo "✅ Python found:"
python3 --version
echo ""

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not available!"
    echo "💡 Please reinstall Python with pip included"
    exit 1
fi

echo "✅ pip3 found:"
pip3 --version
echo ""

# Check for Homebrew (optional but recommended)
if command -v brew &> /dev/null; then
    echo "✅ Homebrew found:"
    brew --version | head -1
    echo ""
else
    echo "⚠️  Homebrew not found (optional)"
    echo "💡 Consider installing from: https://brew.sh"
    echo ""
fi

# Install required packages
echo "📦 Installing required packages..."
echo ""

# Update pip first
echo "🔄 Updating pip..."
pip3 install --upgrade pip
if [ $? -ne 0 ]; then
    echo "⚠️  Failed to upgrade pip (continuing anyway)"
fi

# Install customtkinter
echo "🎨 Installing CustomTkinter..."
pip3 install "customtkinter>=5.2.0"
if [ $? -ne 0 ]; then
    echo "❌ Failed to install customtkinter"
    exit 1
fi

# Install PyInstaller
echo "📦 Installing PyInstaller..."
pip3 install "pyinstaller>=5.13.0"
if [ $? -ne 0 ]; then
    echo "❌ Failed to install pyinstaller"
    exit 1
fi

# Install Pillow (for icon creation)
echo "🖼️  Installing Pillow..."
pip3 install "pillow>=10.0.0"
if [ $? -ne 0 ]; then
    echo "⚠️  Failed to install pillow (optional)"
    echo "This is not critical, continuing..."
fi

# Check macOS specific tools
echo ""
echo "🔍 Checking macOS tools..."

# Check iconutil
if command -v iconutil &> /dev/null; then
    echo "✅ iconutil (icon creation)"
else
    echo "⚠️  iconutil not found"
fi

# Check codesign
if command -v codesign &> /dev/null; then
    echo "✅ codesign (code signing)"
else
    echo "⚠️  codesign not found"
fi

# Check hdiutil
if command -v hdiutil &> /dev/null; then
    echo "✅ hdiutil (DMG creation)"
else
    echo "⚠️  hdiutil not found"
fi

# Check sips
if command -v sips &> /dev/null; then
    echo "✅ sips (image processing)"
else
    echo "⚠️  sips not found"
fi

echo ""
echo "🍎 ========================================"
echo "🍎 SETUP COMPLETE!"
echo "🍎 ========================================"
echo ""
echo "📋 Next steps:"
echo "1. Run: python3 build_admin_key_macos.py"
echo "2. Or test first: python3 admin_key_gui.py"
echo ""
echo "💡 Additional setup (optional):"
echo "- Install Xcode Command Line Tools: xcode-select --install"
echo "- Install Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
echo ""
echo "🔒 Security Notes:"
echo "- First run may require security approval"
echo "- Use 'System Preferences → Security & Privacy' to allow"
echo ""
echo "Press any key to exit..."
read -n 1 