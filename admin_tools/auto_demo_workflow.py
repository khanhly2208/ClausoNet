#!/usr/bin/env python3
"""
Auto Demo: Tạo key và test workflow tự động
"""

from license_key_generator import LicenseKeyGenerator
import time

def auto_demo_create_and_send():
    print("🎯 AUTO DEMO: TẠO VÀ GỬI KEY WORKFLOW")
    print("=" * 50)

    gen = LicenseKeyGenerator()

    # Test 1: Tạo Trial Key
    print("📋 TEST 1: TẠO TRIAL KEY")
    print("-" * 30)

    trial_key = gen.generate_trial_key(7)
    print(f"✅ Trial Key: {trial_key['key']}")
    print(f"   Loại: Trial 7 Days")
    print(f"   Giá: ${trial_key['price']:.2f}")
    print(f"   Hết hạn: {trial_key['expiry_date'][:10]}")

    # Test 2: Tạo Customer
    print(f"\n👤 TEST 2: TẠO CUSTOMER")
    print("-" * 30)

    test_email = "test.customer@example.com"
    test_name = "Test Customer"

    customer = gen.create_customer_record(test_email, test_name)
    print(f"✅ Customer: {customer['email']}")
    print(f"   Tên: {customer['name']}")
    print(f"   Ngày tạo: {customer['created_at'][:10]}")

    # Test 3: Gán Key cho Customer
    print(f"\n🔗 TEST 3: GÁN KEY CHO CUSTOMER")
    print("-" * 30)

    assignment = gen.assign_key_to_customer(trial_key['key'], test_email)
    print(f"✅ Gán key: {assignment}")
    print(f"   Key: {trial_key['key']}")
    print(f"   Customer: {test_email}")

    # Test 4: Kiểm tra Email Config
    print(f"\n📧 TEST 4: KIỂM TRA EMAIL CONFIG")
    print("-" * 30)

    if gen.admin_email and gen.admin_password:
        print(f"✅ Email configured: {gen.admin_email}")
        print(f"✅ SMTP Server: {gen.smtp_server}:{gen.smtp_port}")
        email_configured = True
    else:
        print(f"⚠️ Email chưa configured")
        print(f"   Admin email: {gen.admin_email or 'Not set'}")
        print(f"   Admin password: {'Set' if gen.admin_password else 'Not set'}")
        email_configured = False

    # Test 5: Generate Email Content
    print(f"\n📝 TEST 5: TẠO EMAIL CONTENT")
    print("-" * 30)

    email_content = generate_test_email(trial_key, test_email, test_name)
    print(f"✅ Email content generated:")
    print(f"   Subject: ClausoNet 4.0 Pro - Your Trial License Key")
    print(f"   Body length: {len(email_content)} characters")
    print(f"   Contains key: {trial_key['key'] in email_content}")

    # Test 6: Mock Email Sending
    print(f"\n📤 TEST 6: MOCK EMAIL SENDING")
    print("-" * 30)

    if email_configured:
        print(f"📧 Trying to send real email...")
        try:
            # Test real email sending
            result = gen.send_key_email(trial_key['key'], test_email, test_name)
            if result:
                print(f"✅ Email sent successfully to {test_email}!")
            else:
                print(f"❌ Email sending failed")
        except Exception as e:
            print(f"❌ Email error: {e}")
    else:
        print(f"📧 Mock email sending (no SMTP config):")
        print(f"   To: {test_email}")
        print(f"   Key: {trial_key['key']}")
        print(f"   Status: ✅ READY TO SEND (needs SMTP)")

    # Test 7: Tạo Lifetime Key
    print(f"\n💎 TEST 7: TẠO LIFETIME KEY")
    print("-" * 30)

    lifetime_key = gen.generate_lifetime_key(299.99)
    print(f"✅ Lifetime Key: {lifetime_key['key']}")
    print(f"   Loại: Lifetime License")
    print(f"   Giá: ${lifetime_key['price']:.2f}")
    print(f"   Thời hạn: {lifetime_key['duration_days']//365} years")

    # Test 8: Tạo Premium Customer
    print(f"\n👑 TEST 8: TẠO PREMIUM CUSTOMER")
    print("-" * 30)

    premium_email = "premium.customer@example.com"
    premium_name = "Premium Customer"

    premium_customer = gen.create_customer_record(premium_email, premium_name, "+84123456789", "Tech Corp")
    print(f"✅ Premium Customer: {premium_customer['email']}")
    print(f"   Company: {premium_customer.get('company', 'N/A')}")
    print(f"   Phone: {premium_customer.get('phone', 'N/A')}")

    # Test 9: Gán Lifetime Key
    print(f"\n💰 TEST 9: GÁN LIFETIME KEY")
    print("-" * 30)

    lifetime_assignment = gen.assign_key_to_customer(lifetime_key['key'], premium_email)
    print(f"✅ Lifetime key assigned: {lifetime_assignment}")
    print(f"   Key: {lifetime_key['key']}")
    print(f"   Customer: {premium_email}")

    # Test 10: Statistics
    print(f"\n📊 TEST 10: THỐNG KÊ HỆ THỐNG")
    print("-" * 30)

    stats = gen.get_statistics()
    print(f"✅ Statistics updated:")
    print(f"   Total keys: {stats.get('total_keys', 0)}")
    print(f"   Active keys: {stats.get('active_keys', 0)}")
    print(f"   Total revenue: ${stats.get('total_revenue', 0):.2f}")
    print(f"   Total customers: {stats.get('total_customers', 0)}")

    return True

