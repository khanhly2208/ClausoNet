#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Enhanced Admin License System
Complete license management with user workflow integration
"""

import os
import sys
import json
import datetime
import hashlib
import uuid
import smtplib
import requests
from pathlib import Path
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Any, Optional

# Import license generator
from license_key_generator import LicenseKeyGenerator

class EnhancedAdminLicenseSystem:
    """
    🎯 Enhanced Admin License System
    Manages complete workflow from key generation to user activation
    """

    def __init__(self):
        self.license_generator = LicenseKeyGenerator()
        self.admin_data_path = Path("admin_data")
        self.admin_data_path.mkdir(exist_ok=True)

        # Enhanced database structure
        self.database_file = self.admin_data_path / "enhanced_license_database.json"
        self.customers_file = self.admin_data_path / "customers_database.json"
        self.activation_log_file = self.admin_data_path / "activation_log.json"

        # Initialize databases
        self.init_databases()

        # Email configuration
        self.email_config = self.load_email_config()

    def init_databases(self):
        """Initialize enhanced database structure"""

        # Enhanced License Database
        if not self.database_file.exists():
            enhanced_db = {
                "keys": [],
                "customers": [],
                "activations": [],
                "settings": {
                    "created_at": datetime.datetime.now().isoformat(),
                    "version": "2.0",
                    "encryption_enabled": True,
                    "online_validation": True
                },
                "statistics": {
                    "total_keys_generated": 0,
                    "total_customers": 0,
                    "total_activations": 0,
                    "revenue_tracked": 0.0,
                    "active_licenses": 0
                }
            }
            self.save_enhanced_database(enhanced_db)

        # Customer Database
        if not self.customers_file.exists():
            customers_db = {
                "customers": [],
                "customer_history": [],
                "customer_analytics": {},
                "created_at": datetime.datetime.now().isoformat()
            }
            with open(self.customers_file, 'w', encoding='utf-8') as f:
                json.dump(customers_db, f, indent=2, ensure_ascii=False)

        # Activation Log
        if not self.activation_log_file.exists():
            activation_log = {
                "activations": [],
                "failed_attempts": [],
                "analytics": {
                    "total_attempts": 0,
                    "success_rate": 0.0,
                    "common_errors": []
                }
            }
            with open(self.activation_log_file, 'w', encoding='utf-8') as f:
                json.dump(activation_log, f, indent=2, ensure_ascii=False)

    def load_enhanced_database(self) -> Dict:
        """Load enhanced license database"""
        try:
            with open(self.database_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading enhanced database: {e}")
            return {}

    def save_enhanced_database(self, data: Dict):
        """Save enhanced license database"""
        try:
            with open(self.database_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving enhanced database: {e}")

    def load_email_config(self) -> Dict:
        """Load email configuration"""
        config_file = self.admin_data_path / "email_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        # Default email config
        return {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "admin_email": "",
            "admin_password": "",
            "enabled": False
        }

    def save_email_config(self, config: Dict):
        """Save email configuration"""
        config_file = self.admin_data_path / "email_config.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.email_config = config
            return True
        except Exception as e:
            print(f"Error saving email config: {e}")
            return False

    def add_customer(self, customer_data: Dict) -> str:
        """Add new customer with unique ID"""
        try:
            # Load customers database
            with open(self.customers_file, 'r', encoding='utf-8') as f:
                customers_db = json.load(f)

            # Generate unique customer ID
            customer_id = str(uuid.uuid4())

            # Enhanced customer record
            customer_record = {
                "id": customer_id,
                "email": customer_data.get("email", ""),
                "name": customer_data.get("name", ""),
                "phone": customer_data.get("phone", ""),
                "company": customer_data.get("company", ""),
                "created_at": datetime.datetime.now().isoformat(),
                "last_contact": datetime.datetime.now().isoformat(),
                "total_spent": 0.0,
                "license_keys": [],
                "status": "active",
                "notes": customer_data.get("notes", ""),
                "hardware_ids": [],
                "activation_history": []
            }

            customers_db["customers"].append(customer_record)

            # Save customers database
            with open(self.customers_file, 'w', encoding='utf-8') as f:
                json.dump(customers_db, f, indent=2, ensure_ascii=False)

            print(f"✅ Customer added: {customer_record['name']} ({customer_record['email']})")
            return customer_id

        except Exception as e:
            print(f"❌ Error adding customer: {e}")
            return ""

    def assign_key_to_customer(self, license_key: str, customer_email: str) -> bool:
        """Assign license key to customer"""
        try:
            # Load databases
            enhanced_db = self.load_enhanced_database()
            with open(self.customers_file, 'r', encoding='utf-8') as f:
                customers_db = json.load(f)

            # Find customer
            customer = None
            for c in customers_db["customers"]:
                if c["email"].lower() == customer_email.lower():
                    customer = c
                    break

            if not customer:
                print(f"❌ Customer not found: {customer_email}")
                return False

            # Find license key
            key_data = None
            for key in enhanced_db["keys"]:
                if key["key"] == license_key:
                    key_data = key
                    break

            if not key_data:
                print(f"❌ License key not found: {license_key}")
                return False

            # Assign key to customer
            key_data["customer_id"] = customer["id"]
            key_data["customer_email"] = customer["email"]
            key_data["assigned_at"] = datetime.datetime.now().isoformat()
            key_data["status"] = "assigned"

            # Add key to customer record
            customer["license_keys"].append({
                "key": license_key,
                "assigned_at": datetime.datetime.now().isoformat(),
                "type": key_data["type"],
                "price": key_data["price"]
            })

            # Update customer total spent
            customer["total_spent"] += key_data.get("price", 0.0)
            customer["last_contact"] = datetime.datetime.now().isoformat()

            # Save databases
            self.save_enhanced_database(enhanced_db)
            with open(self.customers_file, 'w', encoding='utf-8') as f:
                json.dump(customers_db, f, indent=2, ensure_ascii=False)

            print(f"✅ Key {license_key} assigned to {customer['name']} ({customer['email']})")
            return True

        except Exception as e:
            print(f"❌ Error assigning key: {e}")
            return False

    def send_key_to_customer(self, license_key: str, customer_email: str, customer_name: str = "") -> bool:
        """Send license key to customer via email"""
        if not self.email_config.get("enabled", False):
            print("❌ Email system not configured")
            return False

        try:
            # Get key data
            enhanced_db = self.load_enhanced_database()
            key_data = None
            for key in enhanced_db["keys"]:
                if key["key"] == license_key:
                    key_data = key
                    break

            if not key_data:
                print(f"❌ License key not found: {license_key}")
                return False

            # Generate email content
            subject = f"🎯 Your ClausoNet 4.0 Pro License Key - {key_data['type'].title()}"

            body = f"""
