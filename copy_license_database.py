#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - License Database Copy Tool
Copy license database to user's AppData for cross-machine deployment
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

def copy_license_database():
    """Copy license database from admin location to user AppData"""
    
    print("🔄 ClausoNet 4.0 Pro - License Database Copy Tool")
    print("=" * 50)
    
    # Source file (admin location)
    source_file = Path("C:/project/videoai/ClausoNet4.0/admin_data/license_database.json")
    
    # Target location (user AppData)
    appdata_local = Path.home() / "AppData" / "Local"
    target_dir = appdata_local / "ClausoNet4.0" / "admin_data"
    target_file = target_dir / "license_database.json"
    
    print(f"📂 Source: {source_file}")
    print(f"📁 Target: {target_file}")
    print()
    
    # Check if source exists
    if not source_file.exists():
        print("❌ Error: Source license database not found!")
        print("   Please make sure you're running this on the admin machine.")
        input("Press Enter to exit...")
        return False
    
    # Create target directory
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        print("📁 Target directory ready")
    except Exception as e:
        print(f"❌ Error creating target directory: {e}")
        input("Press Enter to exit...")
        return False
    
    # Backup existing file
    if target_file.exists():
        try:
            backup_name = f"license_database.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_file = target_dir / backup_name
            shutil.copy2(target_file, backup_file)
            print(f"💾 Backup created: {backup_name}")
        except Exception as e:
            print(f"⚠️ Warning: Could not create backup: {e}")
    
    # Copy the file
    try:
        shutil.copy2(source_file, target_file)
        print("✅ License database copied successfully!")
        
        # Verify the copy
        with open(target_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            key_count = len(data.get('keys', []))
            print(f"🔑 Verified: {key_count} license keys in database")
            
    except Exception as e:
        print(f"❌ Error copying file: {e}")
        input("Press Enter to exit...")
        return False
    
    print()
    print("🎯 ClausoNet 4.0 Pro should now be able to validate licenses on this machine.")
    print(f"📍 License database location: {target_file}")
    print()
    input("Press Enter to exit...")
    return True

if __name__ == "__main__":
    copy_license_database()
