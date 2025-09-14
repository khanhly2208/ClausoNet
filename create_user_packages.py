#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📦 Package Creator for End Users
Tạo gói phân phối cho khách hàng cuối
"""

import os
import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime, timedelta

def create_user_package():
    """📦 Tạo gói phân phối cho người dùng"""

    print("📦 CREATING USER DEPLOYMENT PACKAGE")
    print("=" * 50)

    # Tạo thư mục package
    package_dir = Path("user_package")
    package_dir.mkdir(exist_ok=True)

    print(f"📁 Package directory: {package_dir}")

    # 1. Copy EXE file (giả lập - sẽ có sau khi build)
    exe_source = Path("dist/ClausoNet4.0Pro.exe")
    exe_dest = package_dir / "ClausoNet4.0Pro.exe"

    if exe_source.exists():
        shutil.copy2(exe_source, exe_dest)
        print(f"✅ Copied EXE: {exe_source} → {exe_dest}")
    else:
        # Tạo file giả để demo
        with open(exe_dest, 'w') as f:
            f.write("# ClausoNet 4.0 Pro Executable (Demo)\n")
            f.write("# Size: ~50-100MB after real build\n")
        print(f"⚠️ Created demo EXE: {exe_dest}")

    # 2. Tạo file README cho user
    readme_content = """
# ClausoNet 4.0 Pro - Installation Guide

## 🚀 Quick Start:
1. Run ClausoNet4.0Pro.exe
2. Enter your license key when prompted
3. Click "Activate License"
4. Start creating AI videos!

## 🔑 Your License Information:
- License Key: [See LICENSE_KEY.txt file]
- License Type: [Trial/Monthly/Lifetime]
- Expires: [Date will be shown in software]
- Max Devices: [1/3/5] computer(s)

## 📋 System Requirements:
- Windows 10/11 (64-bit)
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space
- Internet connection for initial activation

## 🔔 Important Notes:
- You'll receive notifications before license expires
- Trial version works on 1 computer only
- For technical support: help@clausonet.com
- For license renewal: support@clausonet.com

## 🎥 Getting Started:
- Video tutorials: https://clausonet.com/tutorials
- User manual: https://docs.clausonet.com
- Community forum: https://forum.clausonet.com

Thank you for choosing ClausoNet 4.0 Pro!
"""

    readme_file = package_dir / "README.txt"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"✅ Created README: {readme_file}")

    return package_dir

def create_license_scenarios():
    """🔑 Tạo các scenario license khác nhau"""

    scenarios = {
        "trial": {
            "name": "Trial User (7 days)",
            "key": "CNPRO-TRIAL-DEMO-2025-FREE",
            "type": "trial",
            "duration": 7,
            "max_devices": 1,
            "price": 0,
            "features": ["basic_generation", "limited_workflows"]
        },
        "monthly": {
            "name": "Monthly License",
            "key": "CNPRO-MONTH-PAID-2025-USER",
            "type": "monthly",
            "duration": 30,
            "max_devices": 1,
            "price": 29.99,
            "features": ["ai_generation", "unlimited_workflows", "api_access"]
        },
        "quarterly": {
            "name": "Quarterly License",
            "key": "CNPRO-QUART-PAID-2025-USER",
            "type": "quarterly",
            "duration": 90,
            "max_devices": 3,
            "price": 79.99,
            "features": ["ai_generation", "unlimited_workflows", "api_access", "priority_support"]
        },
        "enterprise": {
            "name": "Enterprise Multi-Device",
            "key": "CNPRO-MULTI-TEAM-2025-CORP",
            "type": "multi_device",
            "duration": 365,
            "max_devices": 10,
            "price": 299.99,
            "features": ["ai_generation", "unlimited_workflows", "api_access", "priority_support", "team_management"]
        },
        "lifetime": {
            "name": "Lifetime License",
            "key": "CNPRO-LIFE-PREM-2025-USER",
            "type": "lifetime",
            "duration": 36500,  # 100 years
            "max_devices": 1,
            "price": 499.99,
            "features": ["ai_generation", "unlimited_workflows", "api_access", "priority_support", "lifetime_updates"]
        }
    }

    return scenarios

def create_customer_package(customer_type, customer_email="demo@example.com"):
    """📧 Tạo gói cụ thể cho từng loại khách hàng"""

    print(f"\n📧 CREATING PACKAGE FOR: {customer_type.upper()}")
    print("-" * 40)

    # Tạo base package
    package_dir = create_user_package()

    # Get license scenario
    scenarios = create_license_scenarios()
    license_info = scenarios.get(customer_type, scenarios["trial"])

    # Tạo license key file
    current_date = datetime.now()
    expiry_date = current_date + timedelta(days=license_info["duration"])

    license_content = f"""
🔑 ClausoNet 4.0 Pro - Your License Key

Customer: {customer_email}
Purchase Date: {current_date.strftime('%Y-%m-%d %H:%M:%S')}

LICENSE INFORMATION:
===================
License Key: {license_info['key']}
License Type: {license_info['name']}
Duration: {license_info['duration']} days
Expires: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}
Max Devices: {license_info['max_devices']} computer(s)
Price Paid: ${license_info['price']:.2f}

