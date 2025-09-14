#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Admin License Key Generator
Tool for admins to generate and manage license keys
"""

import hashlib
import json
import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging

class LicenseKeyGenerator:
    def __init__(self):
        # Use ResourceManager for proper path handling in exe
        try:
            # Try to import resource manager for proper path handling
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from utils.resource_manager import ResourceManager

            self.resource_manager = ResourceManager()
            self.admin_data_path = str(self.resource_manager.user_data_dir / "admin_data")
            self.license_database_path = str(self.resource_manager.user_data_dir / "admin_data" / "license_database.json")

        except ImportError:
            # Fallback to old method if ResourceManager not available
            current_dir = os.path.dirname(os.path.abspath(__file__))  # admin_tools directory
            project_root = os.path.dirname(current_dir)  # ClausoNet4.0 directory
            self.admin_data_path = os.path.join(project_root, "admin_data")
            self.license_database_path = os.path.join(self.admin_data_path, "license_database.json")
            self.resource_manager = None

        # Updated key formats to match main system expectation: CNPRO-XXXX-XXXX-XXXX-XXXX
        # We'll use the 5th segment to encode the type
        self.key_formats = {
            'trial': 'CNPRO-{}-{}-{}-T{}',      # T for Trial
            'monthly': 'CNPRO-{}-{}-{}-M{}',    # M for Monthly
            'quarterly': 'CNPRO-{}-{}-{}-Q{}',  # Q for Quarterly
            'lifetime': 'CNPRO-{}-{}-{}-L{}',   # L for Lifetime
            'multi_device': 'CNPRO-{}-{}-{}-D{}'  # D for Multi-Device
        }

        # Email configuration
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.admin_email = "admin@clausonet.com"
        self.admin_password = "your_admin_password"  # Change this

        self.setup_admin_directory()
        self.setup_logging()
        self.load_license_database()

    def setup_admin_directory(self):
        """Tạo thư mục admin và database"""
        os.makedirs(self.admin_data_path, exist_ok=True)
        if not os.path.exists(self.license_database_path):
            self.logger.info("Creating initial database for production...")
            self.create_initial_database()
            # PRODUCTION: No sample license keys created
            # self.create_sample_license_for_testing()  # Disabled for production

    def setup_logging(self):
        """Setup logging"""
        # Ensure logs directory exists
        logs_dir = os.path.dirname(self.admin_data_path)
        if self.resource_manager:
            logs_dir = str(self.resource_manager.user_data_dir / "logs")
        else:
            logs_dir = os.path.join(os.path.dirname(self.admin_data_path), "logs")

        os.makedirs(logs_dir, exist_ok=True)

        log_file = os.path.join(self.admin_data_path, 'license_admin.log')

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('LicenseAdmin')

    def create_initial_database(self):
        """Tạo database ban đầu"""
        initial_db = {
            'keys': [],
            'customers': [],
            'statistics': {
                'total_keys_generated': 0,
                'trial_keys': 0,
                'monthly_keys': 0,
                'quarterly_keys': 0,
                'lifetime_keys': 0,
                'multi_device_keys': 0,
                'keys_activated': 0,
                'revenue_tracked': 0.0
            },
            'created_at': datetime.utcnow().isoformat(),
            'version': '1.0'
        }

        with open(self.license_database_path, 'w', encoding='utf-8') as f:
            json.dump(initial_db, f, indent=2, ensure_ascii=False)

    def load_license_database(self):
        """Load license database with enhanced error handling and fallback"""
        try:
            # Try local database first
            if not os.path.exists(self.license_database_path):
                self.logger.info(f"Local database not found at {self.license_database_path}")

                # Try to find database in common locations
                possible_paths = [
                    self.license_database_path,  # Current path
                    os.path.join(os.path.dirname(self.license_database_path), "license_database.json"),
                    os.path.join(os.path.expanduser("~"), "AppData", "Local", "ClausoNet4.0", "admin_data", "license_database.json"),
                    os.path.join(os.path.expanduser("~"), "Documents", "ClausoNet4.0", "license_database.json"),
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "license_database.json"),
                ]

                database_found = False
                for path in possible_paths:
                    if os.path.exists(path):
                        self.logger.info(f"Found database at: {path}")
                        self.license_database_path = path
                        database_found = True
                        break

                if not database_found:
                    self.logger.info(f"No existing database found. Creating new database...")
                    self.create_initial_database()

            with open(self.license_database_path, 'r', encoding='utf-8') as f:
                self.database = json.load(f)

            # Validate database structure
            if not isinstance(self.database.get('keys'), list):
                self.logger.warning("Invalid database structure detected. Recreating database...")
                self.create_initial_database()
                self.load_license_database()
                return

            self.logger.info(f"Database loaded successfully. Found {len(self.database['keys'])} license keys.")

        except Exception as e:
            self.logger.error(f"Failed to load database: {e}")
            self.logger.info("Creating new database...")
            self.create_initial_database()
            self.load_license_database()

    def save_database(self):
        """Save database"""
        try:
            with open(self.license_database_path, 'w', encoding='utf-8') as f:
                json.dump(self.database, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save database: {e}")

    def generate_key_segment(self) -> str:
        """Generate a 4-character key segment (to match CNPRO-XXXX-XXXX-XXXX-XXXX format)"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=4))

    def generate_trial_key(self, days: int = 7) -> Dict[str, Any]:
        """🔍 Generate trial key (7 days default) - Compatible with CNPRO format"""
        segments = [self.generate_key_segment() for _ in range(4)]
        key = f"CNPRO-{segments[0]}-{segments[1]}-{segments[2]}-{segments[3]}"

        key_data = {
            'key': key,
            'type': 'trial',
            'license_format': 'CNPRO',  # Added for compatibility tracking
            'admin_type': 'trial',      # Internal admin tracking
            'duration_days': days,
            'max_devices': 1,
            'features': ['basic_generation', 'limited_workflows'],
            'expiry_date': (datetime.utcnow() + timedelta(days=days)).isoformat(),
            'created_at': datetime.utcnow().isoformat(),
            'status': 'generated',
            'activation_count': 0,
            'hardware_ids': [],
            'customer_info': None,
            'price': 0.0,
            'currency': 'USD'
        }

        self.database['keys'].append(key_data)
        self.database['statistics']['trial_keys'] += 1
        self.database['statistics']['total_keys_generated'] += 1
        self.save_database()

        self.logger.info(f"Generated trial key: {key} (valid for {days} days)")
        return key_data

    def generate_monthly_key(self, months: int = 1, price: float = 29.99) -> Dict[str, Any]:
        """📅 Generate monthly subscription key - Compatible with CNPRO format"""
        segments = [self.generate_key_segment() for _ in range(4)]
        key = f"CNPRO-{segments[0]}-{segments[1]}-{segments[2]}-{segments[3]}"

        key_data = {
            'key': key,
            'type': 'monthly',
            'license_format': 'CNPRO',  # Added for compatibility tracking
            'admin_type': 'monthly',    # Internal admin tracking
            'duration_days': months * 30,
            'max_devices': 1,
            'features': ['ai_generation', 'unlimited_workflows', 'api_access', 'priority_support'],
            'expiry_date': (datetime.utcnow() + timedelta(days=months * 30)).isoformat(),
            'created_at': datetime.utcnow().isoformat(),
            'status': 'generated',
            'activation_count': 0,
            'hardware_ids': [],
            'customer_info': None,
            'price': price * months,
            'currency': 'USD',
            'renewal_eligible': True
        }

        self.database['keys'].append(key_data)
        self.database['statistics']['monthly_keys'] += 1
        self.database['statistics']['total_keys_generated'] += 1
        self.database['statistics']['revenue_tracked'] += key_data['price']
        self.save_database()

        self.logger.info(f"Generated monthly key: {key} (valid for {months} months, ${price * months})")
        return key_data

    def generate_quarterly_key(self, quarters: int = 1, price: float = 79.99) -> Dict[str, Any]:
        """📅 Generate quarterly subscription key (3 months) - Compatible with CNPRO format"""
        segments = [self.generate_key_segment() for _ in range(4)]
        key = f"CNPRO-{segments[0]}-{segments[1]}-{segments[2]}-{segments[3]}"

        key_data = {
            'key': key,
            'type': 'quarterly',
            'duration_days': quarters * 90,
            'max_devices': 2,
            'features': ['ai_generation', 'unlimited_workflows', 'api_access', 'priority_support', 'batch_processing'],
            'expiry_date': (datetime.utcnow() + timedelta(days=quarters * 90)).isoformat(),
            'created_at': datetime.utcnow().isoformat(),
            'status': 'generated',
            'activation_count': 0,
            'hardware_ids': [],
            'customer_info': None,
            'price': price * quarters,
            'currency': 'USD',
            'renewal_eligible': True
        }

        self.database['keys'].append(key_data)
        self.database['statistics']['quarterly_keys'] += 1
        self.database['statistics']['total_keys_generated'] += 1
        self.database['statistics']['revenue_tracked'] += key_data['price']
        self.save_database()

        self.logger.info(f"Generated quarterly key: {key} (valid for {quarters * 3} months, ${price * quarters})")
        return key_data

    def generate_lifetime_key(self, price: float = 299.99) -> Dict[str, Any]:
        """🎯 Generate lifetime license key - Compatible with CNPRO format"""
        segments = [self.generate_key_segment() for _ in range(4)]
        key = f"CNPRO-{segments[0]}-{segments[1]}-{segments[2]}-{segments[3]}"

        key_data = {
            'key': key,
            'type': 'lifetime',
            'duration_days': 36500,  # 100 years
            'max_devices': 1,
            'features': ['ai_generation', 'unlimited_workflows', 'api_access', 'priority_support', 'batch_processing', 'lifetime_updates'],
            'expiry_date': (datetime.utcnow() + timedelta(days=36500)).isoformat(),
            'created_at': datetime.utcnow().isoformat(),
            'status': 'generated',
            'activation_count': 0,
            'hardware_ids': [],
            'customer_info': None,
            'price': price,
            'currency': 'USD',
            'renewal_eligible': False
        }

        self.database['keys'].append(key_data)
        self.database['statistics']['lifetime_keys'] += 1
        self.database['statistics']['total_keys_generated'] += 1
        self.database['statistics']['revenue_tracked'] += key_data['price']
        self.save_database()

        self.logger.info(f"Generated lifetime key: {key} (${price})")
        return key_data

    def generate_multi_device_key(self, max_devices: int = 6, duration_days: int = 365, price: float = 499.99) -> Dict[str, Any]:
        """🖥️ Generate multi-device key (up to 6 devices) - Compatible with CNPRO format"""
        segments = [self.generate_key_segment() for _ in range(4)]
        key = f"CNPRO-{segments[0]}-{segments[1]}-{segments[2]}-{segments[3]}"

        key_data = {
            'key': key,
            'type': 'multi_device',
            'duration_days': duration_days,
            'max_devices': max_devices,
            'features': ['ai_generation', 'unlimited_workflows', 'api_access', 'priority_support', 'batch_processing', 'team_collaboration'],
            'expiry_date': (datetime.utcnow() + timedelta(days=duration_days)).isoformat(),
            'created_at': datetime.utcnow().isoformat(),
            'status': 'generated',
            'activation_count': 0,
            'hardware_ids': [],
            'customer_info': None,
            'price': price,
            'currency': 'USD',
            'renewal_eligible': True
        }

        self.database['keys'].append(key_data)
        self.database['statistics']['multi_device_keys'] += 1
        self.database['statistics']['total_keys_generated'] += 1
        self.database['statistics']['revenue_tracked'] += key_data['price']
        self.save_database()

        self.logger.info(f"Generated multi-device key: {key} (up to {max_devices} devices, {duration_days} days, ${price})")
        return key_data

    def create_customer_record(self, email: str, name: str = "", phone: str = "", company: str = "") -> Dict[str, Any]:
        """📝 Create customer record"""
        customer_data = {
            'id': str(uuid.uuid4()),
            'email': email.lower().strip(),
            'name': name.strip(),
            'phone': phone.strip(),
            'company': company.strip(),
            'created_at': datetime.utcnow().isoformat(),
            'keys_purchased': [],
            'total_spent': 0.0,
            'last_contact': None,
            'status': 'active'
        }

        # Check if customer already exists
        for customer in self.database['customers']:
            if customer['email'] == customer_data['email']:
                self.logger.info(f"Customer already exists: {email}")
                return customer

        self.database['customers'].append(customer_data)
        self.save_database()

        self.logger.info(f"Created customer record: {email}")
        return customer_data

    def assign_key_to_customer(self, key: str, customer_email: str) -> bool:
        """🔗 Assign key to customer"""
        # Find key
        key_data = None
        for k in self.database['keys']:
            if k['key'] == key:
                key_data = k
                break

        if not key_data:
            self.logger.error(f"Key not found: {key}")
            return False

        # Find customer
        customer_data = None
        for c in self.database['customers']:
            if c['email'] == customer_email.lower().strip():
                customer_data = c
                break

        if not customer_data:
            self.logger.error(f"Customer not found: {customer_email}")
            return False

        # Assign key
        key_data['customer_info'] = {
            'customer_id': customer_data['id'],
            'email': customer_data['email'],
            'name': customer_data['name'],
            'assigned_at': datetime.utcnow().isoformat()
        }

        customer_data['keys_purchased'].append({
            'key': key,
            'type': key_data['type'],
            'price': key_data['price'],
            'purchased_at': datetime.utcnow().isoformat()
        })

        customer_data['total_spent'] += key_data['price']
        customer_data['last_contact'] = datetime.utcnow().isoformat()

        self.save_database()
        self.logger.info(f"Assigned key {key} to customer {customer_email}")
        return True

    def send_key_email(self, customer_email: str, key: str, key_type: str) -> bool:
        """📧 Send license key via email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.admin_email
            msg['To'] = customer_email
            msg['Subject'] = f"ClausoNet 4.0 Pro - Your {key_type.title()} License Key"

            # Email body
            body = f"""
