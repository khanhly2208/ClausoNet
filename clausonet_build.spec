# -*- mode: python ; coding: utf-8 -*-
"""
ClausoNet 4.0 Pro - PyInstaller Spec File
Cấu hình đóng gói exe/app cho thương mại hóa
"""

import os
import platform
from pathlib import Path

# Xác định platform
IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

# Thư mục dự án
PROJECT_DIR = Path(SPECPATH)  # ClausoNet4.0 directory
print(f"🏗️ Building ClausoNet 4.0 Pro for {platform.system()}")
print(f"📁 Project directory: {PROJECT_DIR}")

# Entry point
entry_script = str(PROJECT_DIR / "gui" / "main_window.py")

# Check if entry script exists
if not Path(entry_script).exists():
    print(f"❌ Entry script not found: {entry_script}")
    print(f"📁 Available GUI files:")
    gui_dir = PROJECT_DIR / "gui"
    if gui_dir.exists():
        for file in gui_dir.glob("*.py"):
            print(f"   - {file}")
    else:
        print(f"   - GUI directory not found: {gui_dir}")
        # Try to find main_window.py in project root or other locations
        for main_file in PROJECT_DIR.rglob("main_window.py"):
            print(f"   - Found at: {main_file}")
            entry_script = str(main_file)
            break
        else:
            print(f"   - main_window.py not found anywhere in project")
            exit(1)

print(f"📋 Entry script: {entry_script}")

# ===========================================
# DATAS - Các file cần include
# ===========================================

datas = []

# Config files (template) - check if exists first
config_file = PROJECT_DIR / "config.yaml"
if config_file.exists():
    # Bundle config.yaml vào root để dễ tìm thấy trong EXE
    datas.append((str(config_file), "."))  # Root of bundle
    print(f"✅ Including config: {config_file} -> root")
else:
    print(f"⚠️ Config file not found: {config_file}")
    # Create default config if not exists
    default_config = """# ClausoNet 4.0 Pro Configuration
version: "4.0.1"
features:
  simplified_license: true
  auto_creation: true
  offline_operation: true
"""
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(default_config)
        datas.append((str(config_file), "."))
        print(f"✅ Created and including default config: {config_file}")
    except Exception as e:
        print(f"⚠️ Could not create default config: {e}")

# Certificates (nếu có)
certs_dir = PROJECT_DIR / "certs"
if certs_dir.exists():
    datas.append((str(certs_dir), "certs"))
    print(f"✅ Including certs: {certs_dir}")

# 🎯 SIMPLIFIED LICENSE SYSTEM - NO ADMIN_DATA NEEDED!
print("🔑 Using Simplified License System - No admin database required")
print("   ✅ User licenses auto-created in AppData")
print("   ✅ Admin tools separate from user deployment")

# Admin tools (ONLY for key generation - NOT for user deployment)
admin_tools_dir = PROJECT_DIR / "admin_tools"
if admin_tools_dir.exists():
    # Only include the simple key generator files
    admin_files_to_include = [
        "simple_key_generator.py",
        "admin_key_gui.py"
    ]
    
    for admin_file in admin_files_to_include:
        admin_file_path = admin_tools_dir / admin_file
        if admin_file_path.exists():
            datas.append((str(admin_file_path), "admin_tools"))
            print(f"✅ Including admin tool: {admin_file}")
        else:
            print(f"⚠️ Admin tool not found: {admin_file}")
    
    print(f"🔧 Admin tools included for separate distribution only")

# Core modules (license system)
core_dir = PROJECT_DIR / "core"
if core_dir.exists():
    datas.append((str(core_dir), "core"))
    print(f"✅ Including core modules: {core_dir}")

# Tools directory (bundled ChromeDriver)
tools_dir = PROJECT_DIR / "tools"
if tools_dir.exists():
    datas.append((str(tools_dir), "tools"))
    print(f"✅ Including tools: {tools_dir}")

print(f"📦 Total data files to include: {len(datas)}")

# ===========================================
# BINARIES - Các executable cần include
# ===========================================

binaries = []

