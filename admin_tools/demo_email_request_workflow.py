#!/usr/bin/env python3
"""
Demo Email Request Workflow - Test hoàn chỉnh workflow nhận email và tự động tạo key
"""

from email_request_handler import EmailRequestHandler
from license_key_generator import LicenseKeyGenerator
import json
import time

def demo_email_request_workflow():
    print("🚀 CLAUSONET 4.0 PRO - EMAIL REQUEST WORKFLOW DEMO")
    print("=" * 70)

    # Initialize handlers
    print("🔧 INITIALIZING COMPONENTS...")
    handler = EmailRequestHandler()
    gen = LicenseKeyGenerator()

    print("✅ Email Request Handler: Ready")
    print("✅ License Key Generator: Ready")

    # Demo: Simulate incoming email requests
    print(f"\n📧 SIMULATING CUSTOMER EMAIL REQUESTS:")
    print("-" * 50)

    # Simulate different types of email requests
    demo_requests = [
        {
            'email_id': 'demo_001',
            'sender_email': 'customer1@example.com',
            'sender_name': 'John Smith',
            'subject': 'Request ClausoNet Trial License',
            'body': 'Hi, I would like to try ClausoNet 4.0 Pro for my video projects. Can I get a trial license?',
            'license_type': 'trial',
            'phone': '+84123456789',
            'company': None,
            'received_at': '2025-09-07T15:30:00'
        },
        {
            'email_id': 'demo_002',
            'sender_email': 'business@techcorp.com',
            'sender_name': 'Sarah Johnson',
            'subject': 'ClausoNet Lifetime License Purchase',
            'body': 'Hello, our company needs a lifetime license for ClausoNet 4.0 Pro. We work on multiple video projects. Company: TechCorp Solutions, Phone: +84987654321',
            'license_type': 'lifetime',
            'phone': '+84987654321',
            'company': 'TechCorp Solutions',
            'received_at': '2025-09-07T16:15:00'
        },
        {
            'email_id': 'demo_003',
            'sender_email': 'freelancer@creative.com',
            'sender_name': 'Mike Chen',
            'subject': 'Monthly ClausoNet License',
            'body': 'I am a freelance video creator and need a monthly subscription to ClausoNet 4.0 Pro.',
            'license_type': 'monthly',
            'phone': None,
            'company': 'Freelance Creative',
            'received_at': '2025-09-07T17:00:00'
        }
    ]

    # Process each demo request
    processed_successfully = 0
    total_revenue = 0

    for i, request in enumerate(demo_requests, 1):
        print(f"\n📨 PROCESSING REQUEST {i}/3:")
        print(f"   From: {request['sender_email']} ({request['sender_name']})")
        print(f"   Subject: {request['subject']}")
        print(f"   Type: {request['license_type'].title()}")

        # Process the request
        try:
            success = handler.process_license_request(request)

            if success:
                print(f"   ✅ Status: Successfully processed")
                processed_successfully += 1

                # Calculate revenue
                if request['license_type'] == 'trial':
                    revenue = 0
                elif request['license_type'] == 'monthly':
                    revenue = 29.99
                elif request['license_type'] == 'lifetime':
                    revenue = 299.99
                else:
                    revenue = 0

                total_revenue += revenue
                print(f"   💰 Revenue: ${revenue:.2f}")

                # Get customer info to show key
                customer_info = gen.get_customer_info(request['sender_email'])
                if customer_info and customer_info['keys_purchased']:
                    latest_key = customer_info['keys_purchased'][-1]
                    print(f"   🔑 Key Generated: {latest_key}")

            else:
                print(f"   ❌ Status: Processing failed")

        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Simulate processing delay
        time.sleep(1)

    # Show final results
    print(f"\n🎯 WORKFLOW DEMO RESULTS:")
    print("=" * 50)
    print(f"📊 Total Requests: {len(demo_requests)}")
    print(f"✅ Successfully Processed: {processed_successfully}")
    print(f"❌ Failed: {len(demo_requests) - processed_successfully}")
    print(f"📈 Success Rate: {processed_successfully/len(demo_requests)*100:.1f}%")
    print(f"💰 Total Revenue Generated: ${total_revenue:.2f}")

    # Show updated statistics
    print(f"\n📈 UPDATED SYSTEM STATISTICS:")
    print("-" * 40)
    stats = gen.get_statistics()
    print(f"Total Customers: {stats['total_customers']}")
    print(f"Total Keys: {stats['total_keys']}")
    print(f"Active Keys: {stats['active_keys']}")
    print(f"Total Revenue: ${stats['total_revenue']:.2f}")

    # Show customer details
    print(f"\n👥 NEW CUSTOMERS CREATED:")
    print("-" * 40)
    for request in demo_requests:
        customer_info = gen.get_customer_info(request['sender_email'])
        if customer_info:
            print(f"📧 {customer_info['email']}")
            print(f"   Name: {customer_info['name']}")
            print(f"   Keys: {len(customer_info['keys_purchased'])}")
            print(f"   Spent: ${customer_info['total_spent']:.2f}")
            if customer_info.get('phone'):
                print(f"   Phone: {customer_info['phone']}")
            if customer_info.get('company'):
                print(f"   Company: {customer_info['company']}")
            print()

    return True

