#!/bin/bash
# ClausoNet 4.0 Pro - macOS Environment Setup for Main Application

echo "🍎 =========================================="
echo "🍎 ClausoNet 4.0 Pro - macOS Environment Setup"
echo "🍎 =========================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script must be run on macOS!"
    exit 1
fi

echo "🖥️  Platform: macOS $(sw_vers -productVersion)"
echo "🏗️  Setting up build environment for ClausoNet 4.0 Pro"
echo ""

# Check if we're in the right directory
if [ ! -f "clausonet_build.spec" ]; then
    echo "❌ clausonet_build.spec not found!"
    echo "Make sure you're running this from the ClausoNet4.0 directory"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo ""
    echo "💡 Install Python 3.8+ from:"
    echo "   - https://python.org (recommended)"
    echo "   - or use Homebrew: brew install python"
    echo ""
    echo "🔗 Homebrew installation:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
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

# Check for Homebrew (recommended but optional)
if command -v brew &> /dev/null; then
    echo "✅ Homebrew found:"
    brew --version | head -1
    
    # Offer to install ChromeDriver via Homebrew
    echo ""
    read -p "🚗 Install ChromeDriver via Homebrew? (y/n): " install_chromedriver
    if [[ $install_chromedriver =~ ^[Yy]$ ]]; then
        echo "📦 Installing ChromeDriver..."
        brew install chromedriver
        if [ $? -eq 0 ]; then
            echo "✅ ChromeDriver installed via Homebrew"
            # Create symlink in project directory
            mkdir -p drivers
            ln -sf $(which chromedriver) drivers/chromedriver 2>/dev/null
            echo "🔗 Created symlink in drivers/ directory"
        else
            echo "⚠️  ChromeDriver installation failed"
        fi
    fi
    echo ""
else
    echo "⚠️  Homebrew not found (optional but recommended)"
    echo "💡 Install from: https://brew.sh"
    echo ""
fi

# Update pip first
echo "🔄 Updating pip..."
pip3 install --upgrade pip
if [ $? -ne 0 ]; then
    echo "⚠️  Failed to upgrade pip (continuing anyway)"
fi

echo ""
echo "📦 Installing ClausoNet 4.0 Pro dependencies..."
echo ""

# Core build dependencies
echo "🔨 Installing build tools..."
pip3 install "pyinstaller>=5.13.0"
if [ $? -ne 0 ]; then
    echo "❌ Failed to install PyInstaller"
    exit 1
fi

# GUI framework
echo "🎨 Installing GUI framework..."
pip3 install "customtkinter>=5.2.0"
if [ $? -ne 0 ]; then
    echo "❌ Failed to install CustomTkinter"
    exit 1
fi

# Web automation
echo "🌐 Installing web automation tools..."
pip3 install "selenium>=4.15.0"
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Selenium"
    exit 1
fi

# HTTP client
echo "🌍 Installing HTTP client..."
pip3 install "requests>=2.31.0"
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Requests"
    exit 1
fi

# Image processing
echo "🖼️  Installing image processing..."
pip3 install "pillow>=10.0.0"
if [ $? -ne 0 ]; then
    echo "⚠️  Failed to install Pillow (continuing anyway)"
fi

# Additional dependencies
echo "📚 Installing additional dependencies..."
additional_deps=("beautifulsoup4" "lxml" "certifi" "urllib3")
for dep in "${additional_deps[@]}"; do
    pip3 install "$dep" 2>/dev/null || echo "⚠️  Failed to install $dep (optional)"
done

echo ""
echo "🔍 Checking macOS development tools..."

# Check Xcode Command Line Tools
if command -v xcode-select &> /dev/null; then
    if xcode-select -p &> /dev/null; then
        echo "✅ Xcode Command Line Tools installed"
    else
        echo "⚠️  Xcode Command Line Tools not properly configured"
        read -p "📱 Install Xcode Command Line Tools? (y/n): " install_xcode
        if [[ $install_xcode =~ ^[Yy]$ ]]; then
            xcode-select --install
            echo "💡 Complete the installation in the popup dialog"
        fi
    fi