Dear Valued Customer,

Thank you for choosing ClausoNet 4.0 Pro!

Your {key_type.title()} License Key: {key}

🚀 ACTIVATION INSTRUCTIONS:
1. Download ClausoNet 4.0 Pro from our website
2. Open the application
3. Go to Settings → License
4. Enter your license key: {key}
5. Click "Activate License"

🎯 FEATURES INCLUDED:
"""

            # Add features based on key type
            key_data = None
            for k in self.database['keys']:
                if k['key'] == key:
                    key_data = k
                    break

            if key_data:
                for feature in key_data['features']:
                    body += f"• {feature.replace('_', ' ').title()}\n"

                body += f"""
📅 License Details:
• Type: {key_data['type'].title()}
• Valid Until: {key_data['expiry_date'][:10]}
• Max Devices: {key_data['max_devices']}

"""

            body += """
Need Help?
• Email: support@clausonet.com
• Documentation: https://docs.clausonet.com
• Video Tutorials: https://youtube.com/clausonet

Best regards,
ClausoNet Team
"""

            msg.attach(MIMEText(body, 'plain'))

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.admin_email, self.admin_password)
            text = msg.as_string()
            server.sendmail(self.admin_email, customer_email, text)
            server.quit()

            self.logger.info(f"License key email sent to {customer_email}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send email to {customer_email}: {e}")
            return False

    def get_key_info(self, key: str) -> Optional[Dict[str, Any]]:
        """📋 Get key information"""
        for k in self.database['keys']:
            if k['key'] == key:
                return k
        return None

    def get_customer_info(self, email: str) -> Optional[Dict[str, Any]]:
        """👤 Get customer information"""
        for c in self.database['customers']:
            if c['email'] == email.lower().strip():
                return c
        return None

    def list_keys_by_type(self, key_type: str) -> List[Dict[str, Any]]:
        """📊 List all keys by type"""
        return [k for k in self.database['keys'] if k['type'] == key_type]

    def get_statistics(self) -> Dict[str, Any]:
        """📈 Get license statistics"""
        stats = self.database['statistics'].copy()

        # Add real-time calculations
        active_keys = len([k for k in self.database['keys'] if k['status'] == 'activated'])
        expired_keys = 0

        for key in self.database['keys']:
            try:
                expiry = datetime.fromisoformat(key['expiry_date'].replace('Z', '+00:00'))
                if datetime.utcnow().replace(tzinfo=expiry.tzinfo) > expiry:
                    expired_keys += 1
            except:
                pass

        stats.update({
            'active_keys': active_keys,
            'expired_keys': expired_keys,
            'total_customers': len(self.database['customers'])
        })

        return stats

    def get_hardware_fingerprint(self) -> str:
        """🔧 Get current machine hardware fingerprint"""
        try:
            import platform
            import subprocess
            import uuid
            import hashlib
            import json

            components = {}

            # CPU Info
            try:
                cpu_info = platform.processor()
                if cpu_info and cpu_info.strip():
                    components['cpu_id'] = cpu_info.strip()
                else:
                    if platform.system() == "Windows":
                        result = subprocess.run(['wmic', 'cpu', 'get', 'ProcessorId', '/format:value'],
                                              capture_output=True, text=True, shell=True)
                        for line in result.stdout.split('\n'):
                            if line.startswith('ProcessorId='):
                                cpu_id = line.split('=', 1)[1].strip()
                                if cpu_id:
                                    components['cpu_id'] = cpu_id
                                    break
                        else:
                            components['cpu_id'] = "UNKNOWN_CPU"
                    else:
                        components['cpu_id'] = "UNKNOWN_CPU"
            except:
                components['cpu_id'] = "UNKNOWN_CPU"

            # Motherboard Serial
            try:
                if platform.system() == "Windows":
                    result = subprocess.run(['wmic', 'baseboard', 'get', 'SerialNumber', '/format:value'],
                                          capture_output=True, text=True, shell=True)
                    for line in result.stdout.split('\n'):
                        if 'SerialNumber=' in line:
                            components['motherboard'] = line.split('=')[1].strip() or "UNKNOWN_MB"
                            break
                    else:
                        components['motherboard'] = "UNKNOWN_MB"
                else:
                    components['motherboard'] = "UNKNOWN_MB"
            except:
                components['motherboard'] = "UNKNOWN_MB"

            # MAC Address
            try:
                mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0,8*6,8)][::-1])
                components['mac_address'] = mac
            except:
                components['mac_address'] = "UNKNOWN_MAC"

            # Windows Product ID
            try:
                if platform.system() == "Windows":
                    result = subprocess.run(['wmic', 'os', 'get', 'SerialNumber', '/format:value'],
                                          capture_output=True, text=True, shell=True)
                    for line in result.stdout.split('\n'):
                        if 'SerialNumber=' in line:
                            components['windows_id'] = line.split('=')[1].strip() or "UNKNOWN_WIN"
                            break
                    else:
                        components['windows_id'] = "UNKNOWN_WIN"
                else:
                    components['windows_id'] = "UNKNOWN_WIN"
            except:
                components['windows_id'] = "UNKNOWN_WIN"

            # BIOS Info
            try:
                if platform.system() == "Windows":
                    result = subprocess.run(['wmic', 'bios', 'get', 'SerialNumber,Version', '/format:value'],
                                          capture_output=True, text=True, shell=True)
                    bios_info = {}
                    for line in result.stdout.split('\n'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            bios_info[key.strip()] = value.strip()
                    components['bios_info'] = f"{bios_info.get('SerialNumber', 'UNKNOWN')}_{bios_info.get('Version', 'UNKNOWN')}"
                else:
                    components['bios_info'] = "UNKNOWN_BIOS"
            except:
                components['bios_info'] = "UNKNOWN_BIOS"

            components['platform'] = platform.platform()

            # Generate fingerprint
            combined_string = json.dumps(components, sort_keys=True)
            fingerprint = hashlib.sha256(combined_string.encode()).hexdigest()[:32]
            return fingerprint

        except Exception as e:
            self.logger.error(f"Error getting hardware fingerprint: {e}")
            return "ERROR_HARDWARE_ID"

    def check_any_valid_license(self) -> bool:
        """🔍 Check if any valid license exists for current machine"""
        try:
            current_hardware = self.get_hardware_fingerprint()
            current_time = datetime.now()

            # First check user license file (for end users)
            user_license_path = os.path.join(self.admin_data_path, "user_license.json")
            if os.path.exists(user_license_path):
                try:
                    with open(user_license_path, 'r', encoding='utf-8') as f:
                        user_license = json.load(f)

                    # Check hardware binding
                    if user_license.get('hardware_id') == current_hardware:
                        # Check expiry
                        expiry_str = user_license.get('expiry_date', '')
                        if expiry_str:
                            try:
                                if 'T' in expiry_str:
                                    expiry_date = datetime.fromisoformat(expiry_str.replace('Z', ''))
                                else:
                                    expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')

                                if current_time <= expiry_date:
                                    # Valid user license found
                                    self.logger.info(f"Valid user license found: {user_license.get('license_key', 'N/A')[:10]}...")
                                    return True
                            except:
                                pass  # Invalid date format, continue checking
                except Exception as e:
                    self.logger.warning(f"Error reading user license file: {e}")

            # Then check all licenses in admin database (for admin users)
            for license_info in self.database['keys']:
                # Check hardware binding - check if current hardware is in the hardware_ids list
                hardware_ids = license_info.get('hardware_ids', [])
                if current_hardware not in hardware_ids:
                    continue

                # Check expiry
                expiry_str = license_info.get('expiry_date', '')
                if expiry_str:
                    try:
                        if 'T' in expiry_str:
                            expiry_date = datetime.fromisoformat(expiry_str.replace('Z', ''))
                        else:
                            expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')

                        if current_time > expiry_date:
                            continue  # License expired

                    except:
                        continue  # Invalid date format

                # Check if license is activated
                if license_info.get('status') != 'activated':
                    continue

                # If we reach here, license is valid
                license_key = license_info.get('key', 'unknown')
                self.logger.info(f"Valid license found: {license_key} (type: {license_info.get('type', 'unknown')})")
                return True

            self.logger.info("No valid license found for current machine")
            return False

        except Exception as e:
            self.logger.error(f"Error checking license: {e}")
            return False

    def activate_license(self, license_key: str) -> bool:
        """🔑 Activate license key for current machine"""
        try:
            # 🐛 DEBUG: Add comprehensive logging
            self.logger.info(f"🔑 ACTIVATION ATTEMPT:")
            self.logger.info(f"   Input key: {license_key}")
            self.logger.info(f"   Database path: {self.license_database_path}")
            self.logger.info(f"   Database exists: {os.path.exists(self.license_database_path)}")

            # Validate key format - More flexible validation
            if not license_key:
                self.logger.error(f"❌ Empty license key")
                return False

            # Normalize key format (handle common typos)
            license_key = license_key.strip().upper()

            # Fix common typos: 0 vs O, 1 vs I
            license_key = license_key.replace('CNPR0-', 'CNPRO-')  # Fix 0 vs O
            license_key = license_key.replace('CNPRl-', 'CNPRO-')  # Fix l vs O
            license_key = license_key.replace('CNPRI-', 'CNPRO-')  # Fix I vs O

            self.logger.info(f"   Normalized key: {license_key}")

            if not license_key.startswith("CNPRO-"):
                self.logger.error(f"❌ Invalid license key format: {license_key}")
                self.logger.error(f"   Expected format: CNPRO-XXXX-XXXX-XXXX-XXXX")
                return False

            # 🐛 DEBUG: Log database info
            self.logger.info(f"   Total keys in database: {len(self.database.get('keys', []))}")

            # Find key in database
            license_info = None
            license_index = None
            for i, key_data in enumerate(self.database['keys']):
                if key_data.get('key') == license_key:
                    license_info = key_data
                    license_index = i
                    break

            if license_info is None:
                self.logger.error(f"❌ License key not found in database: {license_key}")
                # 🐛 DEBUG: Show all available keys (first 10 chars only for security)
                available_keys = [k.get('key', 'N/A')[:10] + '...' for k in self.database.get('keys', [])]
                self.logger.error(f"   Available keys: {available_keys}")
                return False

            self.logger.info(f"✅ License key found in database")

            # Check if already activated and device limit
            current_hardware = self.get_hardware_fingerprint()
            hardware_ids = license_info.get('hardware_ids', [])
            max_devices = license_info.get('max_devices', 1)

            # 🐛 DEBUG: Hardware info
            self.logger.info(f"   Current hardware: {current_hardware[:10]}...")
            self.logger.info(f"   Registered hardware IDs: {[h[:10] + '...' for h in hardware_ids]}")
            self.logger.info(f"   Max devices allowed: {max_devices}")

            # If current hardware not in list, check if we can add it
            if current_hardware not in hardware_ids:
                if len(hardware_ids) >= max_devices:
                    self.logger.error(f"❌ License key already activated on maximum devices ({max_devices}): {license_key}")
                    return False

            # Check if license is still valid (not expired)
            expiry_str = license_info.get('expiry_date', '')
            if expiry_str:
                try:
                    if 'T' in expiry_str:
                        expiry_date = datetime.fromisoformat(expiry_str.replace('Z', ''))
                    else:
                        expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')

                    if datetime.now() > expiry_date:
                        self.logger.error(f"License key expired: {license_key}")
                        return False
                except Exception as e:
                    self.logger.error(f"Invalid expiry date format for key {license_key}: {e}")
                    return False

            # Activate license - bind to current hardware
            if current_hardware not in hardware_ids:
                self.database['keys'][license_index]['hardware_ids'].append(current_hardware)

            self.database['keys'][license_index]['status'] = 'activated'
            self.database['keys'][license_index]['activated_at'] = datetime.now().isoformat()

            # Update activation count
            if 'activation_count' not in self.database['keys'][license_index]:
                self.database['keys'][license_index]['activation_count'] = 0
            self.database['keys'][license_index]['activation_count'] += 1

            # Update statistics
            self.database['statistics']['keys_activated'] += 1

            # Save database
            self.save_database()

            # Also create user license file for end users
            try:
                user_license_data = {
                    "license_key": license_key,
                    "activation_date": datetime.now().isoformat(),
                    "hardware_id": current_hardware,
                    "license_type": license_info.get('type', 'unknown'),
                    "expiry_date": license_info.get('expiry_date', ''),
                    "features": license_info.get('features', []),
                    "status": "active"
                }

                user_license_path = os.path.join(self.admin_data_path, "user_license.json")
                os.makedirs(self.admin_data_path, exist_ok=True)

                with open(user_license_path, 'w', encoding='utf-8') as f:
                    json.dump(user_license_data, f, indent=2, ensure_ascii=False)

                self.logger.info(f"User license file created: {user_license_path}")
            except Exception as e:
                self.logger.warning(f"Failed to create user license file: {e}")

            self.logger.info(f"License activated successfully: {license_key} for hardware: {current_hardware[:8]}...")
            return True

        except Exception as e:
            self.logger.error(f"Error activating license {license_key}: {e}")
            return False

    def generate_admin_report(self) -> str:
        """📊 Generate admin report"""
        stats = self.get_statistics()

        report = f"""