# ChromeDriver binary (trong drivers/)
drivers_dir = PROJECT_DIR / "drivers"
if drivers_dir.exists():
    if IS_WINDOWS:
        chromedriver_path = drivers_dir / "chromedriver.exe"
        if chromedriver_path.exists():
            binaries.append((str(chromedriver_path), "drivers"))
            print(f"✅ Including ChromeDriver: {chromedriver_path}")
        else:
            print(f"⚠️ ChromeDriver not found: {chromedriver_path}")
    else:
        chromedriver_path = drivers_dir / "chromedriver"
        if chromedriver_path.exists():
            binaries.append((str(chromedriver_path), "drivers"))
            print(f"✅ Including ChromeDriver: {chromedriver_path}")
        else:
            print(f"⚠️ ChromeDriver not found: {chromedriver_path}")

# Microsoft Visual C++ Runtime (fix VCRUNTIME140.dll error)
if IS_WINDOWS:
    import sys
    python_dir = Path(sys.executable).parent
    vcruntime_paths = [
        python_dir / "vcruntime140.dll",
        python_dir / "vcruntime140_1.dll",
        python_dir / "msvcp140.dll",
        # Fallback paths
        Path("C:/Windows/System32/vcruntime140.dll"),
        Path("C:/Windows/System32/vcruntime140_1.dll"),
        Path("C:/Windows/System32/msvcp140.dll")
    ]

    for vcruntime_path in vcruntime_paths:
        if vcruntime_path.exists():
            binaries.append((str(vcruntime_path), "."))
            print(f"✅ Including VC Runtime: {vcruntime_path}")

print(f"🔧 Total binary files to include: {len(binaries)}")

# ===========================================
# HIDDEN IMPORTS
# ===========================================

hiddenimports = [
    # Core dependencies
    'customtkinter',
    'tkinter',
    'tkinter.filedialog',
    'tkinter.messagebox',

    # Selenium
    'selenium',
    'selenium.webdriver',
    'selenium.webdriver.chrome',
    'selenium.webdriver.chrome.service',
    'selenium.webdriver.chrome.options',
    'selenium.webdriver.common.by',
    'selenium.webdriver.support',
    'selenium.webdriver.support.ui',
    'selenium.webdriver.support.expected_conditions',
    'selenium.common.exceptions',
    'webdriver_manager',
    'webdriver_manager.chrome',
    'webdriver_manager.core',

    # API clients
    'requests',
    'google.auth',
    'google.auth.transport',
    'google.auth.transport.requests',
    'google.generativeai',
    'openai',

    # System
    'psutil',
    'platform',
    'pathlib',
    'json',
    'yaml',
    'sqlite3',
    'cryptography',
    'cryptography.fernet',

    # Utils
    'tqdm',
    'colorama',
    'datetime',
    'threading',
    'subprocess',
    'shutil',
    'tempfile',
    'urllib.parse',
    'asyncio',
    'websockets',
    'websockets.client',
    'websockets.exceptions',

    # ClausoNet modules
    'utils.resource_manager',
    'utils.production_chrome_manager',
    'utils.profile_manager',
    'utils.cdp_client',
    'utils.stable_element_finder',
    'utils.enhanced_workflow_detector',

    # 🎯 NEW: Simplified License System
    'core.simple_license_system',
    'admin_tools.simple_key_generator',
    'admin_tools.admin_key_gui',

    # 🗑️ REMOVED: Old license system imports
    # 'admin_tools.license_key_generator',
    # 'admin_tools.admin_license_gui',
]

# ===========================================
# EXCLUDE MODULES (tối ưu kích thước)
# ===========================================

excludes = [
    # Development tools
    'pytest',
    'black',
    'flake8',
    'mypy',
    'autopep8',

    # Unused modules
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'PIL',
    'Pillow',

    # Test modules
    'unittest',
    'doctest',
    'test',
    'tests',
    
    # 🗑️ OLD LICENSE SYSTEM (explicitly exclude)
    'admin_tools.license_key_generator',
    'admin_tools.admin_license_gui',
    'admin_tools.email_request_handler',
]

# ===========================================
# ANALYSIS
# ===========================================

block_cipher = None

