#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔥 Force Clean AppData License - Kill Processes & Clean
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def kill_clausonet_processes():
    """🔥 Kill all ClausoNet processes"""

    print("🔥 KILLING CLAUSONET PROCESSES:")
    print("-" * 35)

    processes_to_kill = [
        "ClausoNet4.0Pro.exe",
        "clausonet.exe",
        "clausonet4.exe",
        "python.exe"  # If running from Python
    ]

    killed = 0
    for process in processes_to_kill:
        try:
            result = subprocess.run(['taskkill', '/F', '/IM', process],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"🔥 Killed: {process}")
                killed += 1
            else:
                print(f"✅ Not running: {process}")
        except Exception as e:
            print(f"❌ Error killing {process}: {e}")

    if killed > 0:
        print(f"⏳ Waiting 3 seconds for processes to close...")
        time.sleep(3)

    return killed

def force_delete_appdata():
    """🗑️ Force delete AppData directory"""

    print(f"\n🗑️ FORCE DELETING APPDATA:")
    print("-" * 30)

    appdata_path = Path.home() / "AppData" / "Local" / "ClausoNet4.0"

    if not appdata_path.exists():
        print(f"✅ AppData already clean")
        return True

    # Method 1: Python deletion
    try:
        import shutil
        shutil.rmtree(appdata_path)
        print(f"✅ Python deleted: {appdata_path}")
        return True
    except Exception as e:
        print(f"❌ Python delete failed: {e}")

    # Method 2: CMD rmdir
    try:
        result = subprocess.run(['rmdir', '/S', '/Q', str(appdata_path)],
                              shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ CMD deleted: {appdata_path}")
            return True
        else:
            print(f"❌ CMD delete failed: {result.stderr}")
    except Exception as e:
        print(f"❌ CMD delete error: {e}")

    # Method 3: PowerShell Remove-Item
    try:
        ps_command = f'Remove-Item "{appdata_path}" -Recurse -Force'
        result = subprocess.run(['powershell', '-Command', ps_command],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PowerShell deleted: {appdata_path}")
            return True
        else:
            print(f"❌ PowerShell delete failed: {result.stderr}")
    except Exception as e:
        print(f"❌ PowerShell delete error: {e}")

    return False

def manual_file_deletion():
    """🔧 Manual file by file deletion"""

    print(f"\n🔧 MANUAL FILE DELETION:")
    print("-" * 25)

    appdata_path = Path.home() / "AppData" / "Local" / "ClausoNet4.0"

    if not appdata_path.exists():
        print(f"✅ AppData already clean")
        return True

    deleted_files = 0

    # Delete files first
    for file_path in appdata_path.rglob("*"):
        if file_path.is_file():
            try:
                file_path.unlink()
                print(f"🗑️ Deleted: {file_path.relative_to(appdata_path)}")
                deleted_files += 1
            except Exception as e:
                print(f"❌ Can't delete {file_path.name}: {e}")

    # Delete directories
    for dir_path in sorted(appdata_path.rglob("*"), key=lambda x: str(x), reverse=True):
        if dir_path.is_dir() and dir_path != appdata_path:
            try:
                dir_path.rmdir()
                print(f"📁 Removed dir: {dir_path.relative_to(appdata_path)}")
            except Exception as e:
                print(f"❌ Can't remove dir {dir_path.name}: {e}")

    # Remove main directory
    try:
        appdata_path.rmdir()
        print(f"✅ Removed main AppData directory")
        return True
    except Exception as e:
        print(f"❌ Can't remove main directory: {e}")
        return False

def main():
    """🚀 Main force clean function"""

    print("🔥 FORCE CLEAN APPDATA LICENSE DATA")
    print("=" * 40)

    # Step 1: Kill processes
    killed = kill_clausonet_processes()

    # Step 2: Force delete AppData
    if force_delete_appdata():
        print(f"\n🎉 APPDATA FORCE CLEANED!")
        print(f"✅ Ready to rebuild EXE")
        return True

    # Step 3: Manual deletion if force failed
    print(f"\n🔧 Trying manual deletion...")
    if manual_file_deletion():
        print(f"\n🎉 APPDATA MANUALLY CLEANED!")
        print(f"✅ Ready to rebuild EXE")
        return True

    # Step 4: Show remaining files
    appdata_path = Path.home() / "AppData" / "Local" / "ClausoNet4.0"
    if appdata_path.exists():
        print(f"\n❌ SOME FILES STILL REMAIN:")
        for item in appdata_path.rglob("*"):
            if item.is_file():
                print(f"   📄 {item.relative_to(appdata_path)}")

        print(f"\n💡 MANUAL SOLUTION:")
        print(f"1. Close ALL ClausoNet processes")
        print(f"2. Delete manually: {appdata_path}")
        print(f"3. Restart Windows if needed")

        return False

    return True

if __name__ == "__main__":
    main()
