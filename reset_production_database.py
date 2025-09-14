#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗑️ Reset Production Database
Xóa tất cả test keys và tạo database sạch cho production
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

def reset_license_database():
    """🔄 Reset license database về trạng thái production sạch"""

    print("🗑️ RESET PRODUCTION DATABASE")
    print("=" * 35)

    # Paths
    project_dir = Path(__file__).parent
    db_path = project_dir / "admin_data" / "license_database.json"
    backup_path = project_dir / "admin_data" / f"license_database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # 1. Backup current database
    if db_path.exists():
        shutil.copy2(db_path, backup_path)
        print(f"📁 Backup created: {backup_path}")

        # Show current keys
        with open(db_path, 'r', encoding='utf-8') as f:
            current_db = json.load(f)

        print(f"\n🔑 CURRENT KEYS TO BE REMOVED:")
        for i, key_data in enumerate(current_db.get('keys', []), 1):
            key = key_data.get('key', 'Unknown')
            key_type = key_data.get('type', 'unknown')
            status = key_data.get('status', 'unknown')
            print(f"   {i}. {key} ({key_type}) - {status}")

        print(f"\n📊 Total keys to remove: {len(current_db.get('keys', []))}")
    else:
        print(f"❌ Database not found: {db_path}")
        return False

    # 2. Create clean production database
    clean_db = {
        "keys": [],  # Empty - no test keys
        "customers": [],  # Empty - no test customers
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

    # 3. Write clean database
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(clean_db, f, indent=2, ensure_ascii=False)

    print(f"\n✅ PRODUCTION DATABASE RESET COMPLETE!")
    print(f"📍 Clean database created: {db_path}")
    print(f"🔑 Keys in database: 0 (clean slate)")
    print(f"👥 Customers in database: 0")
    print(f"💰 Revenue tracked: $0.00")

    return True

def reset_user_settings():
    """🔧 Reset user settings và activation data"""

    print(f"\n🔧 RESET USER SETTINGS:")
    print("-" * 25)

    project_dir = Path(__file__).parent

    # User data files to reset
    user_files = [
        "config.yaml",  # Có thể chứa activation data
        "user_settings.json",
        "activation_cache.json",
        "hardware_fingerprint.json"
    ]

    removed_files = []
    for file_name in user_files:
        file_path = project_dir / file_name
        if file_path.exists():
            backup_name = f"{file_name}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = project_dir / "backups" / backup_name

            # Create backups directory
            backup_path.parent.mkdir(exist_ok=True)

            # Backup and remove
            shutil.copy2(file_path, backup_path)
            file_path.unlink()

            removed_files.append(file_name)
            print(f"🗑️ Removed: {file_name} (backup: {backup_name})")

    if removed_files:
        print(f"✅ Reset {len(removed_files)} user files")
    else:
        print(f"✅ No user files to reset")

def verify_clean_database():
    """✅ Verify database is clean"""

    print(f"\n✅ VERIFICATION:")
    print("-" * 15)

    project_dir = Path(__file__).parent
    db_path = project_dir / "admin_data" / "license_database.json"

    if not db_path.exists():
        print(f"❌ Database missing: {db_path}")
        return False

    with open(db_path, 'r', encoding='utf-8') as f:
        db_data = json.load(f)

    keys_count = len(db_data.get('keys', []))
    customers_count = len(db_data.get('customers', []))

    print(f"🔑 License keys: {keys_count}")
    print(f"👥 Customers: {customers_count}")
    print(f"💰 Revenue: ${db_data.get('statistics', {}).get('revenue_tracked', 0)}")

    if keys_count == 0 and customers_count == 0:
        print(f"✅ Database is clean - Ready for production!")
        return True
    else:
        print(f"⚠️ Database not completely clean")
        return False

def show_next_steps():
    """📋 Show next steps for production"""

    print(f"\n📋 NEXT STEPS FOR PRODUCTION:")
    print("=" * 35)
    print(f"1. ✅ Database reset complete")
    print(f"2. 🏗️ Build EXE: pyinstaller clausonet_build.spec")
    print(f"3. 📦 Test EXE: dist/ClausoNet4.0Pro.exe")
    print(f"4. 🔑 Generate keys for customers:")
    print(f"   python admin_tools/license_key_generator.py")
    print(f"5. 🚀 Distribute EXE + license keys to users")

    print(f"\n🎯 PRODUCTION WORKFLOW:")
    print(f"   User downloads: ClausoNet4.0Pro.exe")
    print(f"   User enters key: CNPRO-XXXX-XXXX-XXXX-XXXX")
    print(f"   App activates: License stored in embedded database")
    print(f"   Cross-machine: License travels with EXE")

def main():
    """🚀 Main reset function"""

    print("🗑️ CLAUSONET 4.0 PRO - PRODUCTION DATABASE RESET")
    print("=" * 55)

    # Confirm reset
    print("⚠️ WARNING: This will remove ALL test keys and customer data!")
    print("📁 Backups will be created automatically")

    user_input = input("\n❓ Continue with database reset? (yes/no): ").strip().lower()

    if user_input not in ['yes', 'y']:
        print("❌ Reset cancelled by user")
        return

    # Execute reset
    success = reset_license_database()
    if not success:
        print("❌ Database reset failed")
        return

    reset_user_settings()

    # Verify
    if verify_clean_database():
        show_next_steps()
        print(f"\n🎉 PRODUCTION RESET COMPLETE!")
    else:
        print(f"\n❌ Reset verification failed")

if __name__ == "__main__":
    main()
