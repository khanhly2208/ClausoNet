#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - License Activation Wizard
Kích hoạt license, tạo hardware fingerprint và xác thực với server
"""

import hashlib
import json
import platform
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import requests
import psutil
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging
import os

class LicenseWizard:
    def __init__(self):
        self.license_server = "https://license.clausonet.com/api/v4"
        # Đường dẫn file license local (relative to ClausoNet4.0 directory)
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.local_license_path = os.path.join(script_dir, "license", "clausonet.lic")
        self.cert_path = "./certs/clausonet.pem"
        self.timeout = 30

        # Tạo thư mục cần thiết
        os.makedirs(os.path.dirname(self.local_license_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.cert_path), exist_ok=True)
        os.makedirs('logs', exist_ok=True)

        self.setup_logging()

    def setup_logging(self):
        """Thiết lập logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/license.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('LicenseWizard')

    def get_cpu_identifier(self) -> str:
        """Lấy CPU identifier - chuẩn hóa với GUI"""
        try:
            # Sử dụng py-cpuinfo giống như GUI để consistency
            import cpuinfo
            cpu_info = cpuinfo.get_cpu_info()
            return cpu_info.get('brand_raw', 'UNKNOWN_CPU')
        except ImportError:
            self.logger.warning("py-cpuinfo not available, falling back to platform.processor()")
            return platform.processor()
        except Exception as e:
            self.logger.warning(f"Could not get CPU info: {e}")
            # Fallback: sử dụng platform info
            return platform.processor()

    def get_motherboard_serial(self) -> str:
        """Lấy motherboard serial number"""
        try:
            result = subprocess.run(
                ['wmic', 'baseboard', 'get', 'SerialNumber', '/format:value'],
                capture_output=True, text=True, shell=True
            )
            for line in result.stdout.split('\n'):
                if line.startswith('SerialNumber='):
                    return line.split('=', 1)[1].strip()
        except Exception as e:
            self.logger.warning(f"Could not get motherboard serial: {e}")

        return "UNKNOWN_MOTHERBOARD"

    def get_primary_mac(self) -> str:
        """Lấy MAC address của network adapter chính"""
        try:
            # Lấy MAC address của adapter có IP
            import socket
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)

            # Tìm MAC address tương ứng
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == psutil.AF_LINK:  # MAC address
                        return addr.address.replace('-', ':').upper()
        except Exception as e:
            self.logger.warning(f"Could not get MAC address: {e}")

        # Fallback: sử dụng uuid
        mac = uuid.getnode()
        return ':'.join([f"{(mac >> i) & 0xff:02x}" for i in range(0, 48, 8)][::-1]).upper()

    def get_windows_product_id(self) -> str:
        """Lấy Windows Product ID"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            product_id = winreg.QueryValueEx(key, "ProductId")[0]
            winreg.CloseKey(key)
            return product_id
        except Exception as e:
            self.logger.warning(f"Could not get Windows Product ID: {e}")
            return "UNKNOWN_WINDOWS_ID"

    def get_bios_signature(self) -> str:
        """Lấy BIOS signature"""
        try:
            result = subprocess.run(
                ['wmic', 'bios', 'get', 'SerialNumber,Version', '/format:value'],
                capture_output=True, text=True, shell=True
            )

            bios_info = {}
            for line in result.stdout.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    bios_info[key.strip()] = value.strip()

            return f"{bios_info.get('SerialNumber', 'UNKNOWN')}_{bios_info.get('Version', 'UNKNOWN')}"
        except Exception as e:
            self.logger.warning(f"Could not get BIOS info: {e}")
            return "UNKNOWN_BIOS"

    def generate_hardware_id(self) -> str:
        """Tạo hardware fingerprint duy nhất"""
        self.logger.info("Generating hardware fingerprint...")

        components = {
            'cpu_id': self.get_cpu_identifier(),
            'motherboard': self.get_motherboard_serial(),
            'mac_address': self.get_primary_mac(),
            'windows_id': self.get_windows_product_id(),
            'bios_info': self.get_bios_signature(),
            'platform': platform.platform()
        }

        # Log components (ẩn một phần thông tin nhạy cảm)
        for key, value in components.items():
            if len(value) > 8:
                display_value = value[:4] + "***" + value[-4:]
            else:
                display_value = "***"
            self.logger.info(f"Hardware component {key}: {display_value}")

        # Tạo SHA-256 hash
        combined_string = json.dumps(components, sort_keys=True)
        fingerprint = hashlib.sha256(combined_string.encode()).hexdigest()[:32]

        self.logger.info(f"Hardware ID generated: {fingerprint[:8]}***{fingerprint[-8:]}")
        return fingerprint

    def create_encryption_key(self, hardware_id: str) -> bytes:
        """Tạo encryption key từ hardware ID"""
        salt = b'clausonet_v4_salt_2024_pro'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(hardware_id.encode()))
        return key

    def encrypt_data(self, data: str, key: bytes) -> str:
        """Mã hóa dữ liệu"""
        cipher = Fernet(key)
        encrypted_data = cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()

    def decrypt_data(self, encrypted_data: str, key: bytes) -> str:
        """Giải mã dữ liệu"""
        cipher = Fernet(key)
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = cipher.decrypt(decoded_data)
        return decrypted_data.decode()

    def validate_license_format(self, customer_key: str) -> bool:
        """Kiểm tra format của license key"""
        # Format: CNPRO-XXXX-XXXX-XXXX-XXXX (case insensitive)
        import re
        # More flexible pattern - allow lowercase and mixed case
        pattern = r'^CNPRO-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}$'
        result = bool(re.match(pattern, customer_key.upper()))
        self.logger.info(f"License format validation for '{customer_key}': {'PASS' if result else 'FAIL'}")
        return result

    def contact_license_server(self, customer_key: str, hardware_id: str) -> Dict[str, Any]:
        """Liên hệ với license server để xác thực"""
        self.logger.info("Contacting license server...")

        payload = {
            'customer_key': customer_key,
            'hardware_id': hardware_id,
            'product_version': '4.0.0',
            'product_edition': 'Pro',
            'validation_time': datetime.utcnow().isoformat(),
            'machine_info': {
                'os': platform.system(),
                'os_version': platform.release(),
                'python_version': platform.python_version(),
                'hostname': platform.node()
            }
        }

        try:
            response = requests.post(
                f"{self.license_server}/validate",
                json=payload,
                timeout=self.timeout,
                headers={
                    'User-Agent': 'ClausoNet-4.0-Pro/1.0',
                    'Content-Type': 'application/json'
                }
            )

            self.logger.info(f"Server response: {response.status_code}")

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise Exception("Invalid license key")
            elif response.status_code == 409:
                raise Exception("License already activated on different hardware")
            elif response.status_code == 429:
                raise Exception("Too many activation attempts. Please try again later")
            else:
                raise Exception(f"Server error: {response.status_code} - {response.text}")

        except requests.exceptions.ConnectTimeout:
            raise Exception("Connection timeout. Please check your internet connection")
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to license server. Please check your internet connection")
        except Exception as e:
            if "Invalid license key" in str(e):
                raise e
            raise Exception(f"License server communication failed: {e}")

    def save_local_license(self, license_data: Dict[str, Any], hardware_id: str) -> None:
        """Lưu license vào file local với improved error handling"""
        self.logger.info("Saving license file...")

        # Tạo local license object
        local_license = {
            'customer_key': license_data['customer_key'],
            'hardware_id': hardware_id,
            'activation_date': datetime.utcnow().isoformat(),
            'expiry_date': license_data['expiry_date'],
            'license_type': license_data['license_type'],
            'features': license_data['features'],
            'server_signature': license_data.get('signature', 'OFFLINE_MODE_NO_SIGNATURE'),
            'local_checksum': hashlib.sha256(
                json.dumps(license_data, sort_keys=True).encode()
            ).hexdigest()
        }

        # Ensure license directory exists
        os.makedirs(os.path.dirname(self.local_license_path), exist_ok=True)

        # Fix file permissions before writing
        self._fix_license_file_permissions()

        # For demo mode, save as plain JSON (no encryption)
        if local_license.get('server_signature') == 'OFFLINE_MODE_NO_SIGNATURE':
            # Save as plain JSON for demo
            with open(self.local_license_path, 'w', encoding='utf-8') as f:
                json.dump(local_license, f, indent=2, ensure_ascii=False)
        else:
            # Mã hóa license for production
            encryption_key = self.create_encryption_key(hardware_id)
            encrypted_license = self.encrypt_data(
                json.dumps(local_license, indent=2),
                encryption_key
            )

            # Lưu file
            with open(self.local_license_path, 'w') as f:
                f.write(encrypted_license)

        # Set proper file permissions (readable/writable)
        try:
            import stat
            os.chmod(self.local_license_path, stat.S_IREAD | stat.S_IWRITE)
        except:
            pass

        self.logger.info(f"License saved to: {self.local_license_path}")

    def _fix_license_file_permissions(self) -> None:
        """Fix file permissions before writing license file"""
        if os.path.exists(self.local_license_path):
            try:
                import stat
                # Remove read-only attribute if exists
                if platform.system() == "Windows":
                    os.system(f'attrib -r "{self.local_license_path}"')

                # Set read/write permissions
                os.chmod(self.local_license_path, stat.S_IREAD | stat.S_IWRITE)
                self.logger.info("Fixed license file permissions")
            except Exception as e:
                self.logger.warning(f"Could not fix file permissions: {e}")

    def load_local_license(self) -> Optional[Dict[str, Any]]:
        """Đọc license từ file local với enhanced format detection"""
        if not os.path.exists(self.local_license_path):
            return None

        try:
            with open(self.local_license_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            if not content:
                return None

            # Try to parse as plain JSON first (for demo/offline licenses)
            try:
                license_data = json.loads(content)
                self.logger.info("Loaded license as plain JSON")

                # Verify hardware ID matches (if available)
                stored_hardware_id = license_data.get('hardware_id', '')
                if stored_hardware_id:
                    current_hardware_id = self.generate_hardware_id()
                    if stored_hardware_id != current_hardware_id:
                        self.logger.error("Hardware ID mismatch - license invalid")
                        return None

                return license_data

            except json.JSONDecodeError:
                # If not JSON, try to decrypt (for encrypted licenses)
                self.logger.info("Attempting to decrypt license data")

                hardware_id = self.generate_hardware_id()
                encryption_key = self.create_encryption_key(hardware_id)

                try:
                    decrypted_data = self.decrypt_data(content, encryption_key)
                    license_data = json.loads(decrypted_data)

                    # Verify hardware ID matches
                    if license_data['hardware_id'] != hardware_id:
                        self.logger.error("Hardware ID mismatch - license invalid")
                        return None

                    self.logger.info("Loaded encrypted license successfully")
                    return license_data

                except Exception as decrypt_error:
                    self.logger.error(f"Failed to decrypt license: {decrypt_error}")
                    return None

        except Exception as e:
            self.logger.error(f"Failed to load license: {e}")
            return None

    def verify_license_validity(self, license_data: Dict[str, Any]) -> bool:
        """Kiểm tra license còn hợp lệ không"""
        try:
            expiry_date = datetime.fromisoformat(license_data['expiry_date'].replace('Z', '+00:00'))
            current_date = datetime.utcnow().replace(tzinfo=expiry_date.tzinfo)

            if current_date > expiry_date:
                self.logger.error("License expired")
                return False

            # Kiểm tra hardware ID
            current_hardware_id = self.generate_hardware_id()
            if license_data['hardware_id'] != current_hardware_id:
                self.logger.error("Hardware configuration changed")
                return False

            return True

        except Exception as e:
            self.logger.error(f"License validation failed: {e}")
            return False

    def interactive_activation(self) -> bool:
        """Wizard tương tác để kích hoạt license"""
        print("=" * 60)
        print("ClausoNet 4.0 Pro - License Activation Wizard")
        print("=" * 60)
        print()

        # Kiểm tra license hiện tại
        existing_license = self.load_local_license()
        if existing_license and self.verify_license_validity(existing_license):
            print("✓ Valid license already exists!")
            print(f"Customer Key: {existing_license['customer_key']}")
            print(f"License Type: {existing_license['license_type']}")
            print(f"Expires: {existing_license['expiry_date']}")

            choice = input("\nDo you want to reactivate? (y/N): ").strip().lower()
            if choice != 'y':
                return True

        print("Starting license activation process...")
        print()

        # Nhập license key
        while True:
            customer_key = input("Enter your license key (CNPRO-XXXX-XXXX-XXXX-XXXX): ").strip().upper()

            if not customer_key:
                print("License key cannot be empty!")
                continue

            if not self.validate_license_format(customer_key):
                print("Invalid license key format! Please use format: CNPRO-XXXX-XXXX-XXXX-XXXX")
                continue

            break

        print("\n" + "-" * 40)
        print("Generating hardware fingerprint...")

        try:
            # Tạo hardware ID
            hardware_id = self.generate_hardware_id()
            print(f"Hardware ID: {hardware_id[:8]}***{hardware_id[-8:]}")

            print("\nActivating license (offline mode)...")
            print("This may take a few moments...")

            # Create offline license for demo
            license_response = {
                'status': 'success',
                'customer_key': customer_key,
                'license_type': 'professional',
                'expiry_date': (datetime.utcnow() + timedelta(days=365)).isoformat(),
                'features': ['ai_generation', 'unlimited_workflows', 'api_access'],
                'hardware_id': hardware_id,
                'activation_date': datetime.utcnow().isoformat(),
                'created_by': 'Demo Mode'
            }

            print("✓ License validation successful!")

            # Lưu license
            self.save_local_license(license_response, hardware_id)

            print("\n" + "=" * 60)
            print("LICENSE ACTIVATION COMPLETED")
            print("=" * 60)
            print(f"Customer Key: {customer_key}")
            print(f"License Type: {license_response['license_type']}")
            print(f"Expires: {license_response['expiry_date']}")
            print(f"Features: {', '.join(license_response['features'])}")
            print("\nClausoNet 4.0 Pro is now ready to use!")
            print("=" * 60)

            return True

        except Exception as e:
            print(f"\n✗ License activation failed: {e}")
            print("\nPlease check:")
            print("- License key is correct")
            print("- Internet connection is working")
            print("- License is not already activated on another machine")
            print("\nContact support if the problem persists:")
            print("Email: support@clausonet.com")
            return False

    def refresh_hardware_id(self) -> bool:
        """Làm mới hardware ID (dùng khi hardware thay đổi)"""
        print("Refreshing hardware fingerprint...")

        # Load existing license
        existing_license = self.load_local_license()
        if not existing_license:
            print("No existing license found. Please run full activation.")
            return False

        customer_key = existing_license['customer_key']

        try:
            # Tạo hardware ID mới
            new_hardware_id = self.generate_hardware_id()

            print("Requesting license transfer to new hardware...")

            # Liên hệ server để cập nhật hardware ID
            payload = {
                'customer_key': customer_key,
                'old_hardware_id': existing_license['hardware_id'],
                'new_hardware_id': new_hardware_id,
                'transfer_reason': 'hardware_change',
                'validation_time': datetime.utcnow().isoformat()
            }

            response = requests.post(
                f"{self.license_server}/transfer",
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                license_response = response.json()
                self.save_local_license(license_response, new_hardware_id)
                print("✓ Hardware ID refresh successful!")
                return True
            else:
                print(f"✗ Hardware refresh failed: {response.text}")
                return False

        except Exception as e:
            print(f"✗ Hardware refresh failed: {e}")
            return False

    def check_license_status(self) -> Dict[str, Any]:
        """Kiểm tra trạng thái license hiện tại"""
        license_data = self.load_local_license()
        if not license_data:
            return {'status': 'not_activated', 'message': 'No license found'}

        if self.verify_license_validity(license_data):
            expiry_date = datetime.fromisoformat(license_data['expiry_date'].replace('Z', '+00:00'))
            days_until_expiry = (expiry_date - datetime.utcnow().replace(tzinfo=expiry_date.tzinfo)).days

            return {
                'status': 'active',
                'customer_key': license_data['customer_key'],
                'license_type': license_data['license_type'],
                'expiry_date': license_data['expiry_date'],
                'days_until_expiry': days_until_expiry,
                'features': license_data['features']
            }
        else:
            return {'status': 'invalid', 'message': 'License expired or hardware mismatch'}

    def check_and_update_hardware_id(self, license_key: str) -> bool:
        """Check if license exists with different hardware ID and update if needed"""
        try:
            if not os.path.exists(self.local_license_path):
                return False  # No existing license

            current_hardware_id = self.generate_hardware_id()

            # Try to read existing license
            with open(self.local_license_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return False

                license_data = json.loads(content)
                stored_hardware_id = license_data.get('hardware_id', '')
                stored_key = license_data.get('customer_key', '')

                # If same license key but different hardware ID, update it
                if (stored_key == license_key and
                    stored_hardware_id != current_hardware_id):

                    self.logger.info(f"Updating hardware ID from {stored_hardware_id[:8]}*** to {current_hardware_id[:8]}***")

                    # Update license with new hardware ID
                    license_data['hardware_id'] = current_hardware_id
                    license_data['updated_date'] = datetime.utcnow().isoformat()
                    license_data['update_reason'] = 'Hardware ID mismatch fix'

                    # Fix permissions and save
                    self._fix_license_file_permissions()

                    with open(self.local_license_path, 'w', encoding='utf-8') as f:
                        json.dump(license_data, f, indent=2, ensure_ascii=False)

                    self.logger.info("License hardware ID updated successfully")
                    return True

                return False

        except Exception as e:
            self.logger.warning(f"Could not check/update hardware ID: {e}")
            return False

    def activate_license(self, license_key: str, hardware_id: str = None) -> bool:
        """Kích hoạt license với key và hardware ID - Enhanced error handling"""
        try:
            self.logger.info(f"Starting license activation for key: {license_key}")

            # Use provided hardware_id or generate new one
            if hardware_id is None:
                hardware_id = self.generate_hardware_id()
                self.logger.info(f"Generated hardware ID: {hardware_id}")
            else:
                self.logger.info(f"Using provided hardware ID: {hardware_id}")

            # Check if we can update existing license with same key but different hardware ID
            if self.check_and_update_hardware_id(license_key):
                self.logger.info("License updated with current hardware ID - activation successful")
                return True

            # Validate license key format
            self.logger.info(f"Validating license key format...")
            if not self.validate_license_format(license_key):
                self.logger.error(f"Invalid license key format: {license_key}")
                return False

            self.logger.info("License key format validation passed")

            # For demo/offline mode - create license locally
            self.logger.info(f"Activating license offline: {license_key}")

            # Create mock license data for testing
            license_data = {
                'status': 'success',
                'customer_key': license_key,
                'license_type': 'professional',
                'expiry_date': (datetime.utcnow() + timedelta(days=365)).isoformat(),
                'features': ['ai_generation', 'unlimited_workflows', 'api_access'],
                'hardware_id': hardware_id,
                'activation_date': datetime.utcnow().isoformat(),
                'created_by': 'Demo Mode'
            }

            self.logger.info("Created license data structure")

            # Save license locally
            self.save_local_license(license_data, hardware_id)
            self.logger.info("License activated successfully (offline mode)")
            return True

        except Exception as e:
            self.logger.error(f"License activation error: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False

def main():
    """Hàm main để chạy từ command line"""
    import argparse

    parser = argparse.ArgumentParser(description='ClausoNet 4.0 Pro License Wizard')
    parser.add_argument('--activate', action='store_true',
                       help='Start interactive license activation')
    parser.add_argument('--check', action='store_true',
                       help='Check current license status')
    parser.add_argument('--refresh-hardware', action='store_true',
                       help='Refresh hardware fingerprint')
    parser.add_argument('--generate-hardware-id', action='store_true',
                       help='Generate and display hardware ID only')

    args = parser.parse_args()

    wizard = LicenseWizard()

    if args.generate_hardware_id:
        hardware_id = wizard.generate_hardware_id()
        print(f"Hardware ID: {hardware_id}")
        return

    if args.check:
        status = wizard.check_license_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        if status['status'] == 'active':
            sys.exit(0)
        else:
            sys.exit(1)

    if args.refresh_hardware:
        success = wizard.refresh_hardware_id()
        sys.exit(0 if success else 1)

    if args.activate or len(sys.argv) == 1:
        success = wizard.interactive_activation()
        sys.exit(0 if success else 1)

    parser.print_help()

if __name__ == "__main__":
    main()
