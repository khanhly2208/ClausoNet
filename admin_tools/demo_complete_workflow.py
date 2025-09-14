#!/usr/bin/env python3
"""
Demo hoàn chỉnh: Tạo và gửi license key qua email
"""

from license_key_generator import LicenseKeyGenerator
import sys
import json

def demo_complete_license_workflow():
    print("🎯 CLAUSONET 4.0 PRO - COMPLETE LICENSE WORKFLOW DEMO")
    print("=" * 70)

    gen = LicenseKeyGenerator()

    # Step 1: Show current configuration
    print("📋 CURRENT CONFIGURATION:")
    print("-" * 30)
    print(f"Admin Email: {gen.admin_email}")
    print(f"SMTP Server: {gen.smtp_server}:{gen.smtp_port}")
    print(f"License Database: {len(gen.licenses)} keys")
    print(f"Customer Database: {len(gen.customers)} customers")

    # Step 2: Demo key generation options
    print(f"\n🔑 LICENSE KEY OPTIONS:")
    print("-" * 30)
    print("1. Trial Key (7 days) - FREE")
    print("2. Trial Key (30 days) - FREE")
    print("3. Monthly Key - $29.99")
    print("4. Quarterly Key - $79.99")
    print("5. Lifetime Key - $299.99")
    print("6. Multi-Device Key - $499.99")

    # Get user choice
    try:
        choice = input("\nChọn loại key (1-6): ").strip()

        if choice == "1":
            # 7-day trial
            key_data = gen.generate_trial_key(7)
            key_type = "Trial 7 Days"
            price = 0
        elif choice == "2":
            # 30-day trial
            key_data = gen.generate_trial_key(30)
            key_type = "Trial 30 Days"
            price = 0
        elif choice == "3":
            # Monthly
            key_data = gen.generate_monthly_key(29.99)
            key_type = "Monthly"
            price = 29.99
        elif choice == "4":
            # Quarterly
            key_data = gen.generate_quarterly_key(79.99)
            key_type = "Quarterly"
            price = 79.99
        elif choice == "5":
            # Lifetime
            key_data = gen.generate_lifetime_key(299.99)
            key_type = "Lifetime"
            price = 299.99
        elif choice == "6":
            # Multi-device
            key_data = gen.generate_multi_device_key(499.99, 6)
            key_type = "Multi-Device"
            price = 499.99
        else:
            print("❌ Invalid choice!")
            return False

    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        return False

    # Step 3: Show generated key info
    print(f"\n✅ KEY GENERATED SUCCESSFULLY:")
    print("-" * 40)
    print(f"License Key: {key_data['key']}")
    print(f"Type: {key_type}")
    print(f"Price: ${price:.2f}")
    print(f"Duration: {key_data['duration_days']} days")
    print(f"Expires: {key_data['expiry_date'][:10]}")
    print(f"Max Devices: {key_data['max_devices']}")
    print(f"Features: {len(key_data['features'])} features")

    # Step 4: Get customer info
    print(f"\n👤 CUSTOMER INFORMATION:")
    print("-" * 30)

    customer_email = input("Customer Email: ").strip()
    if not customer_email:
        print("❌ Email required!")
        return False

    customer_name = input("Customer Name (optional): ").strip()
    if not customer_name:
        customer_name = "Valued Customer"

    customer_phone = input("Customer Phone (optional): ").strip()
    customer_company = input("Customer Company (optional): ").strip()

    # Step 5: Create customer record
    print(f"\n📝 CREATING CUSTOMER RECORD...")

    customer_data = {
        "email": customer_email,
        "name": customer_name
    }
    if customer_phone:
        customer_data["phone"] = customer_phone
    if customer_company:
        customer_data["company"] = customer_company

    customer_record = gen.create_customer_record(**customer_data)
    print(f"✅ Customer created: {customer_record['email']}")

    # Step 6: Assign key to customer
    print(f"\n🔗 ASSIGNING KEY TO CUSTOMER...")

    assignment_success = gen.assign_key_to_customer(key_data['key'], customer_email)
    if assignment_success:
        print(f"✅ Key assigned successfully!")
    else:
        print(f"❌ Key assignment failed!")
        return False

    # Step 7: Generate email content
    print(f"\n📧 GENERATING EMAIL CONTENT...")

    email_content = generate_license_email(key_data, customer_email, customer_name, key_type)
    print(f"✅ Email content generated:")
    print(f"   Subject: ClausoNet 4.0 Pro - Your {key_type} License Key")
    print(f"   Body length: {len(email_content)} characters")
    print(f"   Contains license key: {key_data['key'] in email_content}")

    # Step 8: Preview email
    print(f"\n👀 EMAIL PREVIEW:")
    print("-" * 50)
    preview_lines = email_content.split('\n')[:15]  # First 15 lines
    for line in preview_lines:
        print(f"   {line}")
    print(f"   ... [total {len(email_content.split('\\n'))} lines]")

    # Step 9: Ask about sending
    print(f"\n📤 EMAIL SENDING OPTIONS:")
    print("-" * 30)
    print("1. Send real email (requires SMTP config)")
    print("2. Save email to file")
    print("3. Show full email content")
    print("4. Skip email sending")

    try:
        email_choice = input("Choose option (1-4): ").strip()

        if email_choice == "1":
            # Real email sending
            if gen.admin_email and gen.admin_password:
                try:
                    send_result = gen.send_key_email(key_data['key'], customer_email)
                    if send_result:
                        print(f"✅ Email sent successfully to {customer_email}!")
                    else:
                        print(f"❌ Email sending failed!")
                except Exception as e:
                    print(f"❌ Email error: {e}")
            else:
                print(f"⚠️ SMTP not configured. Use admin GUI to setup email.")

        elif email_choice == "2":
            # Save to file
            filename = f"license_email_{key_data['key']}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"To: {customer_email}\n")
                f.write(f"Subject: ClausoNet 4.0 Pro - Your {key_type} License Key\n\n")
                f.write(email_content)
            print(f"✅ Email saved to: {filename}")

        elif email_choice == "3":
            # Show full content
            print(f"\n📧 FULL EMAIL CONTENT:")
            print("=" * 60)
            print(email_content)
            print("=" * 60)

        elif email_choice == "4":
            print(f"⏭️ Email sending skipped")
        else:
            print(f"❌ Invalid choice!")

    except KeyboardInterrupt:
        print(f"\n❌ Cancelled by user")

    # Step 10: Show final summary
    print(f"\n📊 WORKFLOW SUMMARY:")
    print("=" * 50)
    print(f"✅ License Key: {key_data['key']}")
    print(f"✅ Customer: {customer_email}")
    print(f"✅ License Type: {key_type}")
    print(f"✅ Price: ${price:.2f}")
    print(f"✅ Database Updated: Yes")
    print(f"✅ Email Generated: Yes")

    # Update statistics
    stats = gen.get_statistics()
    print(f"\n📈 UPDATED STATISTICS:")
    print("-" * 30)
    print(f"Total Keys: {stats['total_keys']}")
    print(f"Active Keys: {stats['active_keys']}")
    print(f"Total Revenue: ${stats['total_revenue']:.2f}")
    print(f"Total Customers: {stats['total_customers']}")

    return True

