#!/usr/bin/env python3
"""
Script to copy license database to another machine or location
This helps when licenses were created on one machine but need to be used on another
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime

def find_database_locations():
    """Find possible database locations"""
    locations = []
    
    # Current machine locations
    user_home = Path.home()
    
    possible_paths = [
        # Standard AppData location
        user_home / "AppData" / "Local" / "ClausoNet4.0" / "admin_data" / "license_database.json",
        
        # Documents folder
        user_home / "Documents" / "ClausoNet4.0" / "license_database.json",
        
        # Current project directory
        Path.cwd() / "admin_data" / "license_database.json",
        
        # Parent admin_data
        Path.cwd().parent / "admin_data" / "license_database.json",
    ]
    
    for path in possible_paths:
        if path.exists():
            locations.append(path)
    
    return locations

def copy_database(source_path, target_path):
    """Copy database from source to target"""
    try:
        # Create target directory if it doesn't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the file
        shutil.copy2(source_path, target_path)
        
        print(f"✅ Database copied successfully!")
        print(f"   From: {source_path}")
        print(f"   To:   {target_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error copying database: {e}")
        return False

def create_portable_database_package():
    """Create a portable database package that can be shared"""
    try:
        # Find existing database
        databases = find_database_locations()
        
        if not databases:
            print("❌ No license database found!")
            return False
        
        source_db = databases[0]  # Use first found
        print(f"📁 Using database: {source_db}")
        
        # Load and verify database
        with open(source_db, 'r', encoding='utf-8') as f:
            db_data = json.load(f)
        
        print(f"📊 Database contains {len(db_data.get('keys', []))} license keys")
        
        # Create portable package
        package_dir = Path("license_database_package")
        package_dir.mkdir(exist_ok=True)
        
        # Copy database file
        package_db = package_dir / "license_database.json"
        shutil.copy2(source_db, package_db)
        
        # Create installation script
        install_script = package_dir / "install_database.bat"
        install_script.write_text(f'''@echo off
echo Installing ClausoNet 4.0 License Database...
echo.

REM Create target directory
if not exist "%USERPROFILE%\\AppData\\Local\\ClausoNet4.0\\admin_data" (
    mkdir "%USERPROFILE%\\AppData\\Local\\ClausoNet4.0\\admin_data"
)

REM Copy database
copy "license_database.json" "%USERPROFILE%\\AppData\\Local\\ClausoNet4.0\\admin_data\\"

echo.
echo ✅ License database installed successfully!
echo    Location: %USERPROFILE%\\AppData\\Local\\ClausoNet4.0\\admin_data\\license_database.json
echo.
echo You can now use ClausoNet 4.0 with these license keys:

REM Show available keys (first few lines)
echo.
echo 📋 Available License Keys:
echo ═══════════════════════════
findstr "CNPRO-" "license_database.json" | head -5
echo.
pause
''', encoding='utf-8')
        
        # Create info file
        info_file = package_dir / "README.txt"
        info_file.write_text(f'''ClausoNet 4.0 Pro - License Database Package
════════════════════════════════════════════

This package contains the license database with {len(db_data.get('keys', []))} license keys.

INSTALLATION INSTRUCTIONS:
═════════════════════════

Method 1 - Automatic (Windows):
  1. Double-click "install_database.bat"
  2. Follow the prompts

Method 2 - Manual:
  1. Copy "license_database.json" to:
     %USERPROFILE%\\AppData\\Local\\ClausoNet4.0\\admin_data\\
  
  2. Create the directory first if it doesn't exist:
     mkdir "%USERPROFILE%\\AppData\\Local\\ClausoNet4.0\\admin_data"

AVAILABLE KEYS:
═══════════════

''', encoding='utf-8')
        
        # Add key list to info
        with open(info_file, 'a', encoding='utf-8') as f:
            for i, key_data in enumerate(db_data.get('keys', []), 1):
                f.write(f"{i}. {key_data.get('key', 'Unknown')} - {key_data.get('type', 'Unknown')} "
                       f"({key_data.get('customer_info', {}).get('name', 'Unknown User')})\n")
        
        print(f"\\n📦 Portable package created: {package_dir}")
        print(f"   Contents:")
        print(f"   - license_database.json (main database)")
        print(f"   - install_database.bat (auto installer)")
        print(f"   - README.txt (instructions)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating package: {e}")
        return False

def install_from_current_directory():
    """Install database from current directory to standard location"""
    try:
        # Look for database in current directory
        current_db = Path("license_database.json")
        if not current_db.exists():
            print("❌ No license_database.json found in current directory!")
            return False
        
        # Standard installation path
        target_dir = Path.home() / "AppData" / "Local" / "ClausoNet4.0" / "admin_data"
        target_db = target_dir / "license_database.json"
        
        # Create directory
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy database
        shutil.copy2(current_db, target_db)
        
        # Load and show stats
        with open(target_db, 'r', encoding='utf-8') as f:
            db_data = json.load(f)
        
        print(f"✅ Database installed successfully!")
        print(f"   Location: {target_db}")
        print(f"   Keys available: {len(db_data.get('keys', []))}")
        
        # Show available keys
        print(f"\\n📋 Available License Keys:")
        print("═" * 40)
        for key_data in db_data.get('keys', []):
            print(f"🔑 {key_data.get('key', 'Unknown')} - {key_data.get('type', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error installing database: {e}")
        return False

def main():
    """Main function"""
    print("🚀 ClausoNet 4.0 Pro - License Database Manager")
    print("=" * 60)
    
    print("\\nAvailable operations:")
    print("1. 📦 Create portable database package")
    print("2. 🔍 Find existing databases") 
    print("3. 📥 Install database from current directory")
    print("4. ❌ Exit")
    
    while True:
        try:
            choice = input("\\n➤ Choose operation (1-4): ").strip()
            
            if choice == "1":
                print("\\n📦 Creating portable database package...")
                create_portable_database_package()
                break
                
            elif choice == "2":
                print("\\n🔍 Searching for databases...")
                databases = find_database_locations()
                if databases:
                    print(f"   Found {len(databases)} database(s):")
                    for i, db in enumerate(databases, 1):
                        print(f"   {i}. {db}")
                else:
                    print("   No databases found!")
                break
                
            elif choice == "3":
                print("\\n📥 Installing from current directory...")
                install_from_current_directory()
                break
                
            elif choice == "4":
                print("\\n👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice! Please enter 1-4.")
                
        except KeyboardInterrupt:
            print("\\n\\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()
