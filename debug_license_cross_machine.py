#!/usr/bin/env python3
"""
DEBUG: License Cross-Machine Issue
Tìm hiểu tại sao key không nhận được trên máy khác
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from admin_tools.license_key_generator import LicenseKeyGenerator

def analyze_license_issue():
    """Phân tích vấn đề license cross-machine"""
    print("🔍 PHÂN TÍCH VẤN ĐỀ LICENSE CROSS-MACHINE")
    print("=" * 60)
    
    # 1. Kiểm tra database hiện tại
    print("\n📊 1. KIỂM TRA DATABASE HIỆN TẠI:")
    print("-" * 40)
    
    try:
        license_gen = LicenseKeyGenerator()
        
        print(f"📁 Database path: {license_gen.license_database_path}")
        print(f"📄 Database exists: {os.path.exists(license_gen.license_database_path)}")
        
        if os.path.exists(license_gen.license_database_path):
            with open(license_gen.license_database_path, 'r', encoding='utf-8') as f:
                db_content = json.load(f)
            
            keys_count = len(db_content.get('keys', []))
            print(f"🔑 Total keys in database: {keys_count}")
            
            if keys_count > 0:
                print("\n📋 Available keys:")
                for i, key_data in enumerate(db_content['keys']):
                    key = key_data.get('key', 'N/A')
                    key_type = key_data.get('type', 'unknown')
                    status = key_data.get('status', 'unknown')
                    print(f"   {i+1}. {key} ({key_type}) - {status}")
            else:
                print("⚠️ Database is EMPTY!")
        else:
            print("❌ Database NOT FOUND!")
            
    except Exception as e:
        print(f"❌ Error analyzing database: {e}")

def create_test_key_for_cross_machine():
    """Tạo key test cho cross-machine"""
    print("\n🔧 2. SỬ DỤNG KEY CÓ SẴN CHO TEST:")
    print("-" * 40)
    
    try:
        license_gen = LicenseKeyGenerator()
        
        # Sử dụng key có sẵn thay vì tạo mới
        if len(license_gen.database['keys']) > 0:
            test_key = license_gen.database['keys'][1]['key']  # CNPRO-DZGJ-TOYE-C34N-EVR0
            print(f"🔑 Using existing test key: {test_key}")
            
            # Verify key trong database
            print(f"\n🔍 Verifying key in database...")
            
            # Tìm key
            found = False
            for key_info in license_gen.database['keys']:
                if key_info.get('key') == test_key:
                    found = True
                    print(f"✅ Key found in database!")
                    print(f"   Type: {key_info.get('type')}")
                    print(f"   Status: {key_info.get('status')}")
                    print(f"   Hardware IDs: {key_info.get('hardware_ids', [])}")
                    print(f"   Max devices: {key_info.get('max_devices', 1)}")
                    break
            
            if not found:
                print(f"❌ Key NOT found in database!")
                
            return test_key
        else:
            print("❌ No keys in database!")
            return None
            
    except Exception as e:
        print(f"❌ Error getting test key: {e}")
        return None

def test_activation_locally(test_key):
    """Test activation trên máy local"""
    print(f"\n🧪 3. TEST ACTIVATION LOCAL:")
    print("-" * 40)
    
    if not test_key:
        print("❌ No test key to test")
        return False
        
    try:
        license_gen = LicenseKeyGenerator()
        
        print(f"🔑 Testing activation of: {test_key}")
        
        # Get current hardware
        hw_id = license_gen.get_hardware_fingerprint()
        print(f"🖥️ Current hardware ID: {hw_id[:10]}...")
        
        # Test activation
        result = license_gen.activate_license(test_key)
        
        if result:
            print("✅ Activation successful on local machine!")
        else:
            print("❌ Activation failed on local machine!")
            
        return result
        
    except Exception as e:
        print(f"❌ Error testing activation: {e}")
        return False

def analyze_cross_machine_scenario():
    """Phân tích scenario cross-machine"""
    print(f"\n📱 4. PHÂN TÍCH CROSS-MACHINE SCENARIO:")
    print("-" * 40)
    
    print("🎯 VẤN ĐỀ CHÍNH:")
    print("   1. Database trên máy development có keys")
    print("   2. Database trên máy khác (máy user) LÀ TRỐNG!")
    print("   3. Khi user nhập key → App check trong database local (trống)")
    print("   4. → Key not found!")
    
    print("\n💡 GIẢI PHÁP:")
    print("   A. Copy database từ máy dev sang máy user")
    print("   B. Hoặc tạo central database server")
    print("   C. Hoặc embed keys vào app")
    
    print("\n🚀 HƯỚNG DẪN CHO USER:")
    print("   1. Copy toàn bộ thư mục admin_data từ máy dev")
    print("   2. Paste vào: C:\\Users\\dattu.TUEMINH-PC\\AppData\\Local\\ClausoNet4.0\\")
    print("   3. Restart app và thử lại")

def create_portable_database():
    """Tạo portable database để copy sang máy khác"""
    print(f"\n📦 5. TẠO PORTABLE DATABASE:")
    print("-" * 40)
    
    try:
        license_gen = LicenseKeyGenerator()
        
        # Tạo thư mục portable
        portable_dir = Path("portable_license_package")
        portable_dir.mkdir(exist_ok=True)
        
        admin_data_dir = portable_dir / "admin_data"
        admin_data_dir.mkdir(exist_ok=True)
        
        # Copy database
        import shutil
        if os.path.exists(license_gen.license_database_path):
            target_db = admin_data_dir / "license_database.json"
            shutil.copy2(license_gen.license_database_path, target_db)
            print(f"✅ Database copied to: {target_db}")
            
            # Tạo hướng dẫn install
            install_guide = portable_dir / "INSTALL_GUIDE.txt"
            
            guide_content = f"""
