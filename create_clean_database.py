#!/usr/bin/env python3
"""
Tạo clean database cho phân phối exe
Loại bỏ key đã activated và data cá nhân
"""

import json
import os
from datetime import datetime

def create_clean_database():
    """Tạo database sạch cho phân phối"""

    # Đọc database hiện tại
    with open("admin_data/license_database.json", 'r', encoding='utf-8') as f:
        current_db = json.load(f)

    # Tạo database sạch
    clean_db = {
        "keys": [],
        "customers": [],
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

    # Chỉ giữ lại key CHƯA ACTIVATED
    for key_data in current_db["keys"]:
        if key_data.get("status") == "generated" and not key_data.get("hardware_ids"):
            # Reset activation data
            clean_key = key_data.copy()
            clean_key["activation_count"] = 0
            clean_key["hardware_ids"] = []
            clean_key["status"] = "generated"
            if "activated_at" in clean_key:
                del clean_key["activated_at"]

            clean_db["keys"].append(clean_key)

            # Update statistics
            key_type = clean_key.get("type", "unknown")
            if key_type == "trial":
                clean_db["statistics"]["trial_keys"] += 1
            elif key_type == "monthly":
                clean_db["statistics"]["monthly_keys"] += 1
            elif key_type == "quarterly":
                clean_db["statistics"]["quarterly_keys"] += 1
            elif key_type == "lifetime":
                clean_db["statistics"]["lifetime_keys"] += 1
            elif key_type == "multi_device":
                clean_db["statistics"]["multi_device_keys"] += 1

            clean_db["statistics"]["total_keys_generated"] += 1
            clean_db["statistics"]["revenue_tracked"] += clean_key.get("price", 0.0)

    print(f"🔄 Original database: {len(current_db['keys'])} keys")
    print(f"✅ Clean database: {len(clean_db['keys'])} keys (unused only)")

    # Backup original
    backup_path = "admin_data/license_database_original.json"
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(current_db, f, indent=2, ensure_ascii=False)
    print(f"💾 Original backed up to: {backup_path}")

    # Save clean database
    clean_path = "admin_data/license_database_clean.json"
    with open(clean_path, 'w', encoding='utf-8') as f:
        json.dump(clean_db, f, indent=2, ensure_ascii=False)
    print(f"✨ Clean database created: {clean_path}")

    print("\n📋 AVAILABLE KEYS FOR DISTRIBUTION:")
    for key_data in clean_db["keys"]:
        key_type = key_data.get("type", "unknown").upper()
        key = key_data.get("key", "")
        price = key_data.get("price", 0.0)
        print(f"  {key_type:10} | {key} | ${price}")

    print(f"\n🎯 To build exe for distribution:")
    print(f"   1. Copy clean database: copy admin_data\\license_database_clean.json admin_data\\license_database.json")
    print(f"   2. Build exe: pyinstaller clausonet_build.spec --clean")
    print(f"   3. Distribute exe with unused keys only")

if __name__ == "__main__":
    create_clean_database()