Dear {customer_name or 'Valued Customer'},

Thank you for your purchase of ClausoNet 4.0 Pro!

🔑 YOUR LICENSE KEY: {license_key}

📋 LICENSE DETAILS:
• Type: {key_data['type'].title()}
• Duration: {key_data['duration_days']} days
• Max Devices: {key_data['max_devices']}
• Expires: {key_data['expiry_date'][:10]}
• Price: ${key_data['price']:.2f}

🚀 ACTIVATION INSTRUCTIONS:
1. Download ClausoNet 4.0 Pro from our website
2. Run the application
3. When prompted, enter your license key: {license_key}
4. The application will automatically activate your license

✨ FEATURES INCLUDED:
"""

            for feature in key_data.get('features', []):
                body += f"• {feature.replace('_', ' ').title()}\n"

            body += f"""

📞 SUPPORT:
If you need any assistance, please don't hesitate to contact us.

Best regards,
ClausoNet Team

Note: Please keep this email safe as it contains your license key.
"""

            # Send email
            msg = MimeMultipart()
            msg['From'] = self.email_config['admin_email']
            msg['To'] = customer_email
            msg['Subject'] = subject

            msg.attach(MimeText(body, 'plain'))

            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['admin_email'], self.email_config['admin_password'])

            text = msg.as_string()
            server.sendmail(self.email_config['admin_email'], customer_email, text)
            server.quit()

            # Log email sent
            self.log_activation_attempt(license_key, "email_sent", {
                "customer_email": customer_email,
                "customer_name": customer_name,
                "sent_at": datetime.datetime.now().isoformat()
            })

            print(f"✅ Email sent to {customer_email}")
            return True

        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False

    def log_activation_attempt(self, license_key: str, event_type: str, data: Dict):
        """Log activation attempts and events"""
        try:
            with open(self.activation_log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)

            log_entry = {
                "license_key": license_key,
                "event_type": event_type,
                "timestamp": datetime.datetime.now().isoformat(),
                "data": data
            }

            if event_type == "activation_success":
                log_data["activations"].append(log_entry)
            elif event_type == "activation_failed":
                log_data["failed_attempts"].append(log_entry)
            else:
                # General events (email_sent, key_assigned, etc.)
                if "events" not in log_data:
                    log_data["events"] = []
                log_data["events"].append(log_entry)

            # Update analytics
            log_data["analytics"]["total_attempts"] += 1

            with open(self.activation_log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Error logging activation: {e}")

    def validate_license_for_user(self, license_key: str, hardware_id: str) -> Dict:
        """Validate license for end user activation"""
        try:
            enhanced_db = self.load_enhanced_database()

            # Find license key
            key_data = None
            for key in enhanced_db["keys"]:
                if key["key"] == license_key:
                    key_data = key
                    break

            if not key_data:
                return {
                    "valid": False,
                    "error": "License key not found",
                    "error_code": "KEY_NOT_FOUND"
                }

            # Check if already activated on different hardware
            if key_data.get("status") == "activated":
                existing_hardware_ids = key_data.get("hardware_ids", [])
                if hardware_id not in existing_hardware_ids:
                    if len(existing_hardware_ids) >= key_data.get("max_devices", 1):
                        return {
                            "valid": False,
                            "error": "License already activated on maximum number of devices",
                            "error_code": "MAX_DEVICES_EXCEEDED"
                        }

            # Check expiry
            expiry_str = key_data.get("expiry_date", "")
            if expiry_str:
                try:
                    expiry_date = datetime.datetime.fromisoformat(expiry_str.replace('Z', ''))
                    if datetime.datetime.now() > expiry_date:
                        return {
                            "valid": False,
                            "error": "License has expired",
                            "error_code": "LICENSE_EXPIRED"
                        }
                except:
                    pass

            # Valid license
            return {
                "valid": True,
                "key_data": key_data,
                "message": "License is valid"
            }

        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}",
                "error_code": "VALIDATION_ERROR"
            }

    def activate_license_for_user(self, license_key: str, hardware_id: str) -> Dict:
        """Activate license for end user"""
        try:
            # First validate
            validation_result = self.validate_license_for_user(license_key, hardware_id)
            if not validation_result["valid"]:
                self.log_activation_attempt(license_key, "activation_failed", {
                    "hardware_id": hardware_id,
                    "error": validation_result["error"],
                    "error_code": validation_result["error_code"]
                })
                return validation_result

            # Activate license
            enhanced_db = self.load_enhanced_database()
            key_data = validation_result["key_data"]

            # Update key data
            if "hardware_ids" not in key_data:
                key_data["hardware_ids"] = []

            if hardware_id not in key_data["hardware_ids"]:
                key_data["hardware_ids"].append(hardware_id)

            key_data["status"] = "activated"
            key_data["activated_at"] = datetime.datetime.now().isoformat()
            key_data["activation_count"] = key_data.get("activation_count", 0) + 1

            # Save database
            self.save_enhanced_database(enhanced_db)

            # Create user license file
            self.create_user_license_file(license_key, hardware_id, key_data)

            # Log successful activation
            self.log_activation_attempt(license_key, "activation_success", {
                "hardware_id": hardware_id,
                "activated_at": datetime.datetime.now().isoformat(),
                "key_type": key_data["type"]
            })

            print(f"✅ License {license_key} activated for hardware {hardware_id[:20]}...")

            return {
                "valid": True,
                "activated": True,
                "message": "License activated successfully",
                "key_data": key_data
            }

        except Exception as e:
            error_msg = f"Activation error: {str(e)}"
            self.log_activation_attempt(license_key, "activation_failed", {
                "hardware_id": hardware_id,
                "error": error_msg,
                "error_code": "ACTIVATION_ERROR"
            })
            return {
                "valid": False,
                "error": error_msg,
                "error_code": "ACTIVATION_ERROR"
            }

    def create_user_license_file(self, license_key: str, hardware_id: str, key_data: Dict):
        """Create user license file for end user"""
        try:
            user_license_data = {
                "license_key": license_key,
                "hardware_id": hardware_id,
                "activation_date": datetime.datetime.now().isoformat(),
                "expiry_date": key_data["expiry_date"],
                "key_type": key_data["type"],
                "features": key_data.get("features", []),
                "max_devices": key_data.get("max_devices", 1),
                "customer_info": {
                    "customer_id": key_data.get("customer_id", ""),
                    "customer_email": key_data.get("customer_email", "")
                }
            }

            # Save to admin data for tracking
            user_license_file = self.admin_data_path / f"user_license_{hardware_id[:10]}.json"
            with open(user_license_file, 'w', encoding='utf-8') as f:
                json.dump(user_license_data, f, indent=2, ensure_ascii=False)

            print(f"✅ User license file created: {user_license_file}")

        except Exception as e:
            print(f"Error creating user license file: {e}")

    def get_license_statistics(self) -> Dict:
        """Get comprehensive license statistics"""
        try:
            enhanced_db = self.load_enhanced_database()

            with open(self.customers_file, 'r', encoding='utf-8') as f:
                customers_db = json.load(f)

            with open(self.activation_log_file, 'r', encoding='utf-8') as f:
                activation_log = json.load(f)

            # Calculate statistics
            total_keys = len(enhanced_db.get("keys", []))
            total_customers = len(customers_db.get("customers", []))

            # Count by type
            key_types = {}
            activated_keys = 0
            total_revenue = 0.0

            for key in enhanced_db.get("keys", []):
                key_type = key.get("type", "unknown")
                key_types[key_type] = key_types.get(key_type, 0) + 1

                if key.get("status") == "activated":
                    activated_keys += 1

                total_revenue += key.get("price", 0.0)

            # Activation statistics
            total_activations = len(activation_log.get("activations", []))
            failed_activations = len(activation_log.get("failed_attempts", []))

            success_rate = 0.0
            if total_activations + failed_activations > 0:
                success_rate = (total_activations / (total_activations + failed_activations)) * 100

            return {
                "total_keys": total_keys,
                "total_customers": total_customers,
                "activated_keys": activated_keys,
                "total_revenue": total_revenue,
                "key_types": key_types,
                "total_activations": total_activations,
                "failed_activations": failed_activations,
                "success_rate": success_rate,
                "activation_rate": (activated_keys / total_keys * 100) if total_keys > 0 else 0.0
            }

        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}

# Integration function for main_window.py
def integrate_with_main_window():
    """
    Integration point for main_window.py
    This function should be called from main_window.py to use enhanced admin system
    """
    return EnhancedAdminLicenseSystem()

if __name__ == "__main__":
    # Test the enhanced system
    admin_system = EnhancedAdminLicenseSystem()

    # Example usage
    print("🎯 ClausoNet 4.0 Pro - Enhanced Admin License System")
    print("=" * 60)

    # Get statistics
    stats = admin_system.get_license_statistics()
    print(f"📊 Statistics: {stats}")
