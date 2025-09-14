#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Enhanced WebDriver Manager
Cross-platform WebDriver setup with bundled drivers for distribution
Quản lý WebDriver đa nền tảng với drivers được đóng gói sẵn
"""

import os
import sys
import platform
import subprocess
import shutil
import zipfile
import requests
from pathlib import Path
from typing import Optional, Dict, Any
import logging

class EnhancedWebDriverManager:
    def __init__(self, app_root: Optional[str] = None):
        """Initialize enhanced WebDriver manager"""
        if app_root:
            self.app_root = Path(app_root)
        else:
            self.app_root = Path(__file__).parent.parent
            
        self.system = platform.system()
        self.architecture = platform.machine().lower()
        
        # Directories
        self.drivers_dir = self.app_root / "drivers"
        self.drivers_dir.mkdir(exist_ok=True)
        
        # Bundled drivers directory (for distribution)
        self.bundled_drivers_dir = self.app_root / "bundled_drivers"
        self.bundled_drivers_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger('WebDriverManager')
        
        # Chrome paths by OS
        self.chrome_paths = {
            "Windows": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
            ],
            "Darwin": [  # macOS
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chrome.app/Contents/MacOS/Google Chrome"
            ],
            "Linux": [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/snap/bin/chromium"
            ]
        }
    
    def get_optimal_webdriver(self) -> Dict[str, Any]:
        """Get optimal WebDriver setup for current system"""
        result = {
            "success": False,
            "method": None,
            "driver_path": None,
            "chrome_path": None,
            "chrome_version": None,
            "notes": []
        }
        
        try:
            # Step 1: Find Chrome
            chrome_path = self.find_chrome_executable()
            if chrome_path:
                result["chrome_path"] = chrome_path
                result["chrome_version"] = self.get_chrome_version(chrome_path)
                result["notes"].append(f"Chrome found: {chrome_path}")
            else:
                result["notes"].append("Chrome not found - using system default")
            
            # Step 2: Try different WebDriver methods in order of preference
            
            # Method 1: Bundled driver (for distribution)
            bundled_driver = self.get_bundled_driver()
            if bundled_driver:
                result.update({
                    "success": True,
                    "method": "bundled",
                    "driver_path": bundled_driver
                })
                result["notes"].append("Using bundled ChromeDriver")
                return result
            
            # Method 2: webdriver-manager (auto-download)
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                driver_path = ChromeDriverManager().install()
                result.update({
                    "success": True,
                    "method": "webdriver-manager",
                    "driver_path": driver_path
                })
                result["notes"].append("Using webdriver-manager")
                return result
            except ImportError:
                result["notes"].append("webdriver-manager not available")
            except Exception as e:
                result["notes"].append(f"webdriver-manager failed: {e}")
            
            # Method 3: Manual download
            manual_driver = self.download_chromedriver_manual(result["chrome_version"])
            if manual_driver:
                result.update({
                    "success": True,
                    "method": "manual_download",
                    "driver_path": manual_driver
                })
                result["notes"].append("Downloaded ChromeDriver manually")
                return result
            
            # Method 4: System PATH
            system_driver = self.find_system_chromedriver()
            if system_driver:
                result.update({
                    "success": True,
                    "method": "system_path",
                    "driver_path": system_driver
                })
                result["notes"].append("Using system ChromeDriver")
                return result
            
            # Method 5: Fallback to Selenium default
            result.update({
                "success": True,
                "method": "selenium_default",
                "driver_path": None
            })
            result["notes"].append("Using Selenium's built-in ChromeDriver")
            
        except Exception as e:
            result["notes"].append(f"Error in WebDriver setup: {e}")
            
        return result
    
    def find_chrome_executable(self) -> Optional[str]:
        """Find Chrome executable across platforms"""
        # Check predefined paths
        for path in self.chrome_paths.get(self.system, []):
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        
        # Try command line detection
        try:
            if self.system in ["Darwin", "Linux"]:
                commands = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]
                for cmd in commands:
                    try:
                        result = subprocess.run(['which', cmd], capture_output=True, text=True, timeout=5)
                        if result.returncode == 0 and result.stdout.strip():
                            return result.stdout.strip()
                    except:
                        continue
            elif self.system == "Windows":
                # Try registry on Windows
                try:
                    import winreg
                    key_paths = [
                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
                        r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"
                    ]
                    for key_path in key_paths:
                        try:
                            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                                chrome_path = winreg.QueryValue(key, "")
                                if os.path.exists(chrome_path):
                                    return chrome_path
                        except:
                            continue
                except ImportError:
                    pass
        except:
            pass
            
        return None
    
    def get_chrome_version(self, chrome_path: str) -> Optional[str]:
        """Get Chrome version"""
        try:
            result = subprocess.run([chrome_path, "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                import re
                match = re.search(r'(\d+)\.(\d+)\.(\d+)\.(\d+)', result.stdout)
                if match:
                    return match.group(0)
        except:
            pass
        return None
    
    def get_bundled_driver(self) -> Optional[str]:
        """Get bundled ChromeDriver for current platform"""
        driver_name = "chromedriver.exe" if self.system == "Windows" else "chromedriver"
        
        # Platform-specific bundled drivers
        platform_map = {
            "Windows": "windows",
            "Darwin": "macos" if self.architecture in ["x86_64", "amd64"] else "macos_arm64", 
            "Linux": "linux"
        }
        
        platform_dir = platform_map.get(self.system, "linux")
        bundled_path = self.bundled_drivers_dir / platform_dir / driver_name
        
        if bundled_path.exists() and os.access(bundled_path, os.X_OK):
            return str(bundled_path)
            
        return None
    
    def download_chromedriver_manual(self, chrome_version: Optional[str] = None) -> Optional[str]:
        """Manually download ChromeDriver"""
        try:
            # Determine version
            if not chrome_version:
                chrome_version = "120.0.6099"  # Fallback
                
            major_version = chrome_version.split('.')[0]
            
            # Get latest ChromeDriver version for this Chrome major version
            try:
                response = requests.get(f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}", timeout=10)
                if response.status_code == 200:
                    chromedriver_version = response.text.strip()
                else:
                    # Fallback versions
                    version_map = {
                        "120": "120.0.6099.109",
                        "119": "119.0.6045.105",
                        "118": "118.0.5993.70"
                    }
                    chromedriver_version = version_map.get(major_version, "120.0.6099.109")
            except:
                chromedriver_version = "120.0.6099.109"
            
            # Platform mapping
            platform_map = {
                "Windows": "win32.zip",
                "Darwin": "mac64.zip" if self.architecture in ["x86_64", "amd64"] else "mac_arm64.zip",
                "Linux": "linux64.zip"
            }
            
            platform_suffix = platform_map.get(self.system, "linux64.zip")
            download_url = f"https://chromedriver.storage.googleapis.com/{chromedriver_version}/chromedriver_{platform_suffix}"
            
            # Download
            self.logger.info(f"Downloading ChromeDriver {chromedriver_version}...")
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            zip_path = self.drivers_dir / f"chromedriver_{chromedriver_version}.zip"
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.drivers_dir)
            
            # Find executable
            driver_name = "chromedriver.exe" if self.system == "Windows" else "chromedriver"
            driver_path = self.drivers_dir / driver_name
            
            if driver_path.exists():
                # Make executable on Unix
                if self.system in ["Darwin", "Linux"]:
                    os.chmod(driver_path, 0o755)
                
                # Cleanup
                zip_path.unlink()
                
                return str(driver_path)
                
        except Exception as e:
            self.logger.error(f"Manual ChromeDriver download failed: {e}")
            
        return None
    
    def find_system_chromedriver(self) -> Optional[str]:
        """Find ChromeDriver in system PATH"""
        driver_name = "chromedriver.exe" if self.system == "Windows" else "chromedriver"
        
        try:
            if self.system in ["Darwin", "Linux"]:
                result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            elif self.system == "Windows":
                result = subprocess.run(['where', 'chromedriver'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip().split('\n')[0]
        except:
            pass
            
        return None
    
    def create_selenium_webdriver(self, options=None):
        """Create Selenium WebDriver with optimal configuration"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        if not options:
            options = Options()
            
        # Get optimal driver setup
        driver_info = self.get_optimal_webdriver()
        
        if not driver_info["success"]:
            raise Exception("Could not setup ChromeDriver")
        
        try:
            # Create driver based on method
            if driver_info["method"] == "selenium_default":
                # Let Selenium handle everything
                driver = webdriver.Chrome(options=options)
            else:
                # Use specific driver path
                service = Service(driver_info["driver_path"])
                driver = webdriver.Chrome(service=service, options=options)
            
            # Anti-detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info(f"✅ WebDriver created using {driver_info['method']} method")
            
            return driver, driver_info
            
        except Exception as e:
            self.logger.error(f"❌ WebDriver creation failed: {e}")
            raise
    
    def prepare_for_distribution(self):
        """Prepare ChromeDrivers for all platforms (for developers)"""
        """This method downloads ChromeDrivers for all platforms to bundle with app"""
        
        platforms = {
            "windows": "win32.zip",
            "macos": "mac64.zip", 
            "macos_arm64": "mac_arm64.zip",
            "linux": "linux64.zip"
        }
        
        chrome_version = "120.0.6099.109"  # Stable version
        
        for platform_name, platform_suffix in platforms.items():
            try:
                download_url = f"https://chromedriver.storage.googleapis.com/{chrome_version}/chromedriver_{platform_suffix}"
                
                print(f"📥 Downloading ChromeDriver for {platform_name}...")
                response = requests.get(download_url, stream=True, timeout=30)
                response.raise_for_status()
                
                # Create platform directory
                platform_dir = self.bundled_drivers_dir / platform_name
                platform_dir.mkdir(exist_ok=True)
                
                # Download and extract
                zip_path = platform_dir / f"chromedriver.zip"
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(platform_dir)
                
                # Make executable (for Unix platforms)
                driver_name = "chromedriver.exe" if "windows" in platform_name else "chromedriver"
                driver_path = platform_dir / driver_name
                
                if driver_path.exists() and "windows" not in platform_name:
                    os.chmod(driver_path, 0o755)
                
                # Cleanup
                zip_path.unlink()
                
                print(f"✅ ChromeDriver for {platform_name} prepared")
                
            except Exception as e:
                print(f"❌ Failed to prepare ChromeDriver for {platform_name}: {e}")

# Global instance
_webdriver_manager = None

def get_webdriver_manager() -> EnhancedWebDriverManager:
    """Get global WebDriver manager instance"""
    global _webdriver_manager
    if _webdriver_manager is None:
        _webdriver_manager = EnhancedWebDriverManager()
    return _webdriver_manager

def create_optimized_webdriver(options=None):
    """Create optimized WebDriver - main public API"""
    manager = get_webdriver_manager()
    return manager.create_selenium_webdriver(options)

if __name__ == "__main__":
    # Test the system
    print("🧪 Testing Enhanced WebDriver Manager...")
    
    manager = EnhancedWebDriverManager()
    driver_info = manager.get_optimal_webdriver()
    
    print(f"✅ WebDriver setup result: {driver_info}")
    
    # Uncomment to prepare drivers for distribution
    # print("📦 Preparing drivers for distribution...")
    # manager.prepare_for_distribution()
