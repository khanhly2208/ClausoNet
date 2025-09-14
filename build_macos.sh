#!/bin/bash
# ClausoNet 4.0 Pro - macOS Build Script
# Build main application (main_window.py) for macOS

echo "🍎 ============================================"
echo "🍎 ClausoNet 4.0 Pro - macOS Build Script"
echo "🍎 ============================================"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script must be run on macOS!"
    echo "💡 For Windows, use build_fixed_exe.py or build.py"
    exit 1
fi

echo "🖥️  Platform: macOS $(sw_vers -productVersion)"
echo "📁 Project directory: $(pwd)"
echo ""

# Check if we're in the right directory
if [ ! -f "clausonet_build.spec" ]; then
    echo "❌ clausonet_build.spec not found!"
    echo "Make sure you're running this from the ClausoNet4.0 directory"
    exit 1
fi

if [ ! -f "gui/main_window.py" ]; then
    echo "❌ gui/main_window.py not found!"
    echo "Make sure the GUI directory exists"
    exit 1
fi

# Check Python installation
echo "🔍 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    echo "Please install Python 3.8+ from python.org or use Homebrew"
    exit 1
fi

python3 --version
echo ""

# Check PyInstaller
echo "🔍 Checking PyInstaller..."
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "❌ PyInstaller not found!"
    echo "Installing PyInstaller..."
    pip3 install pyinstaller>=5.13.0
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install PyInstaller"
        exit 1
    fi
fi

# Check CustomTkinter
echo "🔍 Checking CustomTkinter..."
if ! python3 -c "import customtkinter" 2>/dev/null; then
    echo "❌ CustomTkinter not found!"
    echo "Installing CustomTkinter..."
    pip3 install customtkinter>=5.2.0
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install CustomTkinter"
        exit 1
    fi
fi

# Check other dependencies
echo "🔍 Checking other dependencies..."
dependencies=("selenium" "requests" "pillow")
for dep in "${dependencies[@]}"; do
    if ! python3 -c "import $dep" 2>/dev/null; then
        echo "⚠️  $dep not found, installing..."
        pip3 install "$dep"
    fi
done

echo ""

# Check for required assets
echo "🎨 Checking assets..."
if [ ! -d "assets" ]; then
    echo "⚠️  Assets directory not found, creating..."
    mkdir -p assets
fi

# Check/create icon
if [ ! -f "assets/icon.icns" ]; then
    echo "🖼️  macOS icon not found, checking for PNG..."
    if [ -f "assets/icon.png" ]; then
        echo "📝 Converting PNG to ICNS..."
        # Create iconset
        mkdir -p "assets/icon.iconset"
        
        # Create different sizes
        sips -z 16 16 "assets/icon.png" --out "assets/icon.iconset/icon_16x16.png" 2>/dev/null
        sips -z 32 32 "assets/icon.png" --out "assets/icon.iconset/icon_16x16@2x.png" 2>/dev/null
        sips -z 32 32 "assets/icon.png" --out "assets/icon.iconset/icon_32x32.png" 2>/dev/null
        sips -z 64 64 "assets/icon.png" --out "assets/icon.iconset/icon_32x32@2x.png" 2>/dev/null
        sips -z 128 128 "assets/icon.png" --out "assets/icon.iconset/icon_128x128.png" 2>/dev/null
        sips -z 256 256 "assets/icon.png" --out "assets/icon.iconset/icon_128x128@2x.png" 2>/dev/null
        sips -z 256 256 "assets/icon.png" --out "assets/icon.iconset/icon_256x256.png" 2>/dev/null
        sips -z 512 512 "assets/icon.png" --out "assets/icon.iconset/icon_256x256@2x.png" 2>/dev/null
        sips -z 512 512 "assets/icon.png" --out "assets/icon.iconset/icon_512x512.png" 2>/dev/null
        sips -z 1024 1024 "assets/icon.png" --out "assets/icon.iconset/icon_512x512@2x.png" 2>/dev/null
        
        # Convert to icns
        iconutil -c icns "assets/icon.iconset" -o "assets/icon.icns"
        rm -rf "assets/icon.iconset"
        
        if [ -f "assets/icon.icns" ]; then
            echo "✅ Created macOS icon"
        else
            echo "⚠️  Could not create icon, continuing without"
        fi
    else
        echo "⚠️  No icon found, app will use default"
    fi
