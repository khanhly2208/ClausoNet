#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Build Status Summary
Tóm tắt tình trạng build và bundled ChromeDriver
"""

import os
from pathlib import Path

def main():
    """Main summary"""
    print("🚀 ClausoNet 4.0 Pro - Build Status Summary")
    print("=" * 60)

    project_dir = Path(__file__).parent

    # Check ChromeDriver bundling
    print("\n🚗 ChromeDriver Bundling Status:")

    tools_dir = project_dir / "tools" / "chromedriver"
    drivers_dir = project_dir / "drivers"

    # Check bundled ChromeDrivers
    platforms = {
        "Windows": "chromedriver.exe",
        "macOS": "chromedriver",
        "Linux": "chromedriver"
    }

    for platform, filename in platforms.items():
        platform_dir = tools_dir / platform.lower()
        if platform == "macOS":
            platform_dir = tools_dir / "macos"

        driver_path = platform_dir / filename
        if driver_path.exists():
            size_mb = driver_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ {platform}: {driver_path} ({size_mb:.1f} MB)")
        else:
            print(f"  ❌ {platform}: Not found")

    # Check build directory
    build_ready_driver = drivers_dir / "chromedriver.exe"
    if build_ready_driver.exists():
        size_mb = build_ready_driver.stat().st_size / (1024 * 1024)
        print(f"  ✅ Build Ready: {build_ready_driver} ({size_mb:.1f} MB)")
    else:
        print(f"  ❌ Build Ready: Not prepared")

    # Check build files
    print("\n📋 Build Configuration:")

    spec_file = project_dir / "clausonet_build.spec"
    build_file = project_dir / "build.py"
    entry_file = project_dir / "gui" / "main_window.py"

    files_to_check = [
        ("PyInstaller Spec", spec_file),
        ("Build Script", build_file),
        ("Entry Point", entry_file),
    ]

    for name, file_path in files_to_check:
        if file_path.exists():
            print(f"  ✅ {name}: {file_path}")
        else:
            print(f"  ❌ {name}: {file_path}")

    # Check assets
    print("\n🎨 Assets Status:")

    assets_dir = project_dir / "assets"
    asset_files = [
        ("Windows Icon", assets_dir / "icon.ico"),
        ("Source Icon", assets_dir / "icon.png"),
        ("macOS Icon", assets_dir / "icon.icns"),
    ]

    for name, file_path in asset_files:
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"  ✅ {name}: {file_path} ({size_kb:.1f} KB)")
        else:
            print(f"  ❌ {name}: {file_path}")

    # Summary
    print("\n" + "=" * 60)
    print("📊 BUILD READINESS SUMMARY")
    print("=" * 60)

    ready_count = 0
    total_count = 5

    # ChromeDriver ready
    if build_ready_driver.exists():
        print("✅ ChromeDriver: Ready for bundling")
        ready_count += 1
    else:
        print("❌ ChromeDriver: Not prepared")

    # Spec file ready
    if spec_file.exists():
        print("✅ Build Config: PyInstaller spec ready")
        ready_count += 1
    else:
        print("❌ Build Config: Missing spec file")

    # Entry point ready
    if entry_file.exists():
        print("✅ Entry Point: Main window found")
        ready_count += 1
    else:
        print("❌ Entry Point: Missing main_window.py")

    # Windows icon ready
    if (assets_dir / "icon.ico").exists():
        print("✅ Windows Icon: Ready")
        ready_count += 1
    else:
        print("❌ Windows Icon: Missing icon.ico")

    # Build script ready
    if build_file.exists():
        print("✅ Build Script: Automated build ready")
        ready_count += 1
    else:
        print("❌ Build Script: Missing build.py")

    # Final status
    percentage = (ready_count / total_count) * 100
    print(f"\n🎯 Overall Readiness: {ready_count}/{total_count} ({percentage:.0f}%)")

    if percentage == 100:
        print("🎉 READY TO BUILD! Run: python build.py all")
    elif percentage >= 80:
        print("⚠️ Almost ready - minor issues to fix")
    else:
        print("❌ Not ready - significant issues to resolve")

    # Build commands
    if percentage >= 80:
        print("\n💻 Build Commands:")
        print("   Windows EXE: python build.py all")
        print("   macOS APP:   python3 build.py all")
        print("   Test build:  python build.py build")

if __name__ == "__main__":
    main()