FEATURES INCLUDED:
================
{chr(10).join('• ' + feature.replace('_', ' ').title() for feature in license_info['features'])}

ACTIVATION INSTRUCTIONS:
=======================
1. Run ClausoNet4.0Pro.exe
2. When prompted, enter this license key:
   {license_info['key']}
3. Click "Activate License"
4. Software will bind to your computer's hardware
5. Start using immediately!

IMPORTANT NOTES:
===============
• This license is valid until {expiry_date.strftime('%Y-%m-%d')}
• Can be activated on maximum {license_info['max_devices']} computer(s)
• You'll receive expiry notifications before license expires
• For support: help@clausonet.com
• For renewal: support@clausonet.com

Thank you for choosing ClausoNet 4.0 Pro!
"""

    license_file = package_dir / "LICENSE_KEY.txt"
    with open(license_file, 'w', encoding='utf-8') as f:
        f.write(license_content)
    print(f"✅ Created license file: {license_file}")

    # Tạo email template
    email_template = f"""
Subject: ClausoNet 4.0 Pro - Your {license_info['name']}

Dear Customer,

Thank you for purchasing ClausoNet 4.0 Pro!

🎯 YOUR LICENSE DETAILS:
License Key: {license_info['key']}
License Type: {license_info['name']}
Expires: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}
Max Devices: {license_info['max_devices']} computer(s)
Features: {', '.join(license_info['features'])}

📥 INSTALLATION:
1. Download the attached ClausoNet4.0Pro.exe
2. Run the application
3. Enter your license key: {license_info['key']}
4. Click "Activate License"
5. Start creating amazing AI videos!

🔔 IMPORTANT:
- Your license expires on {expiry_date.strftime('%Y-%m-%d')}
- You'll receive notifications before expiry
- For renewal: support@clausonet.com
- Technical help: help@clausonet.com

Best regards,
ClausoNet Team
"""

    email_file = package_dir / "EMAIL_TEMPLATE.txt"
    with open(email_file, 'w', encoding='utf-8') as f:
        f.write(email_template)
    print(f"✅ Created email template: {email_file}")

    # Tạo ZIP package
    zip_filename = f"ClausoNet4.0Pro_{customer_type}_{current_date.strftime('%Y%m%d')}.zip"
    zip_path = Path(zip_filename)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in package_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(package_dir)
                zipf.write(file_path, arcname)

    print(f"📦 Created ZIP package: {zip_path}")
    print(f"📊 Package size: {zip_path.stat().st_size / 1024:.1f} KB")

    return zip_path, license_info

def demo_all_packages():
    """🎯 Demo tạo tất cả loại package"""

    print("🎯 DEMO: CREATING ALL CUSTOMER PACKAGES")
    print("=" * 50)

    scenarios = create_license_scenarios()
    created_packages = []

    for customer_type, info in scenarios.items():
        zip_path, license_info = create_customer_package(customer_type)
        created_packages.append({
            "type": customer_type,
            "zip": zip_path,
            "license": license_info
        })

    print(f"\n📊 SUMMARY - CREATED PACKAGES:")
    print("=" * 35)

    for pkg in created_packages:
        print(f"📦 {pkg['type'].title()}: {pkg['zip']}")
        print(f"   🔑 Key: {pkg['license']['key']}")
        print(f"   💰 Price: ${pkg['license']['price']:.2f}")
        print(f"   🖥️ Devices: {pkg['license']['max_devices']}")
        print(f"   ⏰ Duration: {pkg['license']['duration']} days")
        print()

    print("🎯 READY FOR DISTRIBUTION!")
    print("✅ Each ZIP contains: EXE + License Key + Instructions")
    print("✅ Send appropriate ZIP to different customer types")
    print("✅ Customer experience: Download → Run → Enter Key → Use")

def main():
    """🚀 Main function"""
    print("📦 ClausoNet 4.0 Pro - Package Creator for End Users")
    print("=" * 60)

    print("\n📋 PACKAGE OPTIONS:")
    print("1. 🆓 Trial Package (7 days)")
    print("2. 💰 Monthly Package ($29.99)")
    print("3. 📅 Quarterly Package ($79.99)")
    print("4. 🏢 Enterprise Package ($299.99)")
    print("5. 🎯 Lifetime Package ($499.99)")
    print("6. 🎪 Create ALL packages (demo)")
    print("0. ❌ Exit")

    choice = input("\nSelect package type: ").strip()

    if choice == "0":
        print("👋 Goodbye!")
        return
    elif choice == "6":
        demo_all_packages()
    else:
        package_types = {
            "1": "trial",
            "2": "monthly",
            "3": "quarterly",
            "4": "enterprise",
            "5": "lifetime"
        }

        customer_type = package_types.get(choice, "trial")
        customer_email = input("Enter customer email (optional): ").strip() or "demo@example.com"

        zip_path, license_info = create_customer_package(customer_type, customer_email)

        print(f"\n✅ PACKAGE CREATED SUCCESSFULLY!")
        print(f"📦 File: {zip_path}")
        print(f"🔑 License: {license_info['key']}")
        print(f"📧 Ready to send to: {customer_email}")

if __name__ == "__main__":
    main()
