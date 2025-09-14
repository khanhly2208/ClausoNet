#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Admin Key GUI Builder
Script để build Admin Key Generator GUI thành file EXE độc lập
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from datetime import datetime

class AdminKeyBuilder:
    """Builder cho Admin Key Generator GUI"""
    
    def __init__(self):
        self.admin_tools_dir = Path(__file__).parent
        self.project_dir = self.admin_tools_dir.parent
        self.build_dir = self.admin_tools_dir / "build"
        self.dist_dir = self.admin_tools_dir / "dist"
        self.package_dir = self.admin_tools_dir / "admin_key_package"
        
        print("🔑 ClausoNet 4.0 Pro - Admin Key GUI Builder")
        print("=" * 60)
        print(f"📁 Admin tools directory: {self.admin_tools_dir}")
        print(f"📁 Project directory: {self.project_dir}")
        
    def check_dependencies(self):
        """Kiểm tra các dependency cần thiết"""
        print("\n🔍 Checking dependencies...")
        
        # Check PyInstaller
        try:
            import PyInstaller
            print("✅ PyInstaller found")
        except ImportError:
            print("❌ PyInstaller not found")
            print("💡 Install with: pip install pyinstaller")
            return False
            
        # Check customtkinter
        try:
            import customtkinter
            print("✅ CustomTkinter found")
        except ImportError:
            print("❌ CustomTkinter not found")
            print("💡 Install with: pip install customtkinter")
            return False
            
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
        
    def create_spec_file(self):
        """Tạo PyInstaller spec file cho Admin Key GUI"""
        print("\n📝 Creating PyInstaller spec file...")
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""
Admin Key Generator GUI - PyInstaller Spec File
"""

import os
import platform
from pathlib import Path

IS_WINDOWS = platform.system() == "Windows"

# Thư mục admin tools
ADMIN_DIR = Path(r"{self.admin_tools_dir}")

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
        "string"
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Icon file
icon_file = None
if IS_WINDOWS:
    icon_path = Path(r"{self.project_dir}") / "assets" / "icon.ico"
    if icon_path.exists():
        icon_file = str(icon_path)
        print(f"✅ Found icon: {{icon_file}}")
    else:
        print(f"⚠️ Icon not found: {{icon_path}}")

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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI app
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)
'''
        
        spec_file = self.admin_tools_dir / "admin_key_gui.spec"
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
            
        print(f"✅ Created spec file: {spec_file}")
        return spec_file
        
    def build_exe(self):
        """Build EXE using PyInstaller"""
        print("\n🔨 Building EXE...")
        
        # Clean previous builds
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            print("🗑️ Cleaned dist directory")
            
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            print("🗑️ Cleaned build directory")
            
        # Create spec file
        spec_file = self.create_spec_file()
        
        # Build command
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            str(spec_file)
        ]
        
        print(f"🚀 Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, cwd=self.admin_tools_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Build successful!")
                
                # Check if EXE was created
                exe_path = self.dist_dir / "ClausoNet_AdminKeyGenerator.exe"
                if exe_path.exists():
                    print(f"✅ EXE created: {exe_path}")
                    print(f"📏 File size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
                    return True
                else:
                    print(f"❌ EXE not found at: {exe_path}")
                    return False
            else:
                print("❌ Build failed!")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False
            
    def create_admin_package(self):
        """Tạo package hoàn chỉnh cho admin key generator"""
        print("\n📦 Creating admin package...")
        
        # Clean and create package directory
        if self.package_dir.exists():
            shutil.rmtree(self.package_dir)
        self.package_dir.mkdir()
        
        # Copy EXE
        exe_source = self.dist_dir / "ClausoNet_AdminKeyGenerator.exe"
        exe_dest = self.package_dir / "ClausoNet_AdminKeyGenerator.exe"
        
        if exe_source.exists():
            shutil.copy2(exe_source, exe_dest)
            print(f"✅ Copied EXE: {exe_dest}")
        else:
            print(f"❌ EXE not found: {exe_source}")
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
                "last_updated": datetime.now().isoformat()
            },
            "keys": {}
        }
        
        db_file = admin_data_dir / "license_database.json"
        with open(db_file, 'w', encoding='utf-8') as f:
            json.dump(initial_db, f, indent=2, ensure_ascii=False)
        print(f"✅ Created license database: {db_file}")
        
        # Create README for admin
        readme_content = f'''# ClausoNet 4.0 Pro - Admin Key Generator

## Hướng dẫn sử dụng

### 1. Khởi chạy
- Chạy file: `ClausoNet_AdminKeyGenerator.exe`
- Ứng dụng sẽ mở giao diện GUI để tạo license key

### 2. Tạo License Key
- Tab "Generate Keys": Tạo key mới
  - Nhập tên khách hàng
  - Chọn thời hạn (7/30/90/365 ngày hoặc tùy chỉnh)
  - Nhập ghi chú (tùy chọn)
  - Click "Generate License Key"

### 3. Quản lý Key
- Tab "View Keys": Xem danh sách key đã tạo
  - Lọc theo trạng thái (Active/All)
  - Xóa key không cần thiết
  - Copy key để gửi khách hàng

### 4. Thống kê
- Tab "Statistics": Xem thống kê database
  - Tổng số key đã tạo
  - Phân loại theo loại license
  - Key gần đây

### 5. Database
- File database: `admin_data/license_database.json`
- Tự động backup khi tạo/xóa key
- Có thể copy sang máy khác

### 6. Bảo mật
- Chỉ admin mới được chạy tool này
- Không chia sẻ file EXE với khách hàng
- Database chứa tất cả key đã tạo

### 7. Hỗ trợ
- Email: support@clausonet.com
- Tài liệu: ADMIN_GUIDE.md

---
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Version: 1.0
'''
        
        readme_file = self.package_dir / "README_ADMIN.txt"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"✅ Created README: {readme_file}")
        
        # Create batch file for easy startup
        batch_content = f'''@echo off
title ClausoNet 4.0 Pro - Admin Key Generator
echo Starting ClausoNet Admin Key Generator...
echo.

REM Check if EXE exists
if not exist "ClausoNet_AdminKeyGenerator.exe" (
    echo ERROR: ClausoNet_AdminKeyGenerator.exe not found!
    echo Please make sure this batch file is in the same directory as the EXE.
    pause
    exit /b 1
)

REM Check admin_data directory
if not exist "admin_data" (
    echo Creating admin_data directory...
    mkdir admin_data
)

REM Start the application
echo Launching Admin Key Generator...
start "" "ClausoNet_AdminKeyGenerator.exe"

REM Wait a moment then close this window
timeout /t 2 /nobreak >nul
exit
'''
        
        batch_file = self.package_dir / "Start_AdminKeyGenerator.bat"
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        print(f"✅ Created startup batch: {batch_file}")
        
        print(f"✅ Admin package created: {self.package_dir}")
        return True
        
    def create_deployment_zip(self):
        """Tạo file ZIP để deploy cho máy khác"""
        print("\n📁 Creating deployment ZIP...")
        
        zip_name = f"ClausoNet_AdminKeyGenerator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = self.admin_tools_dir / zip_name
        
        try:
            shutil.make_archive(
                str(zip_path.with_suffix('')),
                'zip',
                str(self.package_dir)
            )
            
            print(f"✅ Created deployment ZIP: {zip_path}")
            print(f"📏 ZIP size: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")
            
            return zip_path
            
        except Exception as e:
            print(f"❌ Failed to create ZIP: {e}")
            return None
            
    def run_full_build(self):
        """Chạy toàn bộ quá trình build"""
        print("🚀 Starting Admin Key Generator build process...")
        print("=" * 60)
        
        steps = [
            ("Check dependencies", self.check_dependencies),
            ("Build EXE", self.build_exe),
            ("Create admin package", self.create_admin_package),
            ("Create deployment ZIP", self.create_deployment_zip)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 Step: {step_name}")
            result = step_func()
            
            if step_name == "Create deployment ZIP":
                # This step returns the ZIP path or None
                if result is None:
                    print(f"❌ Failed at: {step_name}")
                    return False
            elif not result:
                print(f"❌ Failed at: {step_name}")
                print("\n💡 Please fix the issues above and try again")
                return False
                
        print("\n" + "=" * 60)
        print("🎉 ADMIN KEY GENERATOR BUILD COMPLETE!")
        print("=" * 60)
        print()
        print("📋 What was created:")
        print(f"   📁 Package: {self.package_dir}")
        print(f"   📱 EXE: ClausoNet_AdminKeyGenerator.exe")
        print(f"   📊 Database: admin_data/license_database.json")
        print(f"   📄 README: README_ADMIN.txt")
        print(f"   🚀 Startup: Start_AdminKeyGenerator.bat")
        print()
        print("📋 Next steps:")
        print("1. Test the EXE locally first")
        print("2. Copy the ZIP file to admin's machine")
        print("3. Extract and run Start_AdminKeyGenerator.bat")
        print("4. Generate test license key")
        print("5. Verify database is created properly")
        print()
        print("⚠️  Security Notes:")
        print("   - Only give this tool to authorized admin")
        print("   - Keep the admin_data folder secure")
        print("   - Backup license database regularly")
        
        return True

def main():
    """Main function"""
    try:
        builder = AdminKeyBuilder()
        
        if len(sys.argv) > 1 and sys.argv[1] == "--quick":
            # Quick build - skip dependency check
            print("⚡ Quick build mode")
            builder.build_exe()
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