else
    echo "⚠️  Xcode Command Line Tools not found"
    echo "💡 Some features may not work properly"
fi

# Check macOS development tools
echo ""
echo "🛠️  Checking macOS tools..."

tools_status=()

# Check iconutil
if command -v iconutil &> /dev/null; then
    echo "✅ iconutil (icon creation)"
    tools_status+=("iconutil:✅")
else
    echo "❌ iconutil not found"
    tools_status+=("iconutil:❌")
fi

# Check sips
if command -v sips &> /dev/null; then
    echo "✅ sips (image processing)"
    tools_status+=("sips:✅")
else
    echo "❌ sips not found"
    tools_status+=("sips:❌")
fi

# Check hdiutil
if command -v hdiutil &> /dev/null; then
    echo "✅ hdiutil (DMG creation)"
    tools_status+=("hdiutil:✅")
else
    echo "❌ hdiutil not found"
    tools_status+=("hdiutil:❌")
fi

# Check codesign (optional)
if command -v codesign &> /dev/null; then
    echo "✅ codesign (code signing - optional)"
    tools_status+=("codesign:✅")
else
    echo "⚠️  codesign not found (optional)"
    tools_status+=("codesign:⚠️")
fi

echo ""
echo "📁 Setting up project directories..."

# Create required directories if they don't exist
directories=("assets" "drivers" "tools/chromedriver" "output" "logs" "cache")
for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "📂 Created: $dir/"
    else
        echo "✅ Exists: $dir/"
    fi
done

# Check ChromeDriver setup
echo ""
echo "🚗 ChromeDriver setup..."
chromedriver_locations=("drivers/chromedriver" "tools/chromedriver/chromedriver")
chromedriver_found=false

for location in "${chromedriver_locations[@]}"; do
    if [ -f "$location" ]; then
        echo "✅ ChromeDriver found: $location"
        chromedriver_found=true
        break
    fi
done

if [ "$chromedriver_found" = false ]; then
    echo "⚠️  ChromeDriver not found in project directories"
    echo ""
    echo "💡 Download ChromeDriver for macOS:"
    echo "   1. Visit: https://chromedriver.chromium.org/"
    echo "   2. Download version matching your Chrome browser"
    echo "   3. Extract and place in: drivers/chromedriver"
    echo "   4. Make executable: chmod +x drivers/chromedriver"
    echo ""
    echo "🍺 Or install via Homebrew:"
    echo "   brew install chromedriver"
fi

echo ""
echo "🍎 =========================================="
echo "🍎 SETUP COMPLETE!"
echo "🍎 =========================================="
echo ""

# Show summary
echo "📊 Setup Summary:"
echo "   🐍 Python: $(python3 --version 2>&1)"
echo "   📦 pip: $(pip3 --version 2>&1 | cut -d' ' -f1-2)"

for status in "${tools_status[@]}"; do
    tool=$(echo $status | cut -d':' -f1)
    result=$(echo $status | cut -d':' -f2)
    echo "   🛠️  $tool: $result"
done

echo ""
echo "📋 Next steps:"
echo "1. Build main application:"
echo "   python3 build_main_macos.py"
echo ""
echo "2. Or use simple shell script:"
echo "   chmod +x build_macos.sh && ./build_macos.sh"
echo ""
echo "3. Test the application:"
echo "   python3 gui/main_window.py"
echo ""

if [ "$chromedriver_found" = false ]; then
    echo "⚠️  Important: Download ChromeDriver before building!"
    echo "   The application requires ChromeDriver for web automation"
fi

echo ""
echo "🔒 Security Notes:"
echo "   - First .app run may require security approval"
echo "   - Use 'System Preferences → Security & Privacy' to allow"
echo "   - Or run: xattr -d com.apple.quarantine 'ClausoNet 4.0 Pro.app'"
echo ""
echo "📞 Support:"
echo "   - Documentation: README.md"
echo "   - Issues: Check error logs in logs/ directory"
echo "   - Email: support@clausonet.com"
echo ""
echo "Press any key to exit..."
read -n 1 