else
    echo "✅ macOS icon found"
fi

# Check ChromeDriver
echo "🚗 Checking ChromeDriver..."
if [ ! -f "drivers/chromedriver" ] && [ ! -f "tools/chromedriver/chromedriver" ]; then
    echo "⚠️  ChromeDriver not found"
    echo "💡 Please download ChromeDriver for macOS and place in drivers/ or tools/chromedriver/"
    echo "    Download from: https://chromedriver.chromium.org/"
else
    echo "✅ ChromeDriver found"
fi

echo ""

# Clean previous builds
echo "🗑️  Cleaning previous builds..."
rm -rf build/
rm -rf dist/
echo "✅ Cleaned build directories"

echo ""

# Run PyInstaller build
echo "🔨 Building ClausoNet 4.0 Pro for macOS..."
echo "🚀 Running PyInstaller with clausonet_build.spec..."
echo ""

python3 -m PyInstaller --clean --noconfirm clausonet_build.spec

if [ $? -eq 0 ]; then
    echo ""
    echo "🍎 ============================================"
    echo "🍎 BUILD COMPLETE!"
    echo "🍎 ============================================"
    echo ""
    
    # Check if .app was created
    if [ -d "dist/ClausoNet 4.0 Pro.app" ]; then
        echo "✅ SUCCESS: ClausoNet 4.0 Pro.app created!"
        echo "📍 Location: dist/ClausoNet 4.0 Pro.app"
        
        # Get app size
        app_size=$(du -sh "dist/ClausoNet 4.0 Pro.app" | cut -f1)
        echo "📏 App bundle size: $app_size"
        echo ""
        
        # List contents
        echo "📦 Build output:"
        ls -la dist/
        echo ""
        
        # Create DMG for distribution
        echo "💿 Creating DMG for distribution..."
        dmg_name="ClausoNet_4.0_Pro_macOS_$(date +%Y%m%d_%H%M%S).dmg"
        
        hdiutil create -srcfolder "dist/ClausoNet 4.0 Pro.app" \
                      -volname "ClausoNet 4.0 Pro" \
                      -format UDZO \
                      -imagekey zlib-level=9 \
                      "$dmg_name" 2>/dev/null
        
        if [ -f "$dmg_name" ]; then
            dmg_size=$(du -sh "$dmg_name" | cut -f1)
            echo "✅ Created DMG: $dmg_name ($dmg_size)"
        else
            echo "⚠️  Could not create DMG, but .app is ready"
        fi
        
        echo ""
        echo "📋 Next steps:"
        echo "1. Test the app: open 'dist/ClausoNet 4.0 Pro.app'"
        echo "2. Copy to Applications: cp -r 'dist/ClausoNet 4.0 Pro.app' /Applications/"
        echo "3. Distribute DMG file to other macOS users"
        echo ""
        echo "🔒 Security Notes:"
        echo "- First run may show Gatekeeper warning"
        echo "- Right-click → Open → Open anyway to bypass"
        echo "- Or use: xattr -d com.apple.quarantine 'ClausoNet 4.0 Pro.app'"
        echo ""
        echo "🎯 Build successful for macOS!"
        
    else
        echo "❌ .app bundle not found in dist directory"
        echo "Build may have failed - check error messages above"
        
        if [ -d "dist" ]; then
            echo ""
            echo "Available files in dist:"
            ls -la dist/
        fi
    fi
    
else
    echo ""
    echo "❌ BUILD FAILED!"
    echo "Check the error messages above"
    echo ""
    echo "💡 Common fixes:"
    echo "- Install missing dependencies: pip3 install -r requirements.txt"
    echo "- Update PyInstaller: pip3 install --upgrade pyinstaller"
    echo "- Check Python version: python3 --version (need 3.8+)"
    exit 1
fi

echo ""
echo "Press any key to exit..."
read -n 1
