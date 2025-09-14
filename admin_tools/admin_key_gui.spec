# -*- mode: python ; coding: utf-8 -*-
"""
Admin Key Generator GUI - PyInstaller Spec File
"""

import os
import platform
from pathlib import Path

IS_WINDOWS = platform.system() == "Windows"

# Thư mục admin tools
ADMIN_DIR = Path(r"c:\project\videoai\ClausoNet4.0\admin_tools")

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
    hooksconfig={},
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
    icon_path = Path(r"c:\project\videoai\ClausoNet4.0") / "assets" / "icon.ico"
    if icon_path.exists():
        icon_file = str(icon_path)
        print(f"✅ Found icon: {icon_file}")
    else:
        print(f"⚠️ Icon not found: {icon_path}")

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