def demo_email_detection_logic():
    """Demo automatic license type detection"""
    print(f"\n🔍 EMAIL CONTENT DETECTION DEMO:")
    print("=" * 50)

    handler = EmailRequestHandler()

    # Test different email contents
    test_cases = [
        ("I want to try ClausoNet for my projects", "trial"),
        ("Can I get a test license?", "trial"),
        ("Need a lifetime license for business", "lifetime"),
        ("Monthly subscription please", "monthly"),
        ("Quarterly license for our team", "quarterly"),
        ("Multi-device license for 5 computers", "multi_device"),
        ("ClausoNet license request", "trial")
    ]

    print("📝 DETECTION EXAMPLES:")
    for i, (content, expected) in enumerate(test_cases, 1):

        detected = handler.detect_license_type(content)
        status = "✅" if detected == expected else "❌"

        print(f"{i}. '{content[:40]}...'")
        print(f"   Expected: {expected}")
        print(f"   Detected: {detected} {status}")
        print()

def demo_customer_info_extraction():
    """Demo customer information extraction"""
    print(f"\n👤 CUSTOMER INFO EXTRACTION DEMO:")
    print("=" * 50)

    handler = EmailRequestHandler()

    # Test email content with customer info
    test_content = """
    Hi ClausoNet team,

    I'm interested in getting a lifetime license for ClausoNet 4.0 Pro.

    My details:
    Company: Creative Media Solutions
    Phone: +84-912-345-678

    Looking forward to using your software!

    Best regards,
    John Smith
    Creative Director
    """

    print("📧 TEST EMAIL CONTENT:")
    print(test_content)

    # Extract information
    phone = handler.extract_phone(test_content)
    company = handler.extract_company(test_content)
    license_type = handler.detect_license_type(test_content)

    print(f"\n🔍 EXTRACTED INFORMATION:")
    print(f"📞 Phone: {phone}")
    print(f"🏢 Company: {company}")
    print(f"🔑 License Type: {license_type}")

    return True

if __name__ == "__main__":
    print("🎯 STARTING EMAIL REQUEST WORKFLOW DEMO")
    print("=" * 70)

    try:
        # Run main demo
        success = demo_email_request_workflow()

        if success:
            # Run additional demos
            demo_email_detection_logic()
            demo_customer_info_extraction()

            print(f"\n{'='*70}")
            print(f"🎉 EMAIL REQUEST WORKFLOW DEMO COMPLETED!")
            print(f"{'='*70}")

            print(f"\n📧 EMAIL REQUEST SYSTEM FEATURES:")
            print(f"✅ Automatic email monitoring")
            print(f"✅ Smart license type detection")
            print(f"✅ Customer info extraction")
            print(f"✅ Auto key generation")
            print(f"✅ Professional email responses")
            print(f"✅ Database integration")
            print(f"✅ Revenue tracking")

            print(f"\n🔧 TO USE IN PRODUCTION:")
            print(f"1. Configure email credentials in Admin GUI")
            print(f"2. Enable IMAP access in email account")
            print(f"3. Start auto email processing")
            print(f"4. System will handle all customer requests automatically")

            print(f"\n📈 BUSINESS BENEFITS:")
            print(f"• 24/7 automated customer service")
            print(f"• Instant license delivery")
            print(f"• Zero manual intervention needed")
            print(f"• Professional customer experience")
            print(f"• Complete sales tracking")

        else:
            print(f"❌ Demo failed")

    except KeyboardInterrupt:
        print(f"\n\n❌ Demo cancelled by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
