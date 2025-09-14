#!/usr/bin/env python3
"""
Demo: Tạo key và gửi trực tiếp cho customer
"""

from license_key_generator import LicenseKeyGenerator
import time

def demo_create_and_send_key():
    print("🎯 DEMO: TẠO VÀ GỬI KEY TRỰC TIẾP CHO CUSTOMER")
    print("=" * 60)

    gen = LicenseKeyGenerator()

    # Step 1: Show options
    print("📋 LOẠI KEY CÓ THỂ TẠO:")
    print("-" * 30)
    print("1. Trial Key (7 ngày) - FREE")
    print("2. Trial Key (30 ngày) - FREE")
    print("3. Monthly Key - $29.99")
    print("4. Quarterly Key - $79.99")
    print("5. Lifetime Key - $299.99")
    print("6. Multi-Device Key - $499.99")

    try:
        choice = input("\nChọn loại key (1-6): ").strip()

        # Generate key based on choice
        if choice == "1":
            key_data = gen.generate_trial_key(7)
            key_type = "Trial 7 Days"
        elif choice == "2":
            key_data = gen.generate_trial_key(30)
            key_type = "Trial 30 Days"
        elif choice == "3":
            key_data = gen.generate_monthly_key(29.99)
            key_type = "Monthly License"
        elif choice == "4":
            key_data = gen.generate_quarterly_key(79.99)
            key_type = "Quarterly License"
        elif choice == "5":
            key_data = gen.generate_lifetime_key(299.99)
            key_type = "Lifetime License"
        elif choice == "6":
            devices = input("Số devices (mặc định 6): ").strip() or "6"
            key_data = gen.generate_multi_device_key(int(devices), 365, 499.99)
            key_type = f"Multi-Device ({devices} devices)"
        else:
            print("❌ Lựa chọn không hợp lệ!")
            return

        # Show generated key
        print(f"\n✅ KEY ĐÃ TẠO THÀNH CÔNG:")
        print("=" * 40)
        print(f"🔑 License Key: {key_data['key']}")
        print(f"📝 Loại: {key_type}")
        print(f"💰 Giá: ${key_data['price']:.2f}")
        print(f"⏱️ Thời hạn: {key_data['duration_days']} ngày")
        print(f"📱 Max devices: {key_data['max_devices']}")
        print(f"📅 Hết hạn: {key_data['expiry_date'][:10]}")

        # Get customer info
        print(f"\n👤 THÔNG TIN CUSTOMER:")
        print("-" * 30)

        customer_email = input("Email customer: ").strip()
        if not customer_email:
            print("❌ Cần nhập email customer!")
            return

        customer_name = input("Tên customer (tùy chọn): ").strip()
        if not customer_name:
            customer_name = "Valued Customer"

        # Create customer record
        print(f"\n📝 ĐANG TẠO CUSTOMER RECORD...")
        customer = gen.create_customer_record(customer_email, customer_name)
        print(f"✅ Customer đã tạo: {customer['email']}")

        # Assign key to customer
        print(f"\n🔗 ĐANG GÁN KEY CHO CUSTOMER...")
        assignment = gen.assign_key_to_customer(key_data['key'], customer_email)
        if assignment:
            print(f"✅ Key đã gán thành công cho {customer_email}")
        else:
            print(f"❌ Lỗi gán key!")
            return

        # Check email configuration
        print(f"\n📧 KIỂM TRA CẤU HÌNH EMAIL...")
        if gen.admin_email and gen.admin_password:
            print(f"✅ Email đã cấu hình: {gen.admin_email}")

            # Ask to send email
            send_choice = input(f"\nGửi email cho {customer_email}? (y/n): ").strip().lower()

            if send_choice == 'y':
                print(f"\n📤 ĐANG GỬI EMAIL...")
                try:
                    result = gen.send_key_email(key_data['key'], customer_email, customer_name)
                    if result:
                        print(f"✅ EMAIL ĐÃ GỬI THÀNH CÔNG!")
                        print(f"📧 Địa chỉ: {customer_email}")
                        print(f"🔑 Key: {key_data['key']}")
                        print(f"📝 Loại: {key_type}")
                    else:
                        print(f"❌ GỬI EMAIL THẤT BẠI!")
                        show_manual_send_info(key_data['key'], customer_email, key_type)
                except Exception as e:
                    print(f"❌ LỖI GỬI EMAIL: {e}")
                    show_manual_send_info(key_data['key'], customer_email, key_type)
            else:
                show_manual_send_info(key_data['key'], customer_email, key_type)

        else:
            print(f"⚠️ Email chưa được cấu hình!")
            print(f"💡 Để gửi email tự động:")
            print(f"   1. Chạy: python admin_license_gui.py")
            print(f"   2. Vào tab Settings")
            print(f"   3. Nhập Gmail và app password")
            print(f"   4. Save configuration")

            show_manual_send_info(key_data['key'], customer_email, key_type)

        # Show final summary
        print(f"\n📊 TÓM TẮT:")
        print("=" * 40)
        print(f"✅ Key đã tạo: {key_data['key']}")
        print(f"✅ Customer: {customer_email}")
        print(f"✅ Database đã cập nhật")

        # Show statistics
        stats = gen.get_statistics()
        print(f"\n📈 THỐNG KÊ CẬP NHẬT:")
        print("-" * 25)
        print(f"Tổng keys: {stats.get('total_keys', 0)}")
        print(f"Keys đang hoạt động: {stats.get('active_keys', 0)}")
        print(f"Tổng doanh thu: ${stats.get('total_revenue', 0):.2f}")
        print(f"Tổng customers: {stats.get('total_customers', 0)}")

    except KeyboardInterrupt:
        print(f"\n\n❌ Đã hủy bởi user")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")

def show_manual_send_info(license_key, customer_email, key_type):
    """Show manual sending information"""
    print(f"\n📝 THÔNG TIN GỬI THỦ CÔNG:")
    print("=" * 40)
    print(f"Email customer: {customer_email}")
    print(f"License key: {license_key}")
    print(f"Loại key: {key_type}")

    print(f"\n📧 NỘI DUNG EMAIL MẪU:")
    print("-" * 30)

    email_template = f"""
Subject: ClausoNet 4.0 Pro - Your {key_type} License Key

Dear Customer,

Thank you for choosing ClausoNet 4.0 Pro!

🔑 YOUR LICENSE KEY: {license_key}

🚀 ACTIVATION STEPS:
1. Download ClausoNet 4.0 Pro
2. Launch the application
3. Go to Settings → License
4. Enter key: {license_key}
5. Click "Activate License"

Best regards,
ClausoNet Team
"""

    print(email_template)

    # Try to copy to clipboard
    try:
        import pyperclip
        copy_choice = input("Copy key to clipboard? (y/n): ").strip().lower()
        if copy_choice == 'y':
            pyperclip.copy(license_key)
            print("✅ Key đã copy vào clipboard!")
    except ImportError:
        print("💡 Install pyperclip để copy tự động: pip install pyperclip")

if __name__ == "__main__":
    print("🎯 STARTING CREATE & SEND KEY DEMO")
    print("=" * 60)

    demo_create_and_send_key()

    print(f"\n{'='*60}")
    print("🎉 DEMO HOÀN THÀNH!")
    print("💡 Để gửi email tự động, setup Gmail trong Admin GUI")
    print("💡 Chạy: python admin_license_gui.py")
    print("="*60)