🎯 CLAUSONET 4.0 PRO - LICENSE ADMIN REPORT
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

📈 OVERVIEW:
• Total Keys Generated: {stats['total_keys_generated']}
• Active Keys: {stats['active_keys']}
• Expired Keys: {stats['expired_keys']}
• Total Customers: {stats['total_customers']}
• Revenue Tracked: ${stats['revenue_tracked']:.2f}

🔑 KEY BREAKDOWN:
• Trial Keys: {stats['trial_keys']}
• Monthly Keys: {stats['monthly_keys']}
• Quarterly Keys: {stats['quarterly_keys']}
• Lifetime Keys: {stats['lifetime_keys']}
• Multi-Device Keys: {stats['multi_device_keys']}

💰 REVENUE ANALYSIS:
• Average Revenue per Customer: ${stats['revenue_tracked'] / max(stats['total_customers'], 1):.2f}
• Activation Rate: {(stats['keys_activated'] / max(stats['total_keys_generated'], 1) * 100):.1f}%

🎯 RECENT ACTIVITY:
"""

        # Add recent keys
        recent_keys = sorted(self.database['keys'], key=lambda x: x['created_at'], reverse=True)[:5]
        for key in recent_keys:
            report += f"• {key['key']} ({key['type']}) - {key['created_at'][:10]}\n"

        return report

    def create_sample_license_for_testing(self):
        """Create a sample license key for testing purposes"""
        try:
            # Generate a lifetime license for testing
            self.logger.info("Creating sample lifetime license for testing...")
            sample_license = self.generate_lifetime_key(price=0.0)
            sample_key = sample_license['key']
            self.logger.info(f"✅ Sample license created: {sample_key}")
            print(f"✅ Sample license key created for testing: {sample_key}")
            print("   Use this key to test license activation in the main application.")
            return sample_key
        except Exception as e:
            self.logger.error(f"Failed to create sample license: {e}")
            return None


# CLI Interface for Admin
def main():
    print("🎯 ClausoNet 4.0 Pro - License Key Generator")
    print("=" * 50)

    generator = LicenseKeyGenerator()

    while True:
        print("\n📋 ADMIN MENU:")
        print("1. 🔍 Generate Trial Key (7 days)")
        print("2. 📅 Generate Monthly Key")
        print("3. 📅 Generate Quarterly Key (3 months)")
        print("4. 🎯 Generate Lifetime Key")
        print("5. 🖥️  Generate Multi-Device Key (6 devices)")
        print("6. 👤 Create Customer")
        print("7. 🔗 Assign Key to Customer")
        print("8. 📧 Send Key via Email")
        print("9. 📋 View Key Info")
        print("10. 📊 View Statistics")
        print("11. 📊 Generate Report")
        print("0. ❌ Exit")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            days = int(input("Trial duration (days, default 7): ") or "7")
            key_data = generator.generate_trial_key(days)
            print(f"✅ Generated trial key: {key_data['key']}")

        elif choice == "2":
            months = int(input("Duration (months, default 1): ") or "1")
            price = float(input(f"Price (default $29.99): ") or "29.99")
            key_data = generator.generate_monthly_key(months, price)
            print(f"✅ Generated monthly key: {key_data['key']}")

        elif choice == "3":
            quarters = int(input("Duration (quarters, default 1): ") or "1")
            price = float(input(f"Price (default $79.99): ") or "79.99")
            key_data = generator.generate_quarterly_key(quarters, price)
            print(f"✅ Generated quarterly key: {key_data['key']}")

        elif choice == "4":
            price = float(input(f"Price (default $299.99): ") or "299.99")
            key_data = generator.generate_lifetime_key(price)
            print(f"✅ Generated lifetime key: {key_data['key']}")

        elif choice == "5":
            devices = int(input("Max devices (default 6): ") or "6")
            days = int(input("Duration (days, default 365): ") or "365")
            price = float(input(f"Price (default $499.99): ") or "499.99")
            key_data = generator.generate_multi_device_key(devices, days, price)
            print(f"✅ Generated multi-device key: {key_data['key']}")

        elif choice == "6":
            email = input("Customer email: ").strip()
            name = input("Customer name (optional): ").strip()
            phone = input("Phone (optional): ").strip()
            company = input("Company (optional): ").strip()
            customer = generator.create_customer_record(email, name, phone, company)
            print(f"✅ Created customer: {customer['email']}")

        elif choice == "7":
            key = input("License key: ").strip()
            email = input("Customer email: ").strip()
            if generator.assign_key_to_customer(key, email):
                print("✅ Key assigned successfully")
            else:
                print("❌ Failed to assign key")

        elif choice == "8":
            email = input("Customer email: ").strip()
            key = input("License key: ").strip()
            key_info = generator.get_key_info(key)
            if key_info:
                if generator.send_key_email(email, key, key_info['type']):
                    print("✅ Email sent successfully")
                else:
                    print("❌ Failed to send email")
            else:
                print("❌ Key not found")

        elif choice == "9":
            key = input("License key: ").strip()
            key_info = generator.get_key_info(key)
            if key_info:
                print(json.dumps(key_info, indent=2, ensure_ascii=False))
            else:
                print("❌ Key not found")

        elif choice == "10":
            stats = generator.get_statistics()
            print(json.dumps(stats, indent=2, ensure_ascii=False))

        elif choice == "11":
            report = generator.generate_admin_report()
            print(report)

        elif choice == "0":
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    main()
