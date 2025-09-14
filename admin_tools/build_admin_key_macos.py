#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Admin Key GUI Builder for macOS
Script để build Admin Key Generator GUI thành file .app bundle trên macOS
"""

import os
import sys
import subprocess
import shutil
import json
import platform
from pathlib import Path
from datetime import datetime

class AdminKeyBuilderMacOS:
    """Builder cho Admin Key Generator GUI trên macOS"""
    
    def __init__(self):
        self.admin_tools_dir = Path(__file__).parent
        self.project_dir = self.admin_tools_dir.parent
        self.build_dir = self.admin_tools_dir / "build"
        self.dist_dir = self.admin_tools_dir / "dist"
        self.package_dir = self.admin_tools_dir / "admin_key_package_macos"
        
        print("🍎 ClausoNet 4.0 Pro - Admin Key GUI Builder for macOS")
        print("=" * 60)
        print(f"🖥️  Platform: {platform.system()} {platform.release()}")
        print(f"📁 Admin tools directory: {self.admin_tools_dir}")
        print(f"📁 Project directory: {self.project_dir}")
        
        # Check if running on macOS
        if platform.system() != "Darwin":
            print("❌ This script must be run on macOS!")
            sys.exit(1)
        
    def check_dependencies(self):
        """Kiểm tra các dependency cần thiết cho macOS"""
        print("\n🔍 Checking macOS dependencies...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            print(f"❌ Python version {python_version.major}.{python_version.minor} is too old")
            print("💡 Please upgrade to Python 3.8+")
            return False
        else:
            print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Check PyInstaller
        try:
            import PyInstaller
            print(f"✅ PyInstaller {PyInstaller.__version__}")
        except ImportError:
            print("❌ PyInstaller not found")
            print("💡 Install with: pip install pyinstaller")
            return False
            
        # Check customtkinter
        try:
            import customtkinter as ctk
            print(f"✅ CustomTkinter {ctk.__version__}")
        except ImportError:
            print("❌ CustomTkinter not found")
            print("💡 Install with: pip install customtkinter")
            return False
        except AttributeError:
            print("✅ CustomTkinter (version unknown)")
            
        # Check tkinter (should be built-in)
        try:
            import tkinter
            print("✅ Tkinter available")
        except ImportError:
            print("❌ Tkinter not found")
            print("💡 Reinstall Python with tkinter support")
            return False
            
        # Check macOS specific tools
        tools_to_check = [
            ('iconutil', 'Icon creation tool'),
            ('codesign', 'Code signing tool'),
            ('pkgbuild', 'Package builder'),
        ]
        
        for tool, description in tools_to_check:
            try:
                result = subprocess.run(['which', tool], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ {tool} ({description})")
                else:
                    print(f"⚠️ {tool} not found - {description}")
            except Exception:
                print(f"⚠️ Cannot check {tool}")
        
        # Check required files
        required_files = [
            self.admin_tools_dir / "admin_key_gui.py",
            self.admin_tools_dir / "simple_key_generator.py"
        ]
        
        for file_path in required_files:
            if file_path.exists():
                print(f"✅ {file_path.name} found")
            else:
                print(f"❌ {file_path.name} not found")
                return False
        
        return True
        
    def create_app_icon(self):
        """Tạo icon cho macOS .app bundle"""
        print("\n🎨 Creating macOS app icon...")
        
        # Look for existing icon
        icon_sources = [
            self.project_dir / "assets" / "icon.icns",
            self.project_dir / "assets" / "icon.png",
            self.admin_tools_dir / "icon.png"
        ]
        
        icon_icns = self.admin_tools_dir / "admin_key_icon.icns"
        
        for source in icon_sources:
            if source.exists():
                if source.suffix == '.icns':
                    # Copy existing icns
                    shutil.copy2(source, icon_icns)
                    print(f"✅ Copied existing icon: {source}")
                    return str(icon_icns)
                elif source.suffix == '.png':
                    # Create icns from PNG
                    if self._create_icns_from_png(source, icon_icns):
                        print(f"✅ Created icon from PNG: {source}")
                        return str(icon_icns)
        
        # Create default icon if none found
        print("⚠️ No icon found, creating default...")
        if self._create_default_icon(icon_icns):
            return str(icon_icns)
        
        print("❌ Could not create icon")
        return None
        
    def _create_icns_from_png(self, png_path, icns_path):
        """Tạo .icns từ .png sử dụng iconutil"""
        try:
            # Create iconset directory
            iconset_dir = icns_path.parent / f"{icns_path.stem}.iconset"
            iconset_dir.mkdir(exist_ok=True)
            
            # Define required sizes for macOS
            sizes = [
                (16, "icon_16x16.png"),
                (32, "icon_16x16@2x.png"),
                (32, "icon_32x32.png"),
                (64, "icon_32x32@2x.png"),
                (128, "icon_128x128.png"),
                (256, "icon_128x128@2x.png"),
                (256, "icon_256x256.png"),
                (512, "icon_256x256@2x.png"),
                (512, "icon_512x512.png"),
                (1024, "icon_512x512@2x.png")
            ]
            
            try:
                from PIL import Image
                
                # Open source image
                img = Image.open(png_path)
                
                # Create all required sizes
                for size, filename in sizes:
                    resized = img.resize((size, size), Image.Resampling.LANCZOS)
                    resized.save(iconset_dir / filename)
                
                # Convert to icns using iconutil
                result = subprocess.run([
                    'iconutil', '-c', 'icns',
                    str(iconset_dir),
                    '-o', str(icns_path)
                ], capture_output=True, text=True)
                
                # Clean up iconset directory
                shutil.rmtree(iconset_dir)
                
                return result.returncode == 0
                
            except ImportError:
                print("  ⚠️ PIL/Pillow not available - using sips")
                return self._create_icns_with_sips(png_path, icns_path)
                
        except Exception as e:
            print(f"  ❌ Icon creation error: {e}")
            return False
            
    def _create_icns_with_sips(self, png_path, icns_path):
        """Tạo .icns sử dụng sips (macOS built-in tool)"""
        try:
            # Create temporary iconset
            iconset_dir = icns_path.parent / f"{icns_path.stem}.iconset"
            iconset_dir.mkdir(exist_ok=True)
            
            sizes = [16, 32, 128, 256, 512]
            
            for size in sizes:
                # Create normal size
                subprocess.run([
                    'sips', '-z', str(size), str(size),
                    str(png_path),
                    '--out', str(iconset_dir / f"icon_{size}x{size}.png")
                ], capture_output=True)
                
                # Create @2x size
                if size < 512:
                    subprocess.run([
                        'sips', '-z', str(size * 2), str(size * 2),
                        str(png_path),
                        '--out', str(iconset_dir / f"icon_{size}x{size}@2x.png")
                    ], capture_output=True)
            
            # Convert to icns
            result = subprocess.run([
                'iconutil', '-c', 'icns',
                str(iconset_dir),
                '-o', str(icns_path)
            ], capture_output=True)
            
            # Clean up
            shutil.rmtree(iconset_dir)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"  ❌ sips icon creation error: {e}")
            return False
            
    def _create_default_icon(self, icns_path):
        """Tạo icon mặc định đơn giản"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple icon
            img = Image.new('RGBA', (512, 512), (70, 130, 180, 255))  # Steel blue
            draw = ImageDraw.Draw(img)
            
            # Draw a key symbol
            draw.ellipse([50, 150, 200, 300], fill=(255, 215, 0, 255))  # Gold circle
            draw.rectangle([180, 200, 400, 250], fill=(255, 215, 0, 255))  # Key shaft
            draw.rectangle([350, 180, 400, 220], fill=(255, 215, 0, 255))  # Key teeth
            draw.rectangle([350, 230, 400, 270], fill=(255, 215, 0, 255))
            
            # Add text
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 60)
            except:
                font = ImageFont.load_default()
            
            draw.text((100, 350), "Admin", fill=(255, 255, 255, 255), font=font)
            draw.text((120, 420), "Key", fill=(255, 255, 255, 255), font=font)
            
            # Save as PNG first
            png_path = icns_path.with_suffix('.png')
            img.save(png_path)
            
            # Convert to icns
            return self._create_icns_from_png(png_path, icns_path)
            
        except ImportError:
            print("  ⚠️ PIL not available for default icon creation")
            return False
        except Exception as e:
            print(f"  ❌ Default icon creation error: {e}")
            return False
            
    def create_spec_file(self, icon_path=None):
        """Tạo PyInstaller spec file cho macOS"""
        print("\n📝 Creating PyInstaller spec file for macOS...")
        
        # Use string formatting thay vì f-string để tránh conflicts
        icon_value = f'"{icon_path}"' if icon_path else 'None'
        
        spec_content = '''# -*- mode: python ; coding: utf-8 -*-
"""
Admin Key Generator GUI - PyInstaller Spec File for macOS
"""

import os
import platform
from pathlib import Path

IS_MACOS = platform.system() == "Darwin"

# Thư mục admin tools
ADMIN_DIR = Path(r"''' + str(self.admin_tools_dir) + '''")

block_cipher = None

a = Analysis(
    [str(ADMIN_DIR / "admin_key_gui.py")],
    pathex=[str(ADMIN_DIR)],
    binaries=[],
    datas=[
        # Include simple_key_generator.py
        (str(ADMIN_DIR / "simple_key_generator.py"), "."),
    ],
    hiddenimports=[
        "customtkinter",
        "tkinter",
        "json",
        "pathlib",
        "datetime",
        "hashlib",
        "random",
        "string",
        "PIL",
        "PIL.Image",
        "PIL.ImageTk"
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages to reduce size
        "numpy",
        "pandas",
        "matplotlib",
        "scipy",
        "selenium",
        "requests"
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ClausoNet_AdminKeyGenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX on macOS
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI app
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# macOS App Bundle
if IS_MACOS:
    app = BUNDLE(
        exe,
        name='ClausoNet Admin Key Generator.app',
        icon=''' + icon_value + ''',
        bundle_identifier='com.clausonet.adminkeyGenerator',
        version='1.0.0',
        info_plist={
            'CFBundleName': 'ClausoNet Admin Key Generator',
            'CFBundleDisplayName': 'ClausoNet Admin Key Generator',
            'CFBundleIdentifier': 'com.clausonet.adminkeygenerator',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleExecutable': 'ClausoNet_AdminKeyGenerator',
            'LSMinimumSystemVersion': '10.14.0',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
            'LSApplicationCategoryType': 'public.app-category.developer-tools',
            'CFBundleDocumentTypes': [],
            'NSPrincipalClass': 'NSApplication'
        },
    )
'''
        
        spec_file = self.admin_tools_dir / "admin_key_gui_macos.spec"
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
            
        print(f"✅ Created spec file: {spec_file}")
        return spec_file
        
    def build_app(self):
        """Build .app bundle using PyInstaller"""
        print("\n🔨 Building macOS .app bundle...")
        
        # Clean previous builds
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            print("🗑️ Cleaned dist directory")
            
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            print("🗑️ Cleaned build directory")
            
        # Create icon
        icon_path = self.create_app_icon()
        
        # Create spec file
        spec_file = self.create_spec_file(icon_path)
        
        # Build command
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            str(spec_file)
        ]
        
        print(f"🚀 Running: {' '.join(cmd)}")
        
        try:
            # Set environment variables for macOS build
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.admin_tools_dir)
            
            result = subprocess.run(cmd, cwd=self.admin_tools_dir, 
                                  capture_output=True, text=True, env=env)
            
            if result.returncode == 0:
                print("✅ Build successful!")
                
                # Check if .app was created
                app_path = self.dist_dir / "ClausoNet Admin Key Generator.app"
                if app_path.exists():
                    print(f"✅ .app bundle created: {app_path}")
                    
                    # Get app size
                    size = self._get_directory_size(app_path)
                    print(f"📏 App bundle size: {size / 1024 / 1024:.1f} MB")
                    
                    return True
                else:
                    print(f"❌ .app bundle not found at: {app_path}")
                    print("Available files:")
                    if self.dist_dir.exists():
                        for item in self.dist_dir.iterdir():
                            print(f"  - {item}")
                    return False
            else:
                print("❌ Build failed!")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False
    
    def _get_directory_size(self, path):
        """Tính kích thước thư mục"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception:
            pass
        return total_size
        
    def create_admin_package(self):
        """Tạo package hoàn chỉnh cho admin key generator trên macOS"""
        print("\n📦 Creating macOS admin package...")
        
        # Clean and create package directory
        if self.package_dir.exists():
            shutil.rmtree(self.package_dir)
        self.package_dir.mkdir()
        
        # Copy .app bundle
        app_source = self.dist_dir / "ClausoNet Admin Key Generator.app"
        app_dest = self.package_dir / "ClausoNet Admin Key Generator.app"
        
        if app_source.exists():
            shutil.copytree(app_source, app_dest)
            print(f"✅ Copied .app bundle: {app_dest}")
        else:
            print(f"❌ .app bundle not found: {app_source}")
            return False
            
        # Create admin_data directory for license database
        admin_data_dir = self.package_dir / "admin_data"
        admin_data_dir.mkdir()
        
        # Create empty license database
        initial_db = {
            "metadata": {
                "created": datetime.now().isoformat(),
                "version": "1.0",
                "total_keys": 0,
                "last_updated": datetime.now().isoformat(),
                "platform": "macOS"
            },
            "keys": {}
        }
        
        db_file = admin_data_dir / "license_database.json"
        with open(db_file, 'w', encoding='utf-8') as f:
            json.dump(initial_db, f, indent=2, ensure_ascii=False)
        print(f"✅ Created license database: {db_file}")
        
        # Create launcher script
        launcher_script = f'''#!/bin/bash
# ClausoNet Admin Key Generator Launcher for macOS

APP_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
APP_BUNDLE="$APP_DIR/ClausoNet Admin Key Generator.app"

echo "🍎 ClausoNet Admin Key Generator - macOS Launcher"
echo "================================================"

# Check if .app bundle exists
if [ ! -d "$APP_BUNDLE" ]; then
    echo "❌ Error: App bundle not found!"
    echo "Expected: $APP_BUNDLE"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check admin_data directory
if [ ! -d "$APP_DIR/admin_data" ]; then
    echo "📁 Creating admin_data directory..."
    mkdir -p "$APP_DIR/admin_data"
fi

echo "🚀 Launching ClausoNet Admin Key Generator..."
echo ""

# Launch the app
open "$APP_BUNDLE"

# Wait a moment then exit
sleep 2
echo "✅ App launched successfully!"
'''
        
        launcher_file = self.package_dir / "Launch_AdminKeyGenerator.sh"
        with open(launcher_file, 'w', encoding='utf-8') as f:
            f.write(launcher_script)
        
        # Make launcher executable
        os.chmod(launcher_file, 0o755)
        print(f"✅ Created launcher script: {launcher_file}")
        
        # Create README for macOS admin
        readme_content = f'''# ClausoNet 4.0 Pro - Admin Key Generator (macOS)

## Hướng dẫn sử dụng trên macOS

### 1. Khởi chạy ứng dụng

#### Cách 1: Sử dụng Launcher (Khuyên dùng)
```bash
# Double-click hoặc chạy trong Terminal
./Launch_AdminKeyGenerator.sh
```

#### Cách 2: Khởi chạy trực tiếp
```bash
# Double-click file .app trong Finder
open "ClausoNet Admin Key Generator.app"
```

### 2. Lần đầu chạy trên macOS

Khi chạy lần đầu, macOS có thể hiển thị cảnh báo bảo mật:

1. **"Cannot open because it is from an unidentified developer"**
   - Right-click → Open → Open anyway
   - Hoặc: System Preferences → Security & Privacy → Allow

2. **Gatekeeper warning**
   - Click "Open" để tiếp tục

### 3. Tính năng chính

- **Generate Keys**: Tạo license key mới
- **View Keys**: Xem và quản lý key đã tạo  
- **Statistics**: Thống kê database

### 4. Database

- Vị trí: `admin_data/license_database.json`
- Tự động tạo khi chạy lần đầu
- Có thể backup/restore bằng cách copy file

### 5. Yêu cầu hệ thống

- macOS 10.14+ (Mojave hoặc mới hơn)
- Không cần cài đặt Python
- RAM: 4GB+ khuyên dùng

### 6. Troubleshooting

#### App không khởi chạy
```bash
# Kiểm tra permissions
ls -la "ClausoNet Admin Key Generator.app"

# Reset permissions nếu cần
chmod -R 755 "ClausoNet Admin Key Generator.app"
```

#### Database lỗi permissions
```bash
# Fix permissions cho admin_data
chmod -R 755 admin_data/
```

#### Lỗi "Damaged app"
```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine "ClausoNet Admin Key Generator.app"
```

### 7. Backup và Migration

#### Backup database
```bash
# Copy toàn bộ admin_data folder
cp -r admin_data/ ~/Desktop/clausonet_backup_$(date +%Y%m%d)/
```

#### Chuyển sang máy macOS khác
1. Copy toàn bộ package folder
2. Chạy `Launch_AdminKeyGenerator.sh`
3. Database sẽ được preserve

### 8. Bảo mật

- ⚠️ **CHỈ** admin được sử dụng tool này
- ⚠️ **KHÔNG** chia sẻ .app với end users
- ⚠️ Backup database thường xuyên
- Khuyên dùng FileVault để mã hóa disk

### 9. Liên hệ hỗ trợ

- Email: support@clausonet.com
- Documentation: ADMIN_BUILD_GUIDE.md
- Platform: macOS
- Version: 1.0

---
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Build Date: {datetime.now().strftime("%Y-%m-%d")}
'''
        
        readme_file = self.package_dir / "README_MACOS.txt"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"✅ Created README: {readme_file}")
        
        print(f"✅ macOS admin package created: {self.package_dir}")
        return True
        
    def create_deployment_dmg(self):
        """Tạo file DMG để deploy cho máy macOS khác"""
        print("\n💿 Creating deployment DMG...")
        
        dmg_name = f"ClausoNet_AdminKeyGenerator_macOS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dmg"
        dmg_path = self.admin_tools_dir / dmg_name
        
        try:
            # Create DMG using hdiutil
            cmd = [
                'hdiutil', 'create',
                '-srcfolder', str(self.package_dir),
                '-volname', 'ClausoNet Admin Key Generator',
                '-format', 'UDZO',  # Compressed
                '-imagekey', 'zlib-level=9',  # Maximum compression
                str(dmg_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Created deployment DMG: {dmg_path}")
                print(f"📏 DMG size: {dmg_path.stat().st_size / 1024 / 1024:.1f} MB")
                return dmg_path
            else:
                print(f"❌ DMG creation failed: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Failed to create DMG: {e}")
            
            # Fallback: create ZIP
            print("📁 Creating ZIP as fallback...")
            zip_name = f"ClausoNet_AdminKeyGenerator_macOS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            zip_path = self.admin_tools_dir / zip_name
            
            try:
                shutil.make_archive(
                    str(zip_path.with_suffix('')),
                    'zip',
                    str(self.package_dir)
                )
                print(f"✅ Created deployment ZIP: {zip_path}")
                return zip_path
            except Exception as e2:
                print(f"❌ ZIP creation also failed: {e2}")
                return None
                
    def run_full_build(self):
        """Chạy toàn bộ quá trình build cho macOS"""
        print("🚀 Starting macOS Admin Key Generator build process...")
        print("=" * 60)
        
        steps = [
            ("Check dependencies", self.check_dependencies),
            ("Build .app bundle", self.build_app),
            ("Create admin package", self.create_admin_package),
            ("Create deployment DMG", self.create_deployment_dmg)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 Step: {step_name}")
            result = step_func()
            
            if step_name == "Create deployment DMG":
                # This step returns the DMG path or None
                if result is None:
                    print(f"❌ Failed at: {step_name}")
                    return False
            elif not result:
                print(f"❌ Failed at: {step_name}")
                print("\n💡 Please fix the issues above and try again")
                return False
                
        print("\n" + "=" * 60)
        print("🎉 macOS ADMIN KEY GENERATOR BUILD COMPLETE!")
        print("=" * 60)
        print()
        print("📋 What was created:")
        print(f"   📁 Package: {self.package_dir}")
        print(f"   📱 App: ClausoNet Admin Key Generator.app")
        print(f"   📊 Database: admin_data/license_database.json")
        print(f"   📄 README: README_MACOS.txt")
        print(f"   🚀 Launcher: Launch_AdminKeyGenerator.sh")
        print()
        print("📋 Next steps:")
        print("1. Test the .app locally first")
        print("2. Copy DMG/ZIP to admin's macOS machine")
        print("3. Mount DMG and drag .app to Applications")
        print("4. Run Launch_AdminKeyGenerator.sh")
        print("5. Generate test license key")
        print()
        print("🍎 macOS Specific Notes:")
        print("   - First run may require security approval")
        print("   - Use 'xattr -d com.apple.quarantine' if needed")
        print("   - .app can be copied to /Applications")
        print("   - Database stored in admin_data folder")
        
        return True

def main():
    """Main function"""
    try:
        builder = AdminKeyBuilderMacOS()
        
        if len(sys.argv) > 1 and sys.argv[1] == "--quick":
            # Quick build - skip dependency check
            print("⚡ Quick build mode")
            builder.build_app()
            builder.create_admin_package()
        else:
            # Full build process
            builder.run_full_build()
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Build cancelled by user")
    except Exception as e:
        print(f"\n❌ Build failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 