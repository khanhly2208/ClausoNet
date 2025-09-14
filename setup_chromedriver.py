#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - ChromeDriver Setup
One-time setup để download ChromeDriver cho tất cả platforms
"""

import os
import sys
import platform
import requests
import zipfile
import shutil
from pathlib import Path

class ChromeDriverSetup:
    """Setup ChromeDriver cho tất cả platforms"""

    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.tools_dir = self.project_dir / "tools" / "chromedriver"
        self.tools_dir.mkdir(parents=True, exist_ok=True)

        print("🚗 ClausoNet 4.0 Pro - ChromeDriver Setup")
        print(f"📁 Tools directory: {self.tools_dir}")
        print("-" * 50)

    def setup_all_platforms(self):
        """Setup ChromeDriver cho tất cả platforms"""
        print("🌍 Setting up ChromeDriver for all platforms...")

        # Chrome version để download (stable)
        chrome_version = "120.0.6099.109"

        platforms = {
            "windows": {
                "url_suffix": "win32.zip",
                "executable": "chromedriver.exe",
                "folder": "windows"
            },
            "macos": {
                "url_suffix": "mac64.zip",
                "executable": "chromedriver",
                "folder": "macos"
            },
            "linux": {
                "url_suffix": "linux64.zip",
                "executable": "chromedriver",
                "folder": "linux"
            }
        }

        success_count = 0

        for platform_name, info in platforms.items():
            print(f"\n📦 Setting up {platform_name.upper()}...")

            platform_dir = self.tools_dir / info["folder"]
            platform_dir.mkdir(exist_ok=True)

            driver_path = platform_dir / info["executable"]

            if driver_path.exists():
                print(f"  ✅ {platform_name} ChromeDriver already exists")
                success_count += 1
                continue

            # Download
            download_url = f"https://chromedriver.storage.googleapis.com/{chrome_version}/chromedriver_{info['url_suffix']}"

            try:
                print(f"  📥 Downloading from: {download_url}")
                response = requests.get(download_url, timeout=30)

                if response.status_code == 200:
                    # Save zip
                    zip_path = platform_dir / "chromedriver.zip"
                    with open(zip_path, 'wb') as f:
                        f.write(response.content)

                    # Extract
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(platform_dir)

                    # Set executable permissions (for Unix)
                    if platform_name in ["macos", "linux"]:
                        os.chmod(driver_path, 0o755)

                    # Cleanup
                    zip_path.unlink()

                    print(f"  ✅ {platform_name} ChromeDriver setup complete")
                    success_count += 1

                else:
                    print(f"  ❌ Download failed: HTTP {response.status_code}")

            except Exception as e:
                print(f"  ❌ Setup failed: {e}")

        print(f"\n🎯 Setup complete: {success_count}/3 platforms ready")

        if success_count == 3:
            print("✅ All platforms ready for build!")
        else:
            print("⚠️ Some platforms failed - build may not work on all systems")

        return success_count == 3

    def setup_current_platform_only(self):
        """Setup ChromeDriver chỉ cho platform hiện tại"""
        current_system = platform.system()

        print(f"🖥️ Setting up ChromeDriver for current platform: {current_system}")

        if current_system == "Windows":
            platform_info = {
                "url_suffix": "win32.zip",
                "executable": "chromedriver.exe",
                "folder": "windows"
            }
        elif current_system == "Darwin":
            platform_info = {
                "url_suffix": "mac-x64.zip",
                "executable": "chromedriver",
                "folder": "macos"
            }
        else:
            platform_info = {
                "url_suffix": "linux64.zip",
                "executable": "chromedriver",
                "folder": "linux"
            }

        platform_dir = self.tools_dir / platform_info["folder"]
        platform_dir.mkdir(exist_ok=True)

        driver_path = platform_dir / platform_info["executable"]

        if driver_path.exists():
            print(f"  ✅ ChromeDriver already exists: {driver_path}")
            return True

        # Try multiple Chrome versions (latest stable versions)
        chrome_versions = ["131.0.6778.85", "130.0.6723.116", "129.0.6668.89", "128.0.6613.137"]

        for chrome_version in chrome_versions:
            download_url = f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}/win32/chromedriver-win32.zip"

            if current_system == "Darwin":
                download_url = f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}/mac-x64/chromedriver-mac-x64.zip"
            elif current_system == "Linux":
                download_url = f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}/linux64/chromedriver-linux64.zip"

            try:
                print(f"  📥 Trying version {chrome_version}...")
                response = requests.get(download_url, timeout=30)

                if response.status_code == 200:
                    # Save and extract
                    zip_path = platform_dir / "chromedriver.zip"
                    with open(zip_path, 'wb') as f:
                        f.write(response.content)

                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(platform_dir)

                    # Find the actual chromedriver executable in extracted folders
                    extracted_driver = None
                    for item in platform_dir.rglob(platform_info["executable"]):
                        if item.is_file():
                            extracted_driver = item
                            break

                    if extracted_driver:
                        # Move to correct location
                        shutil.move(str(extracted_driver), str(driver_path))

                        # Set permissions
                        if current_system in ["Darwin", "Linux"]:
                            os.chmod(driver_path, 0o755)

                        # Cleanup
                        zip_path.unlink()

                        # Remove extracted folders
                        for item in platform_dir.iterdir():
                            if item.is_dir():
                                shutil.rmtree(item)

                        print(f"  ✅ ChromeDriver setup complete: {driver_path}")
                        return True
                    else:
                        print(f"  ❌ ChromeDriver executable not found in zip")
                        zip_path.unlink()
                else:
                    print(f"  ⚠️ Version {chrome_version} not available (HTTP {response.status_code})")

            except Exception as e:
                print(f"  ❌ Version {chrome_version} failed: {e}")

        print(f"  ❌ All versions failed")
        return False

    def list_available_drivers(self):
        """Liệt kê ChromeDriver có sẵn"""
        print("📋 Available ChromeDrivers:")

        platforms = ["windows", "macos", "linux"]
        executables = ["chromedriver.exe", "chromedriver", "chromedriver"]

        for platform_name, executable in zip(platforms, executables):
            driver_path = self.tools_dir / platform_name / executable
            if driver_path.exists():
                size_mb = driver_path.stat().st_size / (1024 * 1024)
                print(f"  ✅ {platform_name}: {driver_path} ({size_mb:.1f} MB)")
            else:
                print(f"  ❌ {platform_name}: Not found")

def main():
    """Main function"""
    setup = ChromeDriverSetup()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "all":
            setup.setup_all_platforms()
        elif command == "current":
            setup.setup_current_platform_only()
        elif command == "list":
            setup.list_available_drivers()
        else:
            print("❌ Unknown command:", command)
            print("Usage: python setup_chromedriver.py [all|current|list]")
    else:
        # Default: setup current platform
        setup.setup_current_platform_only()

if __name__ == "__main__":
    main()