🔧 HƯỚNG DẪN CÀI ĐẶT LICENSE DATABASE

📁 1. COPY FOLDER admin_data:
   - Copy thư mục 'admin_data' trong package này
   - Paste vào: C:\\Users\\[USERNAME]\\AppData\\Local\\ClausoNet4.0\\
   
   Ví dụ với user 'dattu.TUEMINH-PC':
   C:\\Users\\dattu.TUEMINH-PC\\AppData\\Local\\ClausoNet4.0\\admin_data\\

🔄 2. RESTART APP:
   - Đóng hoàn toàn ClausoNet 4.0
   - Mở lại app
   
🔑 3. NHẬP LICENSE KEY:
   - Sử dụng một trong các keys có sẵn trong database
   - Hoặc tạo key mới từ máy development

📊 THỐNG KÊ DATABASE:
   - Tạo lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
   - Total keys: {len(license_gen.database['keys'])}

📋 CÁC KEY CÓ SẴN:
"""
            
            for i, key_data in enumerate(license_gen.database['keys']):
                key = key_data.get('key', 'N/A')
                key_type = key_data.get('type', 'unknown')
                customer_name = 'Unknown'
                if 'customer_info' in key_data and key_data['customer_info']:
                    customer_name = key_data['customer_info'].get('name', 'Unknown')
                guide_content += f"   {i+1}. {key} ({key_type}) - {customer_name}\n"
            
            guide_content += f"""
⚠️ LƯU Ý:
   - Backup database cũ trước khi copy (nếu có)
   - Đảm bảo đường dẫn chính xác
   - Check log file để debug nếu có lỗi

💬 HỖ TRỢ:
   - Nếu vẫn lỗi, gửi log file từ app
   - Log thường ở: AppData\\Local\\ClausoNet4.0\\logs\\
"""
            
            with open(install_guide, 'w', encoding='utf-8') as f:
                f.write(guide_content)
                
            print(f"✅ Install guide created: {install_guide}")
            print(f"\n📦 Portable package ready at: {portable_dir}")
            print("🎯 Send this folder to user on other machine!")
            
            return str(portable_dir)
        else:
            print("❌ Source database not found!")
            return None
            
    except Exception as e:
        print(f"❌ Error creating portable package: {e}")
        return None

def main():
    """Main debug function"""
    print("🚀 ClausoNet 4.0 Pro - Cross-Machine License Debug")
    print("=" * 60)
    
    # 1. Analyze current situation
    analyze_license_issue()
    
    # 2. Create test key
    test_key = create_test_key_for_cross_machine()
    
    # 3. Test activation locally
    if test_key:
        test_activation_locally(test_key)
    
    # 4. Analyze cross-machine scenario
    analyze_cross_machine_scenario()
    
    # 5. Create portable package
    portable_path = create_portable_database()
    
    print("\n✅ DEBUG COMPLETE!")
    print("=" * 60)
    
    if portable_path:
        print(f"📦 Portable package: {portable_path}")
        print("🎯 Send this to user machine!")
    
    if test_key:
        print(f"🔑 Test key for cross-machine: {test_key}")

if __name__ == "__main__":
    main()
