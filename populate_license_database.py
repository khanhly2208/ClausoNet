#!/usr/bin/env python3
"""
Script to populate license database with test keys for cross-machine testing
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from admin_tools.license_key_generator import LicenseKeyGenerator

def populate_database():
    """Populate license database with test keys"""
    print("🔑 Populating license database...")
    
    try:
        # Initialize license generator
        license_gen = LicenseKeyGenerator()
        
        print(f"📁 Database path: {license_gen.license_database_path}")
        print(f"📊 Current database has {len(license_gen.database['keys'])} keys")
        
        # Create several test license keys for different scenarios
        test_licenses = [
            # Keys that the user mentioned in log
            {
                'key': 'CNPRO-DZGJ-TOYE-C34N-EVR0',
                'type': 'professional',
                'customer_name': 'Test User 1',
                'customer_email': 'test1@example.com'
            },
            {
                'key': 'CNPRO-AE4I-KEWQ-KLGG-4L4Q', 
                'type': 'professional',
                'customer_name': 'Test User 2',
                'customer_email': 'test2@example.com'
            },
            # Additional test keys
            {
                'key': 'CNPRO-TEST-1234-ABCD-PROF',
                'type': 'professional',
                'customer_name': 'Test Professional',
                'customer_email': 'prof@example.com'
            },
            {
                'key': 'CNPRO-TRIA-L123-7DAY-S001',
                'type': 'trial',
                'customer_name': 'Trial User',
                'customer_email': 'trial@example.com'
            },
            {
                'key': 'CNPRO-LIFE-TIME-UNLM-LTIM',
                'type': 'lifetime',
                'customer_name': 'Lifetime User',
                'customer_email': 'lifetime@example.com'
            }
        ]
        
        # Add each license to database
        for license_info in test_licenses:
            try:
                # Check if key already exists
                key_exists = False
                for existing_key in license_gen.database['keys']:
                    if existing_key['key'] == license_info['key']:
                        key_exists = True
                        break
                
                if key_exists:
                    print(f"⚠️  Key already exists: {license_info['key']}")
                    continue
                
                # Create license data
                from datetime import datetime, timedelta
                
                # Set duration based on type
                if license_info['type'] == 'trial':
                    expiry_date = datetime.utcnow() + timedelta(days=7)
                    features = ['basic_generation', 'limited_workflows']
                    max_devices = 1
                    price = 0.0
                elif license_info['type'] == 'professional':
                    expiry_date = datetime.utcnow() + timedelta(days=365)  # 1 year
                    features = ['ai_generation', 'unlimited_workflows', 'api_access', 'priority_support']
                    max_devices = 3
                    price = 299.0
                elif license_info['type'] == 'lifetime':
                    expiry_date = datetime.utcnow() + timedelta(days=365*50)  # 50 years
                    features = ['ai_generation', 'unlimited_workflows', 'api_access', 'priority_support', 'lifetime_updates']
                    max_devices = 5
                    price = 999.0
                else:
                    expiry_date = datetime.utcnow() + timedelta(days=30)
                    features = ['basic_generation']
                    max_devices = 1
                    price = 29.0
                
                license_data = {
                    'key': license_info['key'],
                    'type': license_info['type'],
                    'license_format': 'CNPRO',
                    'admin_type': license_info['type'],
                    'duration_days': 365 if license_info['type'] != 'trial' else 7,
                    'max_devices': max_devices,
                    'features': features,
                    'expiry_date': expiry_date.isoformat(),
                    'created_at': datetime.utcnow().isoformat(),
                    'status': 'generated',  # Not activated yet
                    'activation_count': 0,
                    'hardware_ids': [],  # Empty - can be activated on any machine
                    'customer_info': {
                        'name': license_info['customer_name'],
                        'email': license_info['customer_email']
                    },
                    'price': price,
                    'currency': 'USD'
                }
                
                # Add to database
                license_gen.database['keys'].append(license_data)
                
                # Update statistics
                license_gen.database['statistics']['total_keys_generated'] += 1
                if license_info['type'] == 'trial':
                    license_gen.database['statistics']['trial_keys'] += 1
                elif license_info['type'] == 'professional':
                    license_gen.database['statistics']['professional_keys'] = license_gen.database['statistics'].get('professional_keys', 0) + 1
                elif license_info['type'] == 'lifetime':
                    license_gen.database['statistics']['lifetime_keys'] += 1
                
                print(f"✅ Added: {license_info['key']} ({license_info['type']})")
                
            except Exception as e:
                print(f"❌ Error adding {license_info['key']}: {e}")
        
        # Save database
        license_gen.save_database()
        
        print(f"\n📊 Database now has {len(license_gen.database['keys'])} keys")
        print("✅ Database populated successfully!")
        
        # Print summary
        print("\n📋 Available License Keys:")
        print("=" * 50)
        for key_data in license_gen.database['keys']:
            print(f"🔑 {key_data['key']} - {key_data['type']} ({key_data['customer_info']['name']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        return False

def test_activation():
    """Test activation of one of the keys"""
    print("\n🧪 Testing license activation...")
    
    try:
        license_gen = LicenseKeyGenerator()
        
        # Try to activate one of the keys we just created
        test_key = 'CNPRO-AE4I-KEWQ-KLGG-4L4Q'
        
        print(f"🔑 Testing activation of key: {test_key}")
        
        # Test activation
        result = license_gen.activate_license(test_key)
        
        if result:
            print(f"✅ Activation successful!")
        else:
            print(f"❌ Activation failed!")
        
        return result
        
    except Exception as e:
        print(f"❌ Activation test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ClausoNet 4.0 Pro - License Database Populator")
    print("=" * 60)
    
    # Populate database
    if populate_database():
        # Test activation
        test_activation()
    
    print("\n✅ Script complete!")
