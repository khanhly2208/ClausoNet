#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Chrome Profile Manager
Quản lý Chrome profiles cho việc đăng nhập Google Veo
"""

import os
import subprocess
import json
import sqlite3
import shutil
import platform
import sys
from pathlib import Path
from tkinter import messagebox
import time
import threading
import requests
from urllib.parse import unquote
from .cdp_client import CDPClient

class ChromeProfileManager:
    def __init__(self):
        # 🎯 NEW: Sử dụng ResourceManager cho exe compatibility
        try:
            from .resource_manager import resource_manager
            # Use ResourceManager's chrome_profiles_dir (user writable location)
            self.base_profile_dir = Path(resource_manager.chrome_profiles_dir)
            print(f"✅ Using ResourceManager profile directory: {self.base_profile_dir}")
        except ImportError:
            # Fallback for old behavior if ResourceManager not available
            print("⚠️ ResourceManager not available, using legacy path")
            current_script_dir = Path(__file__).parent.parent  # utils -> ClausoNet4.0
            self.base_profile_dir = current_script_dir / "chrome_profiles"
        
        # Detect if running from exe (frozen)
        self.is_frozen = getattr(sys, 'frozen', False)
        
        # Override for exe mode - ALWAYS use user data directory
        if self.is_frozen:
            print("🔧 EXE MODE: Using user data directory for profiles")
            system = platform.system()
            if system == "Windows":
                user_data_dir = Path.home() / "AppData" / "Local" / "ClausoNet4.0"
            elif system == "Darwin":  # macOS
                user_data_dir = Path.home() / "Library" / "Application Support" / "ClausoNet4.0"
            else:  # Linux
                user_data_dir = Path.home() / ".local" / "share" / "ClausoNet4.0"
            
            self.base_profile_dir = user_data_dir / "chrome_profiles"
            print(f"🎯 EXE mode profile directory: {self.base_profile_dir}")
        
        self.base_profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize CDP client
        self.cdp_client = CDPClient(port=9222)
        
        # Chrome executable paths for different OS
        self.chrome_paths = {
            "Windows": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', ''))
            ],
            "Darwin": [  # macOS
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            ],
            "Linux": [
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser"
            ]
        }
        
        # Google Veo login URL
        self.veo_login_url = "https://labs.google/fx/vi/tools/flow"
    
    def find_chrome_executable(self):
        """Tìm Chrome executable"""
        system = platform.system()
        paths = self.chrome_paths.get(system, [])
        
        for path in paths:
            if os.path.exists(path):
                return path
        
        # Try common commands
        try:
            result = subprocess.run(['which', 'google-chrome'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
            
        try:
            result = subprocess.run(['which', 'chromium'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return None
    
    def create_profile(self, profile_name):
        """Tạo Chrome profile mới"""
        try:
            # Validate profile name
            if not profile_name or not profile_name.strip():
                raise ValueError("Profile name cannot be empty")
            
            profile_name = profile_name.strip()
            profile_dir = self.base_profile_dir / profile_name
            
            # Check if profile already exists
            if profile_dir.exists():
                raise ValueError(f"Profile '{profile_name}' already exists")
            
            # Create profile directory
            profile_dir.mkdir(parents=True)
            
            # Create basic Chrome profile structure
            default_dir = profile_dir / "Default"
            default_dir.mkdir(exist_ok=True)
            
            # Create essential Chrome profile files
            
            # 1. Preferences file
            preferences = {
                "profile": {
                    "name": profile_name,
                    "managed_user_id": "",
                    "default_content_setting_values": {
                        "notifications": 2,
                        "popups": 2
                    },
                    "content_settings": {
                        "exceptions": {}
                    }
                },
                "browser": {
                    "show_home_button": True,
                    "check_default_browser": False
                },
                "sync": {
                    "suppress_start": True
                },
                "first_run_tabs": [self.veo_login_url]
            }
            
            with open(default_dir / "Preferences", 'w') as f:
                json.dump(preferences, f, indent=2)
            
            # 2. Local State file for the profile  
            local_state = {
                "profile": {
                    "info_cache": {
                        "Default": {
                            "name": profile_name,
                            "is_using_default_name": False,
                            "is_using_default_avatar": True,
                            "avatar_icon": "chrome://theme/IDR_PROFILE_AVATAR_0"
                        }
                    },
                    "last_used": "Default",
                    "profiles_created": 1
                }
            }
            
            with open(profile_dir / "Local State", 'w') as f:
                json.dump(local_state, f, indent=2)
            
            # 3. First Run file to prevent setup wizard
            with open(default_dir / "First Run", 'w') as f:
                f.write("")
            
            return str(profile_dir)
            
        except Exception as e:
            raise Exception(f"Failed to create profile: {str(e)}")
    
    def launch_chrome_with_profile(self, profile_name, open_veo_login=True, use_cdp=True):
        """Mở Chrome với profile cụ thể - CDP mode cho real-time cookies"""
        try:
            chrome_exe = self.find_chrome_executable()
            if not chrome_exe:
                raise Exception("Chrome executable not found. Please install Google Chrome.")
            
            profile_dir = self.base_profile_dir / profile_name
            if not profile_dir.exists():
                raise Exception(f"Profile '{profile_name}' does not exist")
            
            if use_cdp:
                # Use CDP for real-time cookie extraction
                veo_url = self.veo_login_url if open_veo_login else None
                process = self.cdp_client.start_chrome_with_debug(
                    chrome_exe, 
                    str(profile_dir.absolute()), 
                    veo_url
                )
                
                # Wait for Chrome to be ready for CDP
                time.sleep(3)
                self.cdp_client.connect()
                
                return process
            else:
                # Legacy file-based approach (fallback)
                absolute_profile_path = profile_dir.absolute()
                # Close any existing Chrome processes first
                try:
                    subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(2)  # Wait for processes to close
                except:
                    pass
                
                # Use minimal arguments to allow cookies saving
                args = [
                    chrome_exe,
                    f"--user-data-dir={absolute_profile_path}",
                    "--profile-directory=Default",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-features=TranslateUI,ChromeAccountManagement",
                    "--disable-default-apps",
                    "--disable-component-update",
                    "--new-window"
                ]
                
                # Add URL if needed
                if open_veo_login:
                    args.append(self.veo_login_url)
                
                # Launch Chrome
                process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                return process
            
        except Exception as e:
            raise Exception(f"Failed to launch Chrome: {str(e)}")
    
    def extract_cookies_from_profile(self, profile_name):
        """Trích xuất cookies từ Chrome profile"""
        debug_info = []
        try:
            profile_dir = self.base_profile_dir / profile_name
            cookies_db_path = profile_dir / "Default" / "Cookies"
            
            debug_info.append(f"🔍 DEBUG INFO:")
            debug_info.append(f"Profile dir: {profile_dir}")
            debug_info.append(f"Cookies DB path: {cookies_db_path}")
            debug_info.append(f"Profile dir exists: {profile_dir.exists()}")
            debug_info.append(f"Default dir exists: {(profile_dir / 'Default').exists()}")
            debug_info.append(f"Cookies DB exists: {cookies_db_path.exists()}")
            
            if cookies_db_path.exists():
                debug_info.append(f"Cookies DB size: {cookies_db_path.stat().st_size} bytes")
            
            # List all files in Default directory
            default_dir = profile_dir / "Default"
            if default_dir.exists():
                debug_info.append(f"Files in Default directory:")
                for file in default_dir.iterdir():
                    debug_info.append(f"  - {file.name} ({file.stat().st_size} bytes)")
            
            if not cookies_db_path.exists():
                debug_output = "\n".join(debug_info)
                return f"❌ No cookies database found.\n\n{debug_output}\n\n🔍 This means:\n• Chrome hasn't saved any cookies yet\n• You may not have visited or logged into any websites\n• Profile needs to be used first\n\n📋 Please:\n1. Open Chrome with this profile\n2. Navigate to labs.google/fx/tools/flow\n3. Login with your Google account\n4. Browse a few pages to generate cookies\n5. Try extracting cookies again"
            
            # Copy cookies DB to temp location (Chrome locks the original)
            temp_cookies_path = profile_dir / "temp_cookies.db"
            shutil.copy2(cookies_db_path, temp_cookies_path)
            
            cookies_list = []
            
            try:
                # Connect to cookies database
                conn = sqlite3.connect(temp_cookies_path)
                cursor = conn.cursor()
                
                # Query cookies for Google Veo domains
                query = """
                SELECT name, value, host_key, path, expires_utc, is_secure, is_httponly 
                FROM cookies 
                WHERE host_key LIKE '%google.com%' OR host_key LIKE '%googleapis.com%' 
                   OR host_key LIKE '%labs.google%' OR host_key LIKE '%.google%'
                ORDER BY host_key, name
                """
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                debug_info.append(f"Found {len(rows)} total cookies in database")
                
                # Count critical Veo cookies
                critical_cookies = set()
                google_auth_cookies = set()
                
                cookie_objects = []
                
                for row in rows:
                    name, value, host_key, path, expires_utc, is_secure, is_httponly = row
                    debug_info.append(f"Cookie: {name} @ {host_key}")
                    
                    # Convert Chrome timestamp to Unix timestamp  
                    if expires_utc > 0:
                        # Chrome timestamp is microseconds since Jan 1, 1601
                        # Unix timestamp is seconds since Jan 1, 1970
                        unix_timestamp = (expires_utc / 1000000) - 11644473600
                    else:
                        unix_timestamp = 0
                    
                    # Create cookie object in JSON format (like screenshot)
                    cookie_obj = {
                        "name": name,
                        "value": value,
                        "domain": host_key,
                        "path": path,
                        "expiry": int(unix_timestamp) if unix_timestamp > 0 else None,
                        "secure": bool(is_secure),
                        "httpOnly": bool(is_httponly),
                        "sameSite": "Lax"  # Default for Google cookies
                    }
                    
                    cookie_objects.append(cookie_obj)
                    
                    # Track important cookies (traditional string for compatibility)
                    cookie_str = f"{name}={value}"
                    cookies_list.append(cookie_str)
                    
                    if 'session-token' in name or 'csrf-token' in name:
                        critical_cookies.add(name)
                    if 'email' in name.lower() or 'auth' in name.lower():
                        google_auth_cookies.add(name)
                
                conn.close()
                
                # Clean up temp file
                temp_cookies_path.unlink()
                
                if cookie_objects:
                    # Return JSON format (like in screenshot)
                    import json
                    result = json.dumps(cookie_objects, indent=2, ensure_ascii=False)
                    
                    debug_output = "\n".join(debug_info)
                    final_result = f"✅ SUCCESS! Extracted {len(cookie_objects)} cookies\n\n🔍 DEBUG INFO:\n{debug_output}\n\n📋 COOKIES (JSON Format):\n{result}"
                    
                    return final_result
                else:
                    debug_output = "\n".join(debug_info)
                    return f"❌ No Google cookies found.\n\n🔍 DEBUG INFO:\n{debug_output}\n\n💡 Please login to Google first and visit labs.google/fx/tools/flow"
                
            except Exception as e:
                if temp_cookies_path.exists():
                    temp_cookies_path.unlink()
                raise e
                
        except Exception as e:
            debug_output = "\n".join(debug_info) if debug_info else "No debug info available"
            return f"❌ Error extracting cookies: {str(e)}\n\n🔍 DEBUG INFO:\n{debug_output}"
    
    def get_profile_path(self, profile_name):
        """Lấy đường dẫn đầy đủ của profile"""
        return str(self.base_profile_dir / profile_name)
    
    def close_all_chrome_instances(self):
        """Đóng tất cả Chrome instances để tránh conflict"""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Windows":
                # Windows
                subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe'], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif system == "Darwin":  # macOS
                subprocess.run(['pkill', '-f', 'Google Chrome'], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif system == "Linux":
                subprocess.run(['pkill', '-f', 'chrome'], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            time.sleep(2)  # Wait for processes to close
            
        except Exception as e:
            print(f"⚠️ Could not close Chrome instances: {e}")
    
    def list_profiles(self):
        """Liệt kê tất cả profiles"""
        profiles = []
        if self.base_profile_dir.exists():
            for item in self.base_profile_dir.iterdir():
                if item.is_dir():
                    profiles.append(item.name)
        return sorted(profiles)
    
    def delete_profile(self, profile_name):
        """Xóa profile"""
        try:
            profile_dir = self.base_profile_dir / profile_name
            if profile_dir.exists():
                shutil.rmtree(profile_dir)
                return True
            return False
        except Exception as e:
            raise Exception(f"Failed to delete profile: {str(e)}")
    
    def extract_cookies_via_cdp(self, timeout=60):
        """Extract cookies real-time using Chrome DevTools Protocol"""
        try:
            # First verify CDP connection is ready
            import requests
            import time
            
            # Check if debug port is accessible
            for i in range(10):
                try:
                    response = requests.get(f"http://localhost:{self.cdp_client.port}/json", timeout=2)
                    if response.status_code == 200:
                        tabs = response.json()
                        if tabs:
                            print(f"✅ CDP ready with {len(tabs)} tabs")
                            break
                except:
                    pass
                time.sleep(1)
                print(f"⏳ Waiting for CDP... {i+1}/10")
            else:
                return {
                    "logged_in": False,
                    "method": "CDP (Real-time)",
                    "error": "Chrome debug port not accessible",
                    "cookies": "",
                    "debug_info": "❌ CDP port 9222 not ready after 10 seconds"
                }
            
            # Reconnect CDP client
            self.cdp_client.connect()
            
            # Extract cookies immediately (don't wait for login)
            target_urls = [
                "https://labs.google",
                "https://google.com", 
                "https://accounts.google.com",
                "https://googleapis.com"
            ]
            
            cookies = self.cdp_client.extract_cookies_sync(target_urls)
            
            # Check if we have authentication cookies
            auth_cookies = []
            critical_cookies = []
            
            for cookie in cookies:
                name = cookie.get('name', '')
                domain = cookie.get('domain', '')
                
                # Check for Google auth indicators
                if any(indicator in name for indicator in [
                    'SAPISID', 'SSID', 'HSID', 'APISID', 'SID',
                    'session-token', 'csrf-token', 'email'
                ]):
                    auth_cookies.append(cookie)
                
                # Check for Veo critical cookies
                if 'labs.google' in domain and any(indicator in name for indicator in [
                    'session-token', 'csrf-token', 'auth'
                ]):
                    critical_cookies.append(cookie)
            
            # Return result based on cookies found
            if cookies:
                import json
                cookies_json = json.dumps(cookies, indent=2, ensure_ascii=False)
                
                # Login detected if we have auth cookies OR any cookies from target domains
                is_logged_in = len(auth_cookies) > 0 or len(critical_cookies) > 0
                
                return {
                    "logged_in": is_logged_in,
                    "method": "CDP (Real-time)",
                    "total_cookies": len(cookies),
                    "auth_cookies": len(auth_cookies),
                    "critical_cookies": len(critical_cookies),
                    "cookies": cookies_json,
                    "debug_info": f"✅ CDP Success - Total: {len(cookies)}, Auth: {len(auth_cookies)}, Critical: {len(critical_cookies)}, Login: {is_logged_in}"
                }
            else:
                return {
                    "logged_in": False,
                    "method": "CDP (Real-time)",
                    "total_cookies": 0,
                    "auth_cookies": 0,
                    "critical_cookies": 0,
                    "cookies": "[]",
                    "debug_info": "🔄 CDP Connected but no cookies found - User may not be logged in yet"
                }
                
        except Exception as e:
            return {
                "logged_in": False,
                "method": "CDP (Real-time)",
                "error": str(e),
                "cookies": "",
                "debug_info": f"❌ CDP Exception: {str(e)}"
            }

    def check_profile_login_status(self, profile_name, use_cdp=True):
        """Kiểm tra trạng thái đăng nhập của profile - CDP or legacy"""
        
        if use_cdp:
            # Try CDP first (real-time approach)
            return self.extract_cookies_via_cdp()
        else:
            # Fallback to legacy file-based approach
            try:
                cookies = self.extract_cookies_from_profile(profile_name)
                
                # Check for both traditional Google auth cookies and Veo-specific cookies
                traditional_auth_indicators = [
                    "SAPISID", "SSID", "HSID", "APISID", 
                    "SID", "__Secure-3PAPISID", "__Secure-3PSID"
                ]
                
                # Veo-specific cookies (from your curl example)
                veo_auth_indicators = [
                    "__Secure-next-auth.session-token",
                    "__Host-next-auth.csrf-token", 
                    "__Secure-next-auth.callback-url",
                    "email", "EMAIL"
                ]
                
                found_traditional_auth = []
                found_veo_auth = []
                
                # Check traditional Google auth
                for indicator in traditional_auth_indicators:
                    if indicator in cookies:
                        found_traditional_auth.append(indicator)
                
                # Check Veo-specific auth  
                for indicator in veo_auth_indicators:
                    if indicator in cookies:
                        found_veo_auth.append(indicator)
                
                # Login is detected if we have either traditional auth OR Veo auth
                is_logged_in = len(found_traditional_auth) > 0 or len(found_veo_auth) > 0
                
                # Additional check for any email or session token
                has_email = "email" in cookies.lower() or "EMAIL" in cookies
                has_session = "session-token" in cookies
                
                if has_session or has_email:
                    is_logged_in = True
                
                return {
                    "logged_in": is_logged_in,
                    "method": "File-based (Legacy)",
                    "traditional_auth_cookies": found_traditional_auth,
                    "veo_auth_cookies": found_veo_auth,
                    "has_email": has_email,
                    "has_session_token": has_session,
                    "cookies": cookies,
                    "debug_info": f"Traditional: {len(found_traditional_auth)}, Veo: {len(found_veo_auth)}, Email: {has_email}, Session: {has_session}"
                }
                    
            except Exception as e:
                return {
                    "logged_in": False,
                    "method": "File-based (Legacy)",
                    "error": str(e),
                    "cookies": "",
                    "debug_info": f"Error: {str(e)}"
                } 