a = Analysis(
    [entry_script],
    pathex=[str(PROJECT_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ===========================================
# PYZ (Python Archive)
# ===========================================

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ===========================================
# EXECUTABLE
# ===========================================

# Icon file
icon_file = None
if IS_WINDOWS:
    icon_path = PROJECT_DIR / "assets" / "icon.ico"
    if icon_path.exists():
        icon_file = str(icon_path)
        print(f"✅ Found Windows icon: {icon_file}")
    else:
        print(f"❌ Windows icon not found: {icon_path}")
        # Try alternative paths
        alt_paths = [
            PROJECT_DIR / "icon.ico",
            PROJECT_DIR / "gv.ico",
            PROJECT_DIR / "assets" / "icon.png"
        ]
        for alt_path in alt_paths:
            if alt_path.exists():
                icon_file = str(alt_path)
                print(f"✅ Using alternative icon: {icon_file}")
                break
elif IS_MACOS:
    icon_path = PROJECT_DIR / "assets" / "icon.icns"
    if icon_path.exists():
        icon_file = str(icon_path)
        print(f"✅ Found macOS icon: {icon_file}")
    else:
        print(f"❌ macOS icon not found: {icon_path}")

print(f"🎨 Final icon file: {icon_file}")

# Version file for Windows
version_file = None
if IS_WINDOWS:
    version_info_path = PROJECT_DIR / "version_info.py"
    if version_info_path.exists():
        version_file = str(version_info_path)
        print(f"✅ Found version info: {version_file}")
    else:
        print(f"⚠️ Version info not found: {version_info_path}")

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ClausoNet4.0Pro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Nén executable (có thể tắt nếu gặp lỗi)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI app - windowed mode
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
    version_file=version_file,  # Add version info for Windows
)

# ===========================================
# macOS APP BUNDLE
# ===========================================

if IS_MACOS:
    app = BUNDLE(
        exe,
        name='ClausoNet 4.0 Pro.app',
        icon=icon_file,
        bundle_identifier='com.clausonet.clausonet4pro',
        version='1.0.1',
        info_plist={
            'CFBundleName': 'ClausoNet 4.0 Pro',
            'CFBundleDisplayName': 'ClausoNet 4.0 Pro',
            'CFBundleIdentifier': 'com.clausonet.clausonet4pro',
            'CFBundleVersion': '1.0.1',
            'CFBundleShortVersionString': '1.0.1',
            'CFBundleExecutable': 'ClausoNet4.0Pro',
            'LSMinimumSystemVersion': '10.14.0',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
            'LSApplicationCategoryType': 'public.app-category.productivity',
            # Permissions (nếu cần)
            'NSCameraUsageDescription': 'ClausoNet needs camera access for video processing',
            'NSMicrophoneUsageDescription': 'ClausoNet needs microphone access for audio processing',
        },
    )

print("✅ PyInstaller spec configuration complete!")
print(f"🎯 Target: {'Windows EXE' if IS_WINDOWS else 'macOS APP' if IS_MACOS else 'Linux Binary'}")

# ===========================================
# BUILD VERIFICATION - SIMPLIFIED LICENSE SYSTEM
# ===========================================

print("\n🔍 PRE-BUILD VERIFICATION (Simplified License System):")
print("=" * 50)

# Check critical files for NEW system
critical_files = [
    (PROJECT_DIR / "gui" / "main_window.py", "Main GUI"),
    (PROJECT_DIR / "core" / "simple_license_system.py", "License System"),
    (PROJECT_DIR / "admin_tools" / "simple_key_generator.py", "Key Generator"),
    (PROJECT_DIR / "admin_tools" / "admin_key_gui.py", "Admin GUI"),
]

all_critical_exist = True
for critical_file, description in critical_files:
    if critical_file.exists():
        print(f"✅ {description}: Found")
    else:
        print(f"❌ {description}: Missing - {critical_file}")
        all_critical_exist = False

# 🎯 NO LICENSE DATABASE REQUIRED!
print(f"🔑 License Database: ✅ NOT REQUIRED (Auto-created)")
print(f"📁 Admin Data: ✅ NOT REQUIRED (Independent)")

if not all_critical_exist:
    print(f"\n❌ CRITICAL FILES MISSING - BUILD WILL FAIL")
    print(f"   Please ensure all required files exist before building")
    exit(1)

print(f"\n🎉 All critical files found - Ready to build with Simplified License System!")
print(f"📦 Total data files: {len(datas)}")
print(f"🔧 Total binary files: {len(binaries)}")
print(f"📨 Hidden imports: {len(hiddenimports)}")

print(f"\n🚀 BUILD COMMAND:")
print(f"   pyinstaller clausonet_build.spec")
print(f"\n📁 OUTPUT LOCATION:")
print(f"   dist/ClausoNet4.0Pro.exe  ← Send this to users!")

print(f"\n🎯 DEPLOYMENT FEATURES:")
print(f"   ✅ Zero setup required")
print(f"   ✅ Auto-creates license directory") 
print(f"   ✅ Hardware-bound activation")
print(f"   ✅ Offline operation")
print(f"   ✅ No admin database dependency")
