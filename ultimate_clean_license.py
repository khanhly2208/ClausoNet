#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧹 Ultimate Clean All License Data
Xóa hoàn toàn tất cả license data từ project + AppData để đảm bảo EXE production sạch
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path

def clean_project_license_data():
    """🧹 Clean license data in project directory"""

    print("🧹 CLEANING PROJECT LICENSE DATA:")
    print("-" * 35)

    project_dir = Path(__file__).parent
    cleaned_items = []

    # 1. Admin data
    admin_data_dir = project_dir / "admin_data"
    if admin_data_dir.exists():
        for item in admin_data_dir.iterdir():
            if item.name != "license_database.json":  # Keep the clean database
                if item.is_file():
                    item.unlink()
                    cleaned_items.append(f"🗑️ {item.name}")
                    print(f"🗑️ Removed: {item.name}")

    # 2. Root license files
    license_files = [
        "user_license.json",
        "activation_cache.json",
        "hardware_fingerprint.json",
        "license_cache.json"
    ]

    for file_name in license_files:
        file_path = project_dir / file_name
        if file_path.exists():
            file_path.unlink()
            cleaned_items.append(f"🗑️ {file_name}")
            print(f"🗑️ Removed: {file_name}")

    print(f"✅ Project data cleaned: {len(cleaned_items)} items")
    return len(cleaned_items)

def clean_windows_appdata():
    """🧹 Clean Windows AppData license data"""

    print(f"\n🧹 CLEANING WINDOWS APPDATA:")
    print("-" * 30)

    # Windows AppData path
    appdata_path = Path.home() / "AppData" / "Local" / "ClausoNet4.0"

    if not appdata_path.exists():
        print(f"✅ No AppData found: {appdata_path}")
        return 0

    print(f"📁 Found AppData: {appdata_path}")

    # List contents before deletion
    items_found = []
    try:
        for item in appdata_path.rglob("*"):
            if item.is_file():
                items_found.append(item.relative_to(appdata_path))
                print(f"   📄 {item.relative_to(appdata_path)}")

        if items_found:
            print(f"\n🗑️ Removing AppData directory with {len(items_found)} files...")
            shutil.rmtree(appdata_path)
            print(f"✅ AppData cleaned: {appdata_path}")
            return len(items_found)
        else:
            print(f"✅ AppData empty")
            return 0

    except Exception as e:
        print(f"❌ Error cleaning AppData: {e}")
        return 0

def clean_hardcoded_test_keys():
    """🧹 Clean hardcoded test keys from debug files"""

    print(f"\n🧹 CLEANING HARDCODED TEST KEYS:")
    print("-" * 35)

    project_dir = Path(__file__).parent

    # Files with hardcoded test keys
    test_files = [
        "debug_license_exe.py",
        "test_gui_license.py",
        "test_clean_exe.py"
    ]

    cleaned_keys = 0

    for file_name in test_files:
        file_path = project_dir / file_name
        if file_path.exists():
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Replace hardcoded keys with placeholders
            original_content = content
            content = content.replace('CNPRO-MQOI-AIWE-1RHK-A84A', 'CNPRO-TEST-TEST-TEST-TEST')
            content = content.replace('CNPRO-ZGZK-RSRC-HTT6-9GUF', 'CNPRO-DEMO-DEMO-DEMO-DEMO')
            content = content.replace('CNPRO-CY1B-B7PC-PB2G-XN5W', 'CNPRO-DEMO-DEMO-DEMO-DEMO')
            content = content.replace('CNPRO-SOFF-6R90-PVPW-3JWL', 'CNPRO-DEMO-DEMO-DEMO-DEMO')
            content = content.replace('CNPRO-COLA-E3BK-R8TH-8LSL', 'CNPRO-DEMO-DEMO-DEMO-DEMO')
            content = content.replace('CNPRO-82KR-ACVL-AF4V-IIYL', 'CNPRO-DEMO-DEMO-DEMO-DEMO')
            content = content.replace('CNPRO-3TBK-H55D-GBKJ-C6AG', 'CNPRO-DEMO-DEMO-DEMO-DEMO')

            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                cleaned_keys += 1
                print(f"🔧 Cleaned hardcoded keys: {file_name}")

    print(f"✅ Hardcoded keys cleaned: {cleaned_keys} files")
    return cleaned_keys

