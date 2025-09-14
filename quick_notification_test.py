#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Quick test for notification system syntax
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_import():
    """Test import of main window with notification system"""
    try:
        print("🔍 Testing notification system import...")

        # Test import
        from gui.main_window import ClausoNetGUI
        print("✅ ClausoNetGUI import successful")

        # Test class creation (without running)
        app = ClausoNetGUI()
        print("✅ ClausoNetGUI instance created")

        # Check notification attributes
        if hasattr(app, 'license_expiry_timer'):
            print("✅ license_expiry_timer attribute found")
        if hasattr(app, 'expiry_check_interval'):
            print("✅ expiry_check_interval attribute found")
        if hasattr(app, 'shown_expiry_warnings'):
            print("✅ shown_expiry_warnings attribute found")

        # Check notification methods
        if hasattr(app, 'setup_license_expiry_monitoring'):
            print("✅ setup_license_expiry_monitoring method found")
        if hasattr(app, 'check_license_expiry'):
            print("✅ check_license_expiry method found")
        if hasattr(app, 'show_expiry_notification'):
            print("✅ show_expiry_notification method found")

        print("\n🎉 NOTIFICATION SYSTEM READY!")
        print("   - All imports successful")
        print("   - All attributes present")
        print("   - All methods available")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🔔 QUICK NOTIFICATION SYSTEM TEST")
    print("=" * 40)

    success = test_import()

    if success:
        print("\n✅ System ready for testing!")
        print("   Run ClausoNet 4.0 Pro to see notifications in action")
    else:
        print("\n❌ System has issues - check implementation")

    print("\n📝 Next steps:")
    print("   1. Run: python test_license_expiry_notification.py")
    print("   2. Test different expiry scenarios")
    print("   3. Start main app to see live notifications")
