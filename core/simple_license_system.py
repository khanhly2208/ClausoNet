#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Simple License System
Simplified license system for end users - NO admin database required
"""

import os
import json
import hashlib
import platform
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import random
import string

class SimpleLicenseSystem:
    """Simplified license system for end users"""
    
    def __init__(self):
        """Initialize simple license system"""
        # User data directory only - NO admin data needed
        self.user_data_dir = Path.home() / "AppData" / "Local" / "ClausoNet4.0"
        self.license_file = self.user_data_dir / "user_license.json"
        
        # Create user data directory
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        
    def check_local_license(self) -> bool:
        """Check local license file only - NO server needed"""
        try:
            if not self.license_file.exists():
                return False
                
            with open(self.license_file, 'r', encoding='utf-8') as f:
                license_data = json.load(f)
                
            # Check hardware binding
            if license_data.get('hardware_id') != self.get_simple_hardware_id():
                return False
                
            # Check expiry
            expiry_str = license_data.get('expiry_date', '')
            if expiry_str:
                try:
                    if 'T' in expiry_str:
                        expiry_date = datetime.fromisoformat(expiry_str.replace('Z', ''))
                    else:
                        expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
                        
                    if datetime.now() > expiry_date:
                        return False  # Expired
                except:
                    return False  # Invalid date format
                    
            return True
            
        except Exception as e:
            print(f"License check error: {e}")
            return False
            
    def activate_license(self, license_key: str) -> bool:
        """Offline activation - create license file from key"""
        try:
            if not self.validate_key_format(license_key):
                return False
                
            license_data = self.create_license_from_key(license_key)
            if not license_data:
                return False
                
            # Save license file
            with open(self.license_file, 'w', encoding='utf-8') as f:
                json.dump(license_data, f, indent=2, ensure_ascii=False)
                
            return True
            
        except Exception as e:
            print(f"License activation error: {e}")
            return False
            
    def validate_key_format(self, license_key: str) -> bool:
        """Validate license key format: CNPRO-YYYYMMDD-XXXXX-YYYYY"""
        try:
            if not license_key or not license_key.startswith("CNPRO-"):
                return False
                
            # Normalize key
            license_key = license_key.strip().upper()
            parts = license_key.split("-")
            
            if len(parts) != 4:
                return False
                
            # Check expiry date format (YYYYMMDD)
            try:
                expiry_date = datetime.strptime(parts[1], "%Y%m%d")
                if datetime.now() > expiry_date:
                    return False  # Expired key
            except:
                return False
                
            # Basic checksum validation (optional)
            return True
            
        except Exception as e:
            print(f"Key validation error: {e}")
            return False
            
    def create_license_from_key(self, license_key: str) -> dict:
        """Create license data from key"""
        try:
            parts = license_key.split("-")
            expiry_date_str = parts[1]  # YYYYMMDD
            
            # Parse expiry date
            expiry_date = datetime.strptime(expiry_date_str, "%Y%m%d")
            expiry_date = expiry_date.replace(hour=23, minute=59, second=59)
            
            # Determine license type based on expiry
            days_from_now = (expiry_date - datetime.now()).days
            if days_from_now <= 30:
                license_type = "trial"
            elif days_from_now <= 90:
                license_type = "monthly"  
            elif days_from_now <= 365:
                license_type = "quarterly"
            else:
                license_type = "lifetime"
                
            license_data = {
                "license_key": license_key,
                "activation_date": datetime.now().isoformat(),
                "hardware_id": self.get_simple_hardware_id(),
                "expiry_date": expiry_date.isoformat(),
                "license_type": license_type,
                "status": "active",
                "app_version": "4.0.1"
            }
            
            return license_data
            
        except Exception as e:
            print(f"License creation error: {e}")
            return None
            
    def get_simple_hardware_id(self) -> str:
        """Simple hardware ID generation"""
        try:
            # Use basic system info - simple but effective
            cpu_info = platform.processor()[:20] if platform.processor() else "unknown_cpu"
            mac_address = str(uuid.getnode())
            system_info = platform.system()
            
            # Simple combination
            combined = f"{cpu_info}_{mac_address}_{system_info}"
            
            # Generate MD5 hash (first 16 chars)
            hardware_id = hashlib.md5(combined.encode()).hexdigest()[:16]
            return hardware_id
            
        except Exception as e:
            print(f"Hardware ID error: {e}")
            return "default_hardware_id"
            
    def get_license_info(self) -> dict:
        """Get current license information"""
        try:
            if not self.license_file.exists():
                return {"status": "no_license", "message": "No license found"}
                
            with open(self.license_file, 'r', encoding='utf-8') as f:
                license_data = json.load(f)
                
            # Check if valid
            is_valid = self.check_local_license()
            
            if is_valid:
                expiry_date = datetime.fromisoformat(license_data['expiry_date'])
                days_left = (expiry_date - datetime.now()).days
                
                return {
                    "status": "active",
                    "license_type": license_data.get('license_type', 'unknown'),
                    "expiry_date": license_data.get('expiry_date', ''),
                    "days_left": days_left,
                    "activation_date": license_data.get('activation_date', '')
                }
            else:
                return {"status": "invalid", "message": "License invalid or expired"}
                
        except Exception as e:
            return {"status": "error", "message": f"License check error: {e}"}
            
    def is_license_expiring_soon(self, days_threshold: int = 7) -> bool:
        """Check if license is expiring soon"""
        try:
            license_info = self.get_license_info()
            if license_info["status"] == "active":
                days_left = license_info.get("days_left", 0)
                return days_left <= days_threshold
            return False
        except:
            return False 