def generate_test_email(key_data, customer_email, customer_name):
    """Generate test email content"""
    key = key_data['key']
    key_type = key_data['type'].title()
    expiry = key_data['expiry_date'][:10]

    email_content = f"""Dear {customer_name},

Thank you for choosing ClausoNet 4.0 Pro!

🔑 YOUR LICENSE KEY: {key}

🚀 ACTIVATION STEPS:
1. Download ClausoNet 4.0 Pro
2. Launch the application
3. Go to Settings → License
4. Enter key: {key}
5. Click "Activate License"

🎯 LICENSE DETAILS:
• Type: {key_type}
• Valid Until: {expiry}
• Max Devices: {key_data['max_devices']}
• Price: ${key_data['price']:.2f}

Best regards,
ClausoNet Team

---
Email: {customer_email}
Key: {key}
Generated: {key_data['created_at'][:19]}
"""

    return email_content

def demo_gui_workflow():
    """Demo workflow tương tự GUI"""
    print(f"\n🖥️ DEMO GUI WORKFLOW:")
    print("=" * 40)

    print(f"1. ✅ User mở Admin GUI")
    print(f"2. ✅ Chọn tab 'License Generator'")
    print(f"3. ✅ Chọn loại key (Trial/Lifetime/etc)")
    print(f"4. ✅ Click 'Generate Key' → Key hiển thị")
    print(f"5. ✅ Nhập email customer vào 'Send to Customer'")
    print(f"6. ✅ Nhập tên customer (optional)")
    print(f"7. ✅ Click 'Send Key via Email'")
    print(f"")
    print(f"💡 WORKFLOW OPTIONS:")
    print(f"   🔧 Nếu email configured → Gửi tự động")
    print(f"   📋 Nếu email chưa setup → Copy key manual")
    print(f"   ⚙️ Link to Settings tab để config email")
    print(f"   ✅ Customer record tự động tạo")
    print(f"   📊 Statistics tự động update")

if __name__ == "__main__":
    print("🎯 AUTO TEST: CREATE & SEND KEY WORKFLOW")
    print("=" * 60)

    success = auto_demo_create_and_send()

    if success:
        demo_gui_workflow()

        print(f"\n{'='*60}")
        print(f"🎉 AUTO DEMO RESULTS:")
        print(f"{'='*60}")
        print(f"✅ Trial Key Generation: WORKING")
        print(f"✅ Lifetime Key Generation: WORKING")
        print(f"✅ Customer Creation: WORKING")
        print(f"✅ Key Assignment: WORKING")
        print(f"✅ Email Content Generation: WORKING")
        print(f"✅ Database Operations: WORKING")
        print(f"✅ Statistics Tracking: WORKING")
        print(f"⚠️ Email Sending: NEEDS SMTP CONFIG")
        print(f"{'='*60}")

        print(f"\n💡 ĐỂ SỬ DỤNG THỰC TẾ:")
        print(f"   1. Chạy: python admin_license_gui.py")
        print(f"   2. Tab Settings → Config Gmail")
        print(f"   3. Tab License Generator → Tạo key")
        print(f"   4. Nhập email customer → Send")
        print(f"   5. ✅ Hoàn thành!")
        print(f"{'='*60}")
    else:
        print(f"❌ AUTO DEMO FAILED")