def verify_ultimate_clean():
    """✅ Verify everything is completely clean"""

    print(f"\n🔍 ULTIMATE VERIFICATION:")
    print("=" * 25)

    issues = []

    # 1. Check project database
    project_dir = Path(__file__).parent
    db_path = project_dir / "admin_data" / "license_database.json"

    if db_path.exists():
        with open(db_path, 'r', encoding='utf-8') as f:
            db_data = json.load(f)

        keys_count = len(db_data.get('keys', []))
        if keys_count > 0:
            issues.append(f"❌ Project database has {keys_count} keys")
        else:
            print(f"✅ Project database: 0 keys")
    else:
        issues.append(f"❌ Project database missing")

    # 2. Check AppData
    appdata_path = Path.home() / "AppData" / "Local" / "ClausoNet4.0"
    if appdata_path.exists():
        issues.append(f"❌ AppData still exists: {appdata_path}")
    else:
        print(f"✅ AppData: Clean")

    # 3. Check for any license files in project
    license_files = list(project_dir.rglob("*license*.json"))
    license_files = [f for f in license_files if f.name != "license_database.json"]

    if license_files:
        issues.append(f"❌ Found {len(license_files)} license files")
        for lf in license_files:
            print(f"   📄 {lf.relative_to(project_dir)}")
    else:
        print(f"✅ License files: Clean")

    # 4. Summary
    if issues:
        print(f"\n⚠️ ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
        return False
    else:
        print(f"\n🎉 COMPLETELY CLEAN!")
        print(f"✅ Ready for production build")
        return True

def create_fresh_database():
    """✨ Create completely fresh database"""

    print(f"\n✨ CREATING FRESH DATABASE:")
    print("-" * 30)

    project_dir = Path(__file__).parent
    admin_data_dir = project_dir / "admin_data"
    admin_data_dir.mkdir(exist_ok=True)

    clean_db = {
        "keys": [],  # Completely empty
        "customers": [],  # Completely empty
        "statistics": {
            "total_keys_generated": 0,
            "trial_keys": 0,
            "monthly_keys": 0,
            "quarterly_keys": 0,
            "lifetime_keys": 0,
            "multi_device_keys": 0,
            "keys_activated": 0,
            "revenue_tracked": 0.0
        },
        "created_at": datetime.now().isoformat(),
        "version": "1.0"
    }

    db_path = admin_data_dir / "license_database.json"
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(clean_db, f, indent=2, ensure_ascii=False)

    print(f"✅ Fresh database created: {db_path.name}")
    print(f"🔑 Keys: 0")
    print(f"👥 Customers: 0")
    print(f"💰 Revenue: $0.00")

def show_next_steps():
    """📋 Show next steps"""

    print(f"\n🚀 PRODUCTION BUILD STEPS:")
    print("=" * 30)
    print(f"1. ✅ All license data cleaned")
    print(f"2. 🏗️ Build fresh EXE:")
    print(f"   python -m PyInstaller clausonet_build.spec")
    print(f"3. 📦 Test EXE:")
    print(f"   dist/ClausoNet4.0Pro.exe")
    print(f"4. ✅ Should show: 'No license found'")
    print(f"5. 🔑 Generate customer keys:")
    print(f"   python admin_tools/license_key_generator.py")
    print(f"6. 🚀 Ready for distribution!")

    print(f"\n🎯 CUSTOMER WORKFLOW:")
    print(f"   • Download clean EXE")
    print(f"   • Enter new license key")
    print(f"   • No old keys or warnings")
    print(f"   • Fresh activation process")

def main():
    """🚀 Main ultimate clean function"""

    print("🧹 CLAUSONET 4.0 PRO - ULTIMATE LICENSE CLEAN")
    print("=" * 55)

    # Execute all cleaning steps
    project_cleaned = clean_project_license_data()
    appdata_cleaned = clean_windows_appdata()
    keys_cleaned = clean_hardcoded_test_keys()

    # Create fresh database
    create_fresh_database()

    # Verify everything is clean
    if verify_ultimate_clean():
        show_next_steps()

        total_cleaned = project_cleaned + appdata_cleaned + keys_cleaned
        print(f"\n🎉 ULTIMATE CLEAN COMPLETE!")
        print(f"📊 Total items cleaned: {total_cleaned}")
        print(f"🎯 Ready for production build!")
    else:
        print(f"\n❌ Clean verification failed")
        print(f"💡 Please check and fix remaining issues")

if __name__ == "__main__":
    main()
