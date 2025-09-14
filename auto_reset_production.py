#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗑️ Auto Reset Production Database
Tự động xóa tất cả test keys và tạo database sạch cho production
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

def auto_reset_license_database():
    """🔄 Tự động reset license database về trạng thái production sạch"""

    print("🗑️ AUTO RESET PRODUCTION DATABASE")
    print("=" * 40)

    # Paths
    project_dir = Path(__file__).parent
    db_path = project_dir / "admin_data" / "license_database.json"
    backup_path = project_dir / "admin_data" / f"license_database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # 1. Backup current database
    if db_path.exists():
        shutil.copy2(db_path, backup_path)
        print(f"📁 Backup created: {backup_path.name}")

        # Show current keys
        with open(db_path, 'r', encoding='utf-8') as f:
            current_db = json.load(f)

        print(f"\n🔑 REMOVING DEV TEST KEYS:")
        for i, key_data in enumerate(current_db.get('keys', []), 1):
            key = key_data.get('key', 'Unknown')
            key_type = key_data.get('type', 'unknown')
            status = key_data.get('status', 'unknown')
            print(f"   {i}. {key} ({key_type}) - {status}")

        print(f"\n📊 Total dev keys removed: {len(current_db.get('keys', []))}")
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
    print(f"📍 Clean database: admin_data/license_database.json")
    print(f"🔑 Keys in database: 0 (clean slate)")
    print(f"💰 Revenue tracked: $0.00")

    # 4. Verify clean database
    with open(db_path, 'r', encoding='utf-8') as f:
        verify_db = json.load(f)

    keys_count = len(verify_db.get('keys', []))
    customers_count = len(verify_db.get('customers', []))

    print(f"\n✅ VERIFICATION:")
    print(f"🔑 License keys: {keys_count}")
    print(f"👥 Customers: {customers_count}")

    if keys_count == 0 and customers_count == 0:
        print(f"✅ Database is clean - Ready for production!")
        return True
    else:
        print(f"⚠️ Database not completely clean")
        return False

def show_build_instructions():
    """📋 Show build instructions"""

    print(f"\n🚀 NEXT STEPS - BUILD PRODUCTION EXE:")
    print("=" * 45)
    print(f"1. 🧹 Database cleaned ✅")
    print(f"2. 🏗️ Build command:")
    print(f"   pyinstaller clausonet_build.spec")
    print(f"3. 📦 Output location:")
    print(f"   dist/ClausoNet4.0Pro.exe")
    print(f"4. 🔑 Generate customer keys:")
    print(f"   python admin_tools/license_key_generator.py")
    print(f"5. 🚀 Distribute to customers!")

    print(f"\n🎯 CUSTOMER WORKFLOW:")
    print(f"   • Download: ClausoNet4.0Pro.exe")
    print(f"   • Run EXE: First time startup")
    print(f"   • Enter key: CNPRO-XXXX-XXXX-XXXX-XXXX")
    print(f"   • Activate: License stored permanently")
    print(f"   • Use tool: Full access to features")

def main():
    """🚀 Main auto reset function"""

    print("🗑️ CLAUSONET 4.0 PRO - AUTO PRODUCTION RESET")
    print("=" * 55)

    # Execute reset automatically
    success = auto_reset_license_database()

    if success:
        show_build_instructions()
        print(f"\n🎉 PRODUCTION RESET COMPLETE - READY TO BUILD!")
    else:
        print(f"\n❌ Reset failed")

if __name__ == "__main__":
    main()
