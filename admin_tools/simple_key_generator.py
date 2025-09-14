#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Admin Key Generator
Standalone tool for admin to generate license keys for customers
"""

import os
import json
import random
import string
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

class SimpleKeyGenerator:
    """Standalone key generator for admin use"""
    
    def __init__(self):
        """Initialize admin key generator"""
        # Admin tool directory
        self.admin_dir = Path(__file__).parent
        
        # Check for admin_data directory (for deployed EXE)
        admin_data_dir = self.admin_dir / "admin_data"
        if admin_data_dir.exists():
            self.key_database = admin_data_dir / "license_database.json"
        else:
            # Fallback to old location
            self.key_database = self.admin_dir / "generated_keys.json"
        
        # Create database if not exists
        if not self.key_database.exists():
            # Ensure directory exists
            self.key_database.parent.mkdir(exist_ok=True)
            self._create_empty_database()
            
    def _create_empty_database(self):
        """Create empty key database"""
        initial_data = {
            "metadata": {
                "created": datetime.now().isoformat(),
                "version": "1.0",
                "total_keys": 0
            },
            "keys": {}
        }
        
        with open(self.key_database, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)
            
    def generate_license_key(self, duration_days: int, customer_name: str = "", notes: str = "") -> str:
        """Generate a new license key with specified duration"""
        try:
            # Calculate expiry date
            expiry_date = datetime.now() + timedelta(days=duration_days)
            expiry_str = expiry_date.strftime("%Y%m%d")
            
            # Generate random components
            random_part1 = self._generate_random_string(5)
            random_part2 = self._generate_random_string(5)
            
            # Create base key without checksum
            base_key = f"CNPRO-{expiry_str}-{random_part1}-{random_part2}"
            
            # Generate simple checksum (last 2 chars)
            checksum = self._calculate_checksum(base_key)
            
            # Final key
            license_key = f"CNPRO-{expiry_str}-{random_part1}-{checksum}{random_part2[2:]}"
            
            # Save to database
            self._save_key_to_database(license_key, duration_days, customer_name, notes, expiry_date)
            
            return license_key
            
        except Exception as e:
            print(f"Key generation error: {e}")
            return None
            
    def _generate_random_string(self, length: int) -> str:
        """Generate random alphanumeric string"""
        chars = string.ascii_uppercase + string.digits
        # Exclude confusing characters
        chars = chars.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
        return ''.join(random.choice(chars) for _ in range(length))
        
    def _calculate_checksum(self, base_key: str) -> str:
        """Calculate simple checksum for key validation"""
        # Simple hash-based checksum
        hash_obj = hashlib.md5(base_key.encode())
        hex_digest = hash_obj.hexdigest()
        
        # Take first 2 chars and convert to alphanumeric
        checksum_chars = []
        for char in hex_digest[:2]:
            if char.isdigit():
                # Convert digit to letter (0->A, 1->B, etc.)
                checksum_chars.append(chr(ord('A') + int(char)))
            else:
                # Keep letter uppercase
                checksum_chars.append(char.upper())
                
        return ''.join(checksum_chars)
        
    def _save_key_to_database(self, license_key: str, duration_days: int, customer_name: str, notes: str, expiry_date: datetime):
        """Save generated key to admin database"""
        try:
            # Load existing database
            with open(self.key_database, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Add new key
            key_info = {
                "created_date": datetime.now().isoformat(),
                "expiry_date": expiry_date.isoformat(),
                "duration_days": duration_days,
                "customer_name": customer_name,
                "notes": notes,
                "status": "generated"
            }
            
            data["keys"][license_key] = key_info
            data["metadata"]["total_keys"] = len(data["keys"])
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # Save back to file
            with open(self.key_database, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Database save error: {e}")
            
    def list_generated_keys(self, show_expired: bool = False) -> list:
        """List all generated keys"""
        try:
            with open(self.key_database, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            keys_list = []
            for license_key, info in data["keys"].items():
                expiry_date = datetime.fromisoformat(info["expiry_date"])
                is_expired = datetime.now() > expiry_date
                
                if not show_expired and is_expired:
                    continue
                    
                days_left = (expiry_date - datetime.now()).days
                
                key_summary = {
                    "license_key": license_key,
                    "customer_name": info.get("customer_name", ""),
                    "created_date": info["created_date"][:10],  # YYYY-MM-DD
                    "expiry_date": info["expiry_date"][:10],
                    "days_left": days_left,
                    "duration_days": info["duration_days"],
                    "is_expired": is_expired,
                    "notes": info.get("notes", "")
                }
                
                keys_list.append(key_summary)
                
            # Sort by creation date (newest first)
            keys_list.sort(key=lambda x: x["created_date"], reverse=True)
            return keys_list
            
        except Exception as e:
            print(f"List keys error: {e}")
            return []
            
    def validate_key_format(self, license_key: str) -> bool:
        """Validate if key follows correct format"""
        try:
            if not license_key or not license_key.startswith("CNPRO-"):
                return False
                
            parts = license_key.split("-")
            if len(parts) != 4:
                return False
                
            # Check date format
            try:
                datetime.strptime(parts[1], "%Y%m%d")
            except:
                return False
                
            # Check part lengths
            if len(parts[2]) != 5 or len(parts[3]) != 5:
                return False
                
            return True
            
        except Exception as e:
            print(f"Validation error: {e}")
            return False
            
    def get_database_stats(self) -> dict:
        """Get statistics about generated keys"""
        try:
            with open(self.key_database, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            total_keys = len(data["keys"])
            active_keys = 0
            expired_keys = 0
            
            for info in data["keys"].values():
                expiry_date = datetime.fromisoformat(info["expiry_date"])
                if datetime.now() > expiry_date:
                    expired_keys += 1
                else:
                    active_keys += 1
                    
            return {
                "total_keys": total_keys,
                "active_keys": active_keys,
                "expired_keys": expired_keys,
                "database_created": data["metadata"]["created"][:10]
            }
            
        except Exception as e:
            print(f"Stats error: {e}")
            return {"error": str(e)}
            
    def delete_license_key(self, license_key: str) -> bool:
        """Delete a license key from database"""
        try:
            with open(self.key_database, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if license_key not in data["keys"]:
                print(f"License key not found: {license_key}")
                return False
                
            # Remove the key
            del data["keys"][license_key]
            data["metadata"]["total_keys"] = len(data["keys"])
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # Save back to file
            with open(self.key_database, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            print(f"License key deleted successfully: {license_key}")
            return True
            
        except Exception as e:
            print(f"Delete key error: {e}")
            return False

# Quick test and demonstration
if __name__ == "__main__":
    print("=== ClausoNet 4.0 Pro - Admin Key Generator ===")
    
    generator = SimpleKeyGenerator()
    
    # Generate sample keys
    print("\n1. Generating sample keys...")
    
    # 30-day trial
    trial_key = generator.generate_license_key(30, "Test Customer 1", "30-day trial")
    print(f"Trial Key (30 days): {trial_key}")
    
    # 90-day license  
    quarterly_key = generator.generate_license_key(90, "Test Customer 2", "Quarterly license")
    print(f"Quarterly Key (90 days): {quarterly_key}")
    
    # 365-day license
    yearly_key = generator.generate_license_key(365, "Test Customer 3", "Yearly license")
    print(f"Yearly Key (365 days): {yearly_key}")
    
    # Show statistics
    print("\n2. Database Statistics:")
    stats = generator.get_database_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
        
    # List keys
    print("\n3. Generated Keys List:")
    keys_list = generator.list_generated_keys()
    for i, key_info in enumerate(keys_list[:3]):  # Show first 3
        print(f"   {i+1}. {key_info['license_key']} - {key_info['customer_name']} ({key_info['days_left']} days left)")
        
    print(f"\nDatabase file: {generator.key_database}")
    print("=== Key Generation Complete ===") 