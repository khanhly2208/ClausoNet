#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Build Script
Tự động hóa việc build exe/app cho thương mại hóa
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
import tempfile
import requests
import zipfile

class ClausoNetBuilder:
    """Builder cho ClausoNet 4.0 Pro"""

    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.system = platform.system()
        self.build_dir = self.project_dir / "build"
        self.dist_dir = self.project_dir / "dist"
        self.drivers_dir = self.project_dir / "drivers"

        print(f"🏗️ ClausoNet 4.0 Pro Builder")
        print(f"📁 Project: {self.project_dir}")
        print(f"💻 Platform: {self.system}")
        print(f"🐍 Python: {platform.python_version()}")
        print("-" * 60)

    def check_dependencies(self, auto_install=True):
        """Kiểm tra dependencies cần thiết"""
        print("🔍 Checking dependencies...")

        package_imports = {
            'pyinstaller': 'PyInstaller',
            'customtkinter': 'customtkinter',
            'selenium': 'selenium',
            'webdriver-manager': 'webdriver_manager',
            'requests': 'requests',
            'pyyaml': 'yaml',
            'google-generativeai': 'google.generativeai',
            'openai': 'openai',
            'psutil': 'psutil',
            'cryptography': 'cryptography',
            'websockets': 'websockets'
        }

        missing = []
        for package, import_name in package_imports.items():
            try:
                __import__(import_name)
                print(f"  ✅ {package}")
            except ImportError:
                missing.append(package)
                print(f"  ❌ {package}")

        if missing:
            print(f"\n📦 Missing packages: {', '.join(missing)}")

            if auto_install:
                print("🔄 Auto-installing missing packages...")
                return self._install_packages(missing)
            else:
                print("Install with: pip install " + " ".join(missing))
                return False

        print("✅ All dependencies OK")
        return True

    def _install_packages(self, packages):
        """Tự động install packages"""
        try:
            import subprocess

            # Use current Python executable to ensure correct environment
            cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade'] + packages

            print(f"🚀 Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print("✅ Packages installed successfully!")
                print("🔄 Re-checking dependencies...")
                return self.check_dependencies(auto_install=False)
            else:
                print(f"❌ Installation failed:")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Installation timeout (300s)")
            return False
        except Exception as e:
            print(f"❌ Installation error: {e}")
            return False

    def clean_build(self):
        """Dọn dẹp build cũ"""
        print("🧹 Cleaning previous builds...")

        dirs_to_clean = [self.build_dir, self.dist_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"  🗑️ Removed {dir_path}")

        print("✅ Build cleanup complete")
        return True

    def prepare_chromedriver(self):
        """Chuẩn bị ChromeDriver cho build - sử dụng ChromeDriver có sẵn"""
        print("🚗 Preparing ChromeDriver...")

        self.drivers_dir.mkdir(exist_ok=True)

        # Determine driver filename
        if self.system == "Windows":
            driver_name = "chromedriver.exe"
        else:
            driver_name = "chromedriver"

        driver_path = self.drivers_dir / driver_name

        # Check if already exists
        if driver_path.exists():
            print(f"  ✅ ChromeDriver already exists: {driver_path}")
            return True

        # Look for bundled ChromeDriver in project
        bundled_locations = [
            # Priority order: tools > bundled_drivers > drivers > bin > root
            self.project_dir / "tools" / "chromedriver" / driver_name,
            self.project_dir / "tools" / "chromedriver" / "windows" / driver_name if self.system == "Windows" else
            self.project_dir / "tools" / "chromedriver" / "macos" / driver_name if self.system == "Darwin" else
            self.project_dir / "tools" / "chromedriver" / "linux" / driver_name,
            self.project_dir / "bundled_drivers" / driver_name,
            self.project_dir / "drivers" / driver_name,
            self.project_dir / "bin" / driver_name,
            self.project_dir / driver_name
        ]

        # Also check platform-specific directories
        if self.system == "Windows":
            bundled_locations.extend([
                self.project_dir / "tools" / "windows" / driver_name,
                self.project_dir / "bundled_drivers" / "windows" / driver_name
            ])
        elif self.system == "Darwin":
            bundled_locations.extend([
                self.project_dir / "tools" / "macos" / driver_name,
                self.project_dir / "bundled_drivers" / "macos" / driver_name
            ])
        else:
            bundled_locations.extend([
                self.project_dir / "tools" / "linux" / driver_name,
                self.project_dir / "bundled_drivers" / "linux" / driver_name
            ])

        # Try to find bundled ChromeDriver
        bundled_driver = None
        for location in bundled_locations:
            if location.exists():
                bundled_driver = location
                print(f"  🔍 Found bundled ChromeDriver: {bundled_driver}")
                break

        if bundled_driver:
            # Copy bundled driver to drivers directory
            try:
                shutil.copy2(bundled_driver, driver_path)

                # Set executable permissions on Unix systems
                if self.system in ["Darwin", "Linux"]:
                    os.chmod(driver_path, 0o755)

                print(f"  ✅ ChromeDriver copied: {driver_path}")
                return True

            except Exception as e:
                print(f"  ❌ Failed to copy ChromeDriver: {e}")
                return False
        else:
            print(f"  ❌ ChromeDriver not found in bundled locations:")
            for location in bundled_locations:
                print(f"     - {location}")
            print(f"  💡 Please place {driver_name} in one of the above locations")
            return False

    def _get_chrome_version(self):
        """Lấy Chrome version"""
        try:
            if self.system == "Windows":
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                ]
            elif self.system == "Darwin":
                chrome_paths = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
            else:
                chrome_paths = ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable"]

            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    result = subprocess.run([chrome_path, "--version"],
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        version_text = result.stdout.strip()
                        # Extract major version
                        version = version_text.split()[-1]
                        major_version = version.split('.')[0]
                        return major_version
        except:
            pass

        # Fallback
        return "120"

    def create_assets(self):
        """Tạo assets cần thiết"""
        print("🎨 Creating assets...")

        assets_dir = self.project_dir / "assets"
        assets_dir.mkdir(exist_ok=True)

        # Check và tạo icons
        icon_status = self._check_and_create_icons(assets_dir)

        if icon_status:
            print("  ✅ Assets OK")
        else:
            print("  ⚠️ Some assets missing but build can continue")

        return True

    def _check_and_create_icons(self, assets_dir):
        """Kiểm tra và tạo icons cho các platform"""
        all_good = True

        # Windows icon
        if self.system == "Windows":
            icon_ico = assets_dir / "icon.ico"
            if icon_ico.exists():
                print(f"  ✅ Windows icon found: {icon_ico}")
            else:
                print(f"  ⚠️ Windows icon missing: {icon_ico}")
                # Try to create from PNG
                icon_png = assets_dir / "icon.png"
                if icon_png.exists():
                    if self._create_ico_from_png(icon_png, icon_ico):
                        print(f"  ✅ Created Windows icon from PNG")
                    else:
                        print(f"  ⚠️ Could not create Windows icon")
                        all_good = False
                else:
                    all_good = False

        # macOS icon
        elif self.system == "Darwin":
            icon_icns = assets_dir / "icon.icns"
            if icon_icns.exists():
                print(f"  ✅ macOS icon found: {icon_icns}")
            else:
                print(f"  ⚠️ macOS icon missing: {icon_icns}")
                # Try to create from PNG
                icon_png = assets_dir / "icon.png"
                if icon_png.exists():
                    if self._create_icns_from_png(icon_png, icon_icns):
                        print(f"  ✅ Created macOS icon from PNG")
                    else:
                        print(f"  ⚠️ Could not create macOS icon")
                        all_good = False
                else:
                    all_good = False

        return all_good

    def _create_ico_from_png(self, png_path, ico_path):
        """Tạo .ico từ .png (Windows)"""
        try:
            from PIL import Image
            img = Image.open(png_path)
            img.save(ico_path, format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
            return True
        except ImportError:
            print("    ⚠️ PIL/Pillow not available for icon conversion")
            return False
        except Exception as e:
            print(f"    ❌ Icon conversion error: {e}")
            return False

    def _create_icns_from_png(self, png_path, icns_path):
        """Tạo .icns từ .png (macOS)"""
        try:
            # Method 1: Use iconutil (macOS only)
            if self.system == "Darwin":
                iconset_dir = png_path.parent / "icon.iconset"
                iconset_dir.mkdir(exist_ok=True)

                # Create different sizes
                sizes = [16, 32, 64, 128, 256, 512, 1024]

                from PIL import Image
                img = Image.open(png_path)

                for size in sizes:
                    resized = img.resize((size, size), Image.Resampling.LANCZOS)
                    resized.save(iconset_dir / f"icon_{size}x{size}.png")
                    if size <= 512:  # Create @2x versions
                        resized.save(iconset_dir / f"icon_{size//2}x{size//2}@2x.png")

                # Use iconutil to create .icns
                result = subprocess.run(['iconutil', '-c', 'icns', str(iconset_dir), '-o', str(icns_path)],
                                      capture_output=True, text=True)

                if result.returncode == 0:
                    shutil.rmtree(iconset_dir)  # Cleanup
                    return True
                else:
                    print(f"    ❌ iconutil failed: {result.stderr}")
                    return False

            return False

        except ImportError:
            print("    ⚠️ PIL/Pillow not available for icon conversion")
            return False
        except Exception as e:
            print(f"    ❌ Icon conversion error: {e}")
            return False

    def build_executable(self):
        """Build executable với PyInstaller"""
        print("🔨 Building executable...")

        spec_file = self.project_dir / "clausonet_build.spec"
        if not spec_file.exists():
            print(f"  ❌ Spec file not found: {spec_file}")
            return False

        # PyInstaller command
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            str(spec_file)
        ]

        print(f"  🚀 Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, cwd=str(self.project_dir),
                                  capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                print("  ✅ Build successful!")

                # Show build info
                if self.system == "Windows":
                    exe_path = self.dist_dir / "ClausoNet4.0Pro.exe"
                    if exe_path.exists():
                        size_mb = self._get_size_mb(exe_path)
                        print(f"  📊 Executable: {exe_path} ({size_mb:.1f} MB)")
                elif self.system == "Darwin":
                    app_path = self.dist_dir / "ClausoNet 4.0 Pro.app"
                    if app_path.exists():
                        size_mb = self._get_size_mb(app_path)
                        print(f"  📊 App Bundle: {app_path} ({size_mb:.1f} MB)")

                return True
            else:
                print(f"  ❌ Build failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("  ❌ Build timeout")
            return False
        except Exception as e:
            print(f"  ❌ Build error: {e}")
            return False

        print("\n💡 Next steps:")
        print("1. Test the executable thoroughly")
        print("2. Create installer (NSIS/InstallShield for Windows)")
        print("3. Code signing for distribution")
        print("4. Create DMG for macOS distribution")

    def _get_size_mb(self, path):
        """Lấy kích thước file/folder theo MB"""
        if path.is_file():
            return path.stat().st_size / (1024 * 1024)
        elif path.is_dir():
            total = 0
            for item in path.rglob("*"):
                if item.is_file():
                    total += item.stat().st_size
            return total / (1024 * 1024)
        return 0

    def run_tests(self):
        """Chạy tests cơ bản"""
        print("🧪 Running basic tests...")

        # Test import các module chính
        test_modules = [
            'gui.main_window',
            'utils.resource_manager',
            'utils.production_chrome_manager',
            'utils.profile_manager'
        ]

        for module in test_modules:
            try:
                __import__(module)
                print(f"  ✅ {module}")
            except Exception as e:
                print(f"  ❌ {module}: {e}")
                return False

        print("✅ Basic tests passed")
        return True

    def build_all(self):
        """Build toàn bộ"""
        print("🚀 Starting full build process...")
        print("="*60)

        steps = [
            ("Check dependencies", self.check_dependencies),
            ("Prepare ChromeDriver", self.prepare_chromedriver),
            ("Create assets", self.create_assets),
            ("Run tests", self.run_tests),
            ("Clean previous builds", self.clean_build),
            ("Build executable", self.build_executable),
        ]

        for step_name, step_func in steps:
            print(f"\n📋 Step: {step_name}")
            if not step_func():
                print(f"❌ Failed at: {step_name}")
                return False

        print("\n" + "="*60)
        print("🎉 BUILD COMPLETE!")
        print("="*60)
        return True

def main():
    """Main function"""
    builder = ClausoNetBuilder()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "clean":
            builder.clean_build()
        elif command == "test":
            builder.run_tests()
        elif command == "chromedriver":
            builder.prepare_chromedriver()
        elif command == "build":
            builder.build_executable()
        elif command == "all":
            builder.build_all()
        else:
            print("❌ Unknown command:", command)
            print("Usage: python build.py [clean|test|chromedriver|build|all]")
    else:
        # Default: build all
        builder.build_all()

if __name__ == "__main__":
    main()
