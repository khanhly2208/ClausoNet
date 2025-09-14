#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Universal Launcher
Cross-platform launcher with automatic system detection and setup
Launcher đa nền tảng với tự động phát hiện và thiết lập hệ thống
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def setup_python_path():
    """Setup Python path for imports"""
    app_root = Path(__file__).parent
    if str(app_root) not in sys.path:
        sys.path.insert(0, str(app_root))

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required!")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        print("   Please upgrade Python: https://python.org/downloads/")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def check_and_install_dependencies():
    """Check and install required dependencies"""
    required_packages = [
        'customtkinter',
        'selenium', 
        'webdriver-manager',
        'requests',
        'pyyaml',
        'tkinter'  # Usually built-in but check anyway
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
            else:
                __import__(package)
            print(f"✅ {package} - Available")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        
        # Fix package names for pip
        pip_packages = []
        for pkg in missing_packages:
            if pkg == 'customtkinter':
                pip_packages.append('customtkinter')
            elif pkg == 'webdriver-manager':
                pip_packages.append('webdriver-manager')
            elif pkg == 'pyyaml':
                pip_packages.append('PyYAML')
            elif pkg == 'tkinter':
                # tkinter is usually built-in, skip or suggest system install
                print("⚠️ tkinter missing - may need system package install")
                if platform.system() == "Linux":
                    print("   Try: sudo apt-get install python3-tk")
                continue
            else:
                pip_packages.append(pkg)
        
        if pip_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + pip_packages)
                print("✅ Dependencies installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install dependencies: {e}")
                print("   Please install manually:")
                for pkg in pip_packages:
                    print(f"     pip install {pkg}")
                return False
    
    return True

def launch_application():
    """Launch the main application"""
    try:
        print("🚀 Launching ClausoNet 4.0 Pro...")
        
        # Import and run
        from gui.main_window import ClausoNetGUI
        
        app = ClausoNetGUI()
        app.run()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Launch error: {e}")
        return False
    
    return True

def show_system_info():
    """Show system information"""
    print("💻 System Information:")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   Architecture: {platform.machine()}")
    print(f"   Python: {platform.python_version()}")
    print(f"   Platform: {platform.platform()}")
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"   Virtual Environment: {sys.prefix}")
    else:
        print("   Virtual Environment: None")

def main():
    """Main launcher function"""
    print("🎯 ClausoNet 4.0 Pro - Universal Launcher")
    print("=" * 50)
    
    # Setup paths
    setup_python_path()
    
    # Show system info
    show_system_info()
    print()
    
    # Check Python version
    if not check_python_version():
        input("Press Enter to exit...")
        return 1
    
    print()
    
    # Check dependencies
    print("📦 Checking dependencies...")
    if not check_and_install_dependencies():
        print("\n❌ Dependency check failed!")
        input("Press Enter to exit...")
        return 1
    
    print()
    
    # Launch application
    if not launch_application():
        print("\n❌ Application launch failed!")
        input("Press Enter to exit...")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⛔ Launch cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)