def generate_license_email(key_data, customer_email, customer_name, key_type):
    """Generate professional license email"""

    key = key_data['key']
    expiry = key_data['expiry_date'][:10]
    price = key_data['price']

    email_content = f"""Dear {customer_name},

🎉 Thank you for choosing ClausoNet 4.0 Pro - the premier AI video generation platform!

🔑 YOUR LICENSE KEY: {key}

🚀 QUICK ACTIVATION GUIDE:
1. Download ClausoNet 4.0 Pro from: https://clausonet.com/download
2. Launch the application
3. Navigate to Settings → License
4. Enter your license key: {key}
5. Click "Activate License"
6. Start creating amazing AI videos!

🎯 YOUR LICENSE DETAILS:
• License Type: {key_type}
• Valid Until: {expiry}
• Max Devices: {key_data['max_devices']}
• Price Paid: ${price:.2f}

✨ FEATURES INCLUDED:"""

    for feature in key_data['features']:
        feature_name = feature.replace('_', ' ').title()
        email_content += f"\n• {feature_name}"

    if key_data['type'] == 'trial':
        email_content += f"""

⏰ TRIAL PERIOD: {key_data['duration_days']} days
Your trial expires on {expiry}. Don't miss out - upgrade to a full license to continue using all features!

💰 UPGRADE OPTIONS:
• Monthly License: $29.99/month
• Quarterly License: $79.99/quarter
• Lifetime License: $299.99 (Best Value!)
• Multi-Device License: $499.99 (Up to 6 devices)
"""
    elif key_data['type'] == 'lifetime':
        email_content += f"""

🎉 CONGRATULATIONS!
You now have LIFETIME ACCESS to ClausoNet 4.0 Pro, including all future updates and new features!

🎁 BONUS BENEFITS:
• Priority Customer Support
• Early Access to New Features
• Exclusive Video Templates
• Advanced AI Models Access
"""

    email_content += f"""
📞 NEED HELP?
• Email Support: support@clausonet.com
• Live Chat: https://clausonet.com/support
• Video Tutorials: https://youtube.com/clausonet
• Documentation: https://docs.clausonet.com

📱 FOLLOW US:
• Twitter: @ClausoNet
• Facebook: ClausoNet Pro
• YouTube: ClausoNet Channel

Thank you for being part of the ClausoNet family!

Best regards,
The ClausoNet Team
https://clausonet.com

---
This email was sent to: {customer_email}
License Key: {key}
Generated: {key_data['created_at'][:19]}
Support ID: {key_data['key'][-4:]}
"""

    return email_content

if __name__ == "__main__":
    print("🎯 STARTING COMPLETE LICENSE WORKFLOW DEMO")
    print("=" * 70)

    try:
        success = demo_complete_license_workflow()

        if success:
            print(f"\n🎉 DEMO COMPLETED SUCCESSFULLY!")
            print(f"✅ License system is fully operational")
            print(f"✅ Ready for production use")
        else:
            print(f"\n❌ Demo incomplete")

        print(f"\n{'='*70}")
        print(f"📧 To setup email sending:")
        print(f"   1. Run: python admin_license_gui.py")
        print(f"   2. Go to Settings tab")
        print(f"   3. Enter Gmail/Outlook credentials")
        print(f"   4. Test email sending")
        print(f"{'='*70}")

    except KeyboardInterrupt:
        print(f"\n\n❌ Demo cancelled by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
