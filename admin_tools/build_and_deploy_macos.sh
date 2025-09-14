#!/bin/bash
# ClausoNet 4.0 Pro - Build Admin Key Generator for macOS

echo "🍎 ============================================"
echo "🍎 ClausoNet 4.0 Pro - Build Admin Key Generator"
echo "🍎 ============================================"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script must be run on macOS!"
    echo "💡 For Windows, use build_and_deploy.bat"
    exit 1
fi

# Check if required files exist
if [ ! -f "admin_key_gui.py" ]; then
    echo "❌ admin_key_gui.py not found!"
    echo "Make sure you're running this from the admin_tools directory"
    exit 1
fi

if [ ! -f "simple_key_generator.py" ]; then
    echo "❌ simple_key_generator.py not found!"
    exit 1
fi

if [ ! -f "build_admin_key_macos.py" ]; then
    echo "❌ build_admin_key_macos.py not found!"
    echo "Please make sure all files are present"
    exit 1
fi

echo "🔍 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    echo "Please install Python or run setup_admin_env_macos.sh first"
    exit 1
fi

python3 --version
echo ""

echo "🚀 Starting build process..."
echo ""

# Run the build script
python3 build_admin_key_macos.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Build failed!"
    echo "Check the error messages above"
    exit 1
fi

echo ""
echo "🍎 ============================================"
echo "🍎 BUILD COMPLETE!"
echo "🍎 ============================================"
echo ""

# Check if files were created
if [ -d "admin_key_package_macos/ClausoNet Admin Key Generator.app" ]; then
    echo "✅ SUCCESS: .app bundle created successfully!"
    echo "📍 Location: admin_key_package_macos/"
    echo ""
    
    # List package contents
    echo "📦 Package contents:"
    ls -la admin_key_package_macos/
    echo ""
    
    # Check for DMG file
    for dmg_file in ClausoNet_AdminKeyGenerator_macOS_*.dmg; do
        if [ -f "$dmg_file" ]; then
            echo "💿 Deployment DMG: $dmg_file"
            echo "✅ Ready to copy to admin machine!"
            break
        fi
    done
    
    # Check for ZIP file (fallback)
    for zip_file in ClausoNet_AdminKeyGenerator_macOS_*.zip; do
        if [ -f "$zip_file" ]; then
            echo "📁 Deployment ZIP: $zip_file"
            echo "✅ Ready to copy to admin machine!"
            break
        fi
    done
    
else
    echo "⚠️  WARNING: .app bundle not found in admin_key_package_macos directory"
    echo "Build may have failed - check error messages above"
fi

echo ""
echo "📋 Next steps:"
echo "1. Test the .app by running: open 'admin_key_package_macos/ClausoNet Admin Key Generator.app'"
echo "2. Copy the DMG/ZIP file to the admin macOS machine"
echo "3. Mount DMG or extract ZIP"
echo "4. Run Launch_AdminKeyGenerator.sh"
echo ""
echo "🔒 Security Notes:"
echo "- First run may require security approval in System Preferences"
echo "- Use 'xattr -d com.apple.quarantine' if app appears damaged"
echo ""
echo "Press any key to exit..."
read -n 1 