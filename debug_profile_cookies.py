#!/usr/bin/env python3
"""
Debug script to check profile and cookies status
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.profile_manager import ChromeProfileManager
from utils.resource_manager import resource_manager

def debug_profile_cookies():
    """Debug profile and cookies status"""
    print("🔍 ClausoNet 4.0 Pro - Profile & Cookies Debug")
    print("=" * 60)
    
    try:
        # Initialize profile manager
        profile_manager = ChromeProfileManager()
        
        print(f"📁 Profile directory: {profile_manager.base_profile_dir}")
        print(f"🔧 Profile directory exists: {profile_manager.base_profile_dir.exists()}")
        print(f"🎯 Is frozen (exe mode): {profile_manager.is_frozen}")
        
        # List all profiles
        profiles = profile_manager.list_profiles()
        print(f"\n📋 Found {len(profiles)} profiles:")
        for i, profile in enumerate(profiles):
            print(f"   {i+1}. {profile}")
        
        if not profiles:
            print("❌ No profiles found!")
            return
        
        # Check each profile for cookies
        print(f"\n🍪 Cookie Status:")
        print("-" * 40)
        
        # Check both paths for cookies
        for profile_name in profiles:
            print(f"\n🔍 Profile: {profile_name}")
            
            # Check profile directory structure
            profile_dir = profile_manager.base_profile_dir / profile_name
            default_dir = profile_dir / "Default"
            cookies_db = default_dir / "Cookies"
            
            print(f"   📂 Profile dir exists: {profile_dir.exists()}")
            print(f"   📂 Default dir exists: {default_dir.exists()}")
            print(f"   🍪 Chrome Cookies DB exists: {cookies_db.exists()}")
            
            if cookies_db.exists():
                size = cookies_db.stat().st_size
                print(f"       Size: {size} bytes")
            
            # Check extracted JSON cookies (ResourceManager path)
            try:
                from utils.resource_manager import resource_manager
                cookies_dir = Path(resource_manager.data_dir) / "profile_cookies"
                cookies_json = cookies_dir / f"{profile_name}.json"
                
                print(f"   📁 Cookies dir: {cookies_dir}")
                print(f"   📁 Cookies dir exists: {cookies_dir.exists()}")
                print(f"   📄 JSON cookies file: {cookies_json}")
                print(f"   📄 JSON cookies exists: {cookies_json.exists()}")
                
                if cookies_json.exists():
                    size = cookies_json.stat().st_size
                    print(f"       Size: {size} bytes")
                    
                    # Try to read content
                    try:
                        with open(cookies_json, 'r', encoding='utf-8') as f:
                            content = f.read()
                            print(f"       Content length: {len(content)} chars")
                            if len(content) > 100:
                                print(f"       Sample: {content[:100]}...")
                            else:
                                print(f"       Content: {content}")
                    except Exception as e:
                        print(f"       ❌ Read error: {e}")
                        
            except Exception as e:
                print(f"   ❌ ResourceManager error: {e}")
            
            # Also check fallback path
            fallback_cookies = Path("data/profile_cookies") / f"{profile_name}.json"
            print(f"   📄 Fallback cookies: {fallback_cookies}")
            print(f"   📄 Fallback exists: {fallback_cookies.exists()}")
        
        # Test cookie availability check (same as in main_window.py)
        print(f"\n🧪 Testing workflow cookie detection:")
        print("-" * 50)
        
        for profile_name in profiles:
            print(f"\n🔍 Testing profile: {profile_name}")
            
            # Simulate the check from run_video_generation
            try:
                from utils.resource_manager import resource_manager
                cookies_dir = Path(resource_manager.data_dir) / "profile_cookies"
                cookies_file = cookies_dir / f"{profile_name}.json"
            except ImportError:
                cookies_file = Path(f"data/profile_cookies/{profile_name}.json")
            
            cookies_available = cookies_file.exists()
            
            print(f"   📄 Checking: {cookies_file}")
            print(f"   ✅ Available: {cookies_available}")
            
            if cookies_available:
                print(f"   🎯 Mode would be: FULL_AUTOMATION")
            else:
                print(f"   🎯 Mode would be: PROMPT_WITH_CHROME")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_profile_cookies()
    
    print("\n" + "=" * 60)
    print("💡 Troubleshooting Tips:")
    print("1. If no JSON cookies found, you need to extract cookies from Chrome profile")
    print("2. Open Settings tab → Select profile → Click 'Extract Cookies'")
    print("3. Or login to Google Veo using the profile first")
    print("4. Check that profile was created in correct directory for exe mode")
    print("\n✅ Debug complete!")
