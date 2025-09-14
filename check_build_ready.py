#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Build Readiness Checker
Kiểm tra tình trạng sẵn sàng build
"""

import os
import sys
import platform
from pathlib import Path

def check_files():
    """Kiểm tra files cần thiết"""
    print("📁 Checking required files...")

    project_dir = Path(__file__).parent
    required_files = [
        "clausonet_build.spec",
        "build.py",
        "gui/main_window.py",
        "config.yaml",
        "assets/icon.ico",
        "assets/icon.png"
    ]

    missing = []
    for file_path in required_files:
        full_path = project_dir / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            missing.append(file_path)

    return len(missing) == 0, missing

def check_dependencies():
    """Kiểm tra dependencies"""
    print("\n🔍 Checking Python dependencies...")

    package_imports = {
        'pyinstaller': 'PyInstaller',
        'customtkinter': 'customtkinter',
        'selenium': 'selenium',
        'requests': 'requests',
        'pyyaml': 'yaml',
        'psutil': 'psutil',
        'cryptography': 'cryptography'
    }

    missing = []
    for package, import_name in package_imports.items():
        try:
            __import__(import_name)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing.append(package)

    return len(missing) == 0, missing

def check_platform_specific():
    """Kiểm tra platform specific requirements"""
    print(f"\n🖥️ Platform specific checks ({platform.system()})...")

    issues = []

    if platform.system() == "Windows":
        icon_ico = Path(__file__).parent / "assets" / "icon.ico"
        if icon_ico.exists():
            print("  ✅ Windows icon (icon.ico) found")
        else:
            print("  ⚠️ Windows icon (icon.ico) missing")
            issues.append("Windows icon missing")

    elif platform.system() == "Darwin":
        icon_icns = Path(__file__).parent / "assets" / "icon.icns"
        if icon_icns.exists():
            print("  ✅ macOS icon (icon.icns) found")
        else:
            print("  ⚠️ macOS icon (icon.icns) missing - can be auto-created")

        # Check for iconutil (macOS tool)
        try:
            import subprocess
            result = subprocess.run(['which', 'iconutil'], capture_output=True)
            if result.returncode == 0:
                print("  ✅ iconutil available for icon creation")
            else:
                print("  ⚠️ iconutil not found - manual icon creation needed")
        except:
            print("  ⚠️ Cannot check iconutil availability")

    return len(issues) == 0, issues

def main():
    """Main check function"""
    print("🚀 ClausoNet 4.0 Pro - Build Readiness Check")
    print("=" * 50)

    # Check files
    files_ok, missing_files = check_files()

    # Check dependencies
    deps_ok, missing_deps = check_dependencies()

    # Check platform specific
    platform_ok, platform_issues = check_platform_specific()

    # Summary
    print("\n" + "=" * 50)
    print("📊 BUILD READINESS SUMMARY")
    print("=" * 50)

    if files_ok:
        print("✅ Required files: OK")
    else:
        print(f"❌ Required files: Missing {len(missing_files)} files")
        for file in missing_files:
            print(f"   - {file}")

    if deps_ok:
        print("✅ Dependencies: OK")
    else:
        print(f"❌ Dependencies: Missing {len(missing_deps)} packages")
        print(f"   Install with: pip install {' '.join(missing_deps)}")

    if platform_ok:
        print(f"✅ Platform ({platform.system()}): OK")
    else:
        print(f"⚠️ Platform ({platform.system()}): Issues found")
        for issue in platform_issues:
            print(f"   - {issue}")

    # Overall status
    if files_ok and deps_ok:
        if platform_ok:
            print("\n🎉 BUILD READY: 100% - Can build immediately!")
            print("   Run: python build.py all")
        else:
            print("\n⚠️ BUILD READY: 90% - Minor issues, can still build")
            print("   Run: python build.py all")
    else:
        print("\n❌ BUILD NOT READY - Fix issues above first")
        if not deps_ok:
            print("   Run: pip install " + " ".join(missing_deps))

    return 0 if (files_ok and deps_ok) else 1

if __name__ == "__main__":
    sys.exit(main())
