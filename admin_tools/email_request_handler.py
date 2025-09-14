#!/usr/bin/env python3
"""
Email Request Handler - Xử lý email request từ customers để tạo key
Tự động đọc email inbox và tạo key gửi trực tiếp
"""

import imaplib
import email
from email.header import decode_header
import re
import json
from datetime import datetime
from license_key_generator import LicenseKeyGenerator

class EmailRequestHandler:
    def __init__(self):
        self.gen = LicenseKeyGenerator()
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993
        self.processed_emails = self.load_processed_emails()

    def load_processed_emails(self):
        """Load đã xử lý email IDs để tránh duplicate"""
        try:
            with open('processed_emails.json', 'r') as f:
                return set(json.load(f))
        except:
            return set()

    def save_processed_emails(self):
        """Save processed email IDs"""
        with open('processed_emails.json', 'w') as f:
            json.dump(list(self.processed_emails), f)

    def connect_to_email(self, email_address, password):
        """Connect to email inbox"""
        try:
            print(f"📧 Connecting to {email_address}...")

            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(email_address, password)
            mail.select('INBOX')

            print(f"✅ Connected successfully!")
            return mail

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return None

    def check_for_license_requests(self, mail):
        """Check inbox cho license requests"""
        try:
            # Search for unread emails về license
            search_criteria = '(UNSEEN SUBJECT "license")'
            result, messages = mail.search(None, search_criteria)

            if result != 'OK':
                return []

            email_ids = messages[0].split()
            print(f"📬 Found {len(email_ids)} new license requests")

            requests = []

            for email_id in email_ids:
                email_id = email_id.decode()

                # Skip nếu đã processed
                if email_id in self.processed_emails:
                    continue

                # Fetch email
                result, msg_data = mail.fetch(email_id, '(RFC822)')
                if result != 'OK':
                    continue

                # Parse email
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)

                # Extract info
                request_info = self.parse_license_request(email_message, email_id)
                if request_info:
                    requests.append(request_info)
                    self.processed_emails.add(email_id)

            self.save_processed_emails()
            return requests

        except Exception as e:
            print(f"❌ Error checking emails: {e}")
            return []

    def parse_license_request(self, email_message, email_id):
        """Parse email để extract license request info"""
        try:
            # Get sender info
            from_header = email_message.get('From', '')
            sender_email = re.findall(r'[\w\.-]+@[\w\.-]+', from_header)
            if not sender_email:
                return None
            sender_email = sender_email[0].lower()

            # Get sender name
            sender_name = from_header.split('<')[0].strip(' "')
            if not sender_name or '@' in sender_name:
                sender_name = sender_email.split('@')[0].title()

            # Get subject
            subject = email_message.get('Subject', '')
            if isinstance(subject, str):
                subject = subject
            else:
                subject, encoding = decode_header(subject)[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or 'utf-8')

            # Get email body
            body = self.get_email_body(email_message)

            # Determine license type from email content
            license_type = self.detect_license_type(subject + ' ' + body)

            # Extract additional info
            phone = self.extract_phone(body)
            company = self.extract_company(body)

            request_info = {
                'email_id': email_id,
                'sender_email': sender_email,
                'sender_name': sender_name,
                'subject': subject,
                'body': body[:500],  # First 500 chars
                'license_type': license_type,
                'phone': phone,
                'company': company,
                'received_at': datetime.now().isoformat()
            }

            print(f"📨 Request from {sender_email}: {license_type}")
            return request_info

        except Exception as e:
            print(f"❌ Error parsing email: {e}")
            return None

    def get_email_body(self, email_message):
        """Extract email body text"""
        body = ""

        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    charset = part.get_content_charset() or 'utf-8'
                    body = part.get_payload(decode=True).decode(charset, errors='ignore')
                    break
        else:
            charset = email_message.get_content_charset() or 'utf-8'
            body = email_message.get_payload(decode=True).decode(charset, errors='ignore')

        return body

    def detect_license_type(self, content):
        """Detect license type từ email content"""
        content_lower = content.lower()

        # Keywords cho từng loại license
        if any(word in content_lower for word in ['trial', 'test', 'try', 'demo', 'thử']):
            return 'trial'
        elif any(word in content_lower for word in ['lifetime', 'permanent', 'vĩnh viễn', 'mãi mãi']):
            return 'lifetime'
        elif any(word in content_lower for word in ['monthly', 'month', 'tháng']):
            return 'monthly'
        elif any(word in content_lower for word in ['quarterly', 'quarter', 'quý']):
            return 'quarterly'
        elif any(word in content_lower for word in ['multi', 'multiple', 'nhiều thiết bị']):
            return 'multi_device'
        else:
            return 'trial'  # Default to trial

    def extract_phone(self, text):
        """Extract phone number từ email"""
        phone_patterns = [
            r'\+?84[\s-]?\d{9,10}',  # Vietnam numbers
            r'\+?\d{1,3}[\s-]?\d{10,12}',  # International
            r'\d{10,11}'  # Simple numbers
        ]

        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        return None

    def extract_company(self, text):
        """Extract company name từ email"""
        # Look for common company patterns
        company_patterns = [
            r'Company[:\s]+([^\n]+)',
            r'Công ty[:\s]+([^\n]+)',
            r'from\s+([A-Z][A-Za-z\s]+(?:Corp|Inc|Ltd|Co\.|Company))',
        ]

        for pattern in company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def process_license_request(self, request_info):
        """Process license request và tạo key"""
        try:
            print(f"\n🔄 Processing request from {request_info['sender_email']}")

            # Create customer record
            customer_data = {
                'email': request_info['sender_email'],
                'name': request_info['sender_name']
            }
            if request_info['phone']:
                customer_data['phone'] = request_info['phone']
            if request_info['company']:
                customer_data['company'] = request_info['company']

            customer_record = self.gen.create_customer_record(**customer_data)
            print(f"✅ Customer created: {customer_record['email']}")

            # Generate appropriate license key
            license_type = request_info['license_type']

            if license_type == 'trial':
                key_data = self.gen.generate_trial_key(30)  # 30-day trial
                print(f"✅ Generated 30-day trial key")
            elif license_type == 'monthly':
                key_data = self.gen.generate_monthly_key(29.99)
                print(f"✅ Generated monthly key ($29.99)")
            elif license_type == 'quarterly':
                key_data = self.gen.generate_quarterly_key(79.99)
                print(f"✅ Generated quarterly key ($79.99)")
            elif license_type == 'lifetime':
                key_data = self.gen.generate_lifetime_key(299.99)
                print(f"✅ Generated lifetime key ($299.99)")
            elif license_type == 'multi_device':
                key_data = self.gen.generate_multi_device_key(499.99, 6)
                print(f"✅ Generated multi-device key ($499.99)")
            else:
                key_data = self.gen.generate_trial_key(7)  # Default 7-day trial
                print(f"✅ Generated default 7-day trial key")

            # Assign key to customer
            assignment_success = self.gen.assign_key_to_customer(
                key_data['key'],
                request_info['sender_email']
            )

            if not assignment_success:
                print(f"❌ Failed to assign key")
                return False

            print(f"✅ Key assigned: {key_data['key']}")

            # Send license email
            email_sent = self.gen.send_key_email(
                request_info['sender_email'],
                key_data['key'],
                key_data['type']
            )

            if email_sent:
                print(f"✅ License email sent successfully!")

                # Log successful processing
                self.log_processed_request(request_info, key_data)
                return True
            else:
                print(f"❌ Failed to send email")
                return False

        except Exception as e:
            print(f"❌ Error processing request: {e}")
            return False

    def log_processed_request(self, request_info, key_data):
        """Log processed request for tracking"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'email_id': request_info['email_id'],
            'customer_email': request_info['sender_email'],
            'customer_name': request_info['sender_name'],
            'license_key': key_data['key'],
            'license_type': key_data['type'],
            'price': key_data['price'],
            'subject': request_info['subject']
        }

        # Save to log file
        try:
            with open('processed_requests.json', 'r') as f:
                logs = json.load(f)
        except:
            logs = []

        logs.append(log_entry)

        with open('processed_requests.json', 'w') as f:
            json.dump(logs, f, indent=2)

    def auto_process_emails(self, email_address, password):
        """Tự động xử lý tất cả email requests"""
        print(f"🚀 STARTING AUTO EMAIL PROCESSING")
        print(f"=" * 50)

        # Connect to email
        mail = self.connect_to_email(email_address, password)
        if not mail:
            return False

        try:
            # Check for requests
            requests = self.check_for_license_requests(mail)

            if not requests:
                print(f"📭 No new license requests found")
                return True

            print(f"📬 Processing {len(requests)} requests...")

            successful = 0
            failed = 0

            for request in requests:
                print(f"\n" + "="*40)
                success = self.process_license_request(request)

                if success:
                    successful += 1
                else:
                    failed += 1

            print(f"\n🎯 PROCESSING SUMMARY:")
            print(f"✅ Successful: {successful}")
            print(f"❌ Failed: {failed}")
            print(f"📊 Success Rate: {successful/(successful+failed)*100:.1f}%")

            return True

        except Exception as e:
            print(f"❌ Auto processing error: {e}")
            return False

        finally:
            try:
                mail.close()
                mail.logout()
            except:
                pass

def demo_email_request_handler():
    """Demo email request handling"""
    print(f"📧 EMAIL REQUEST HANDLER DEMO")
    print(f"=" * 50)

    handler = EmailRequestHandler()

    print(f"📋 EMAIL REQUEST PROCESSING FEATURES:")
    print(f"✅ Auto-detect license type từ email content")
    print(f"✅ Extract customer info (name, phone, company)")
    print(f"✅ Generate appropriate license key")
    print(f"✅ Create customer record tự động")
    print(f"✅ Send license email trực tiếp")
    print(f"✅ Log processed requests")
    print(f"✅ Avoid duplicate processing")

    print(f"\n🔍 SUPPORTED LICENSE TYPE DETECTION:")
    print(f"• 'trial', 'test', 'thử' → Trial Key (30 days)")
    print(f"• 'lifetime', 'vĩnh viễn' → Lifetime Key ($299.99)")
    print(f"• 'monthly', 'tháng' → Monthly Key ($29.99)")
    print(f"• 'quarterly', 'quý' → Quarterly Key ($79.99)")
    print(f"• 'multi', 'nhiều thiết bị' → Multi-Device Key ($499.99)")

    print(f"\n📧 EMAIL PATTERNS DETECTED:")
    print(f"• Subject: Request ClausoNet license")
    print(f"• Body: Tôi muốn thử ClausoNet 4.0 Pro")
    print(f"• Auto-extract: Phone, Company name")
    print(f"• Response: Professional license email")

    print(f"\n🔧 SETUP REQUIRED:")
    print(f"1. Configure email credentials trong admin GUI")
    print(f"2. Enable IMAP access for your email")
    print(f"3. Run email processor: handler.auto_process_emails()")

    print(f"\n📊 WORKFLOW:")
    print(f"Customer → Email request → Auto-detect type → Generate key → Send license")

    return True

if __name__ == "__main__":
    print("🎯 CLAUSONET 4.0 PRO - EMAIL REQUEST HANDLER")
    print("=" * 60)

    demo_email_request_handler()

    print(f"\n" + "="*60)
    print(f"📧 EMAIL REQUEST HANDLER: READY")
    print(f"✅ Customers có thể gửi email request")
    print(f"✅ System tự động tạo và gửi license key")
    print(f"✅ No manual intervention needed")
    print(f"=" * 60)
