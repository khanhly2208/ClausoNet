#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Chrome Driver Manager for Production
Quản lý ChromeDriver cho thương mại hóa (exe/app)
"""

import os
import sys
import platform
import subprocess
import zipfile
import requests
from pathlib import Path
import shutil
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

class ProductionChromeDriverManager:
    """Quản lý ChromeDriver cho production build"""

    def __init__(self, resource_manager):
        self.resource_manager = resource_manager
        self.system = platform.system()
        self.is_frozen = getattr(sys, 'frozen', False)
        
        # 🔒 TRACK CHROME PROCESSES: Lưu PID của Chrome processes do app tạo ra
        self.app_chrome_processes = []  # List of Process objects or PIDs
        self.debug_port = 9222  # Default debug port

        # ChromeDriver paths
        self.drivers_dir = Path(self.resource_manager.user_data_dir) / "drivers"
        self.drivers_dir.mkdir(exist_ok=True)

        # Download URLs cho ChromeDriver
        self.chromedriver_base_url = "https://chromedriver.storage.googleapis.com"
        self.chrome_for_testing_url = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"

    def get_chrome_version(self):
        """Lấy version của Chrome đã cài"""
        try:
            chrome_exe = self.resource_manager.find_chrome_executable()
            if not chrome_exe:
                return None

            if self.system == "Windows":
                # Windows
                result = subprocess.run([chrome_exe, "--version"],
                                      capture_output=True, text=True, timeout=10)
            else:
                # macOS/Linux
                result = subprocess.run([chrome_exe, "--version"],
                                      capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                # Parse version number
                version_text = result.stdout.strip()
                # "Google Chrome 120.0.6099.109" -> "120.0.6099"
                version = version_text.split()[-1]
                major_version = version.split('.')[0]
                return major_version

        except Exception as e:
            print(f"⚠️ Cannot get Chrome version: {e}")

        return None

    def get_bundled_chromedriver_path(self):
        """Lấy đường dẫn ChromeDriver từ bundle (nếu có)"""
        if self.is_frozen:
            # Trong production build
            if self.system == "Windows":
                bundled_path = Path(self.resource_manager.app_dir) / "drivers" / "chromedriver.exe"
            else:
                bundled_path = Path(self.resource_manager.app_dir) / "drivers" / "chromedriver"

            if bundled_path.exists():
                return str(bundled_path)

        return None

    def get_local_chromedriver_path(self):
        """Lấy đường dẫn ChromeDriver local (downloaded)"""
        if self.system == "Windows":
            local_path = self.drivers_dir / "chromedriver.exe"
        else:
            local_path = self.drivers_dir / "chromedriver"

        if local_path.exists():
            return str(local_path)
        return None

    def download_chromedriver(self, version=None):
        """Download ChromeDriver"""
        try:
            if not version:
                version = self.get_chrome_version()
                if not version:
                    # Fallback to latest stable
                    version = "120"  # Hoặc get từ API

            print(f"📥 Downloading ChromeDriver for Chrome {version}... (Legacy API - may fail)")

            # Xác định platform
            if self.system == "Windows":
                platform_name = "win32"
                filename = "chromedriver.exe"
            elif self.system == "Darwin":  # macOS
                platform_name = "mac-x64"  # Hoặc mac-arm64 cho Apple Silicon
                filename = "chromedriver"
            else:  # Linux
                platform_name = "linux64"
                filename = "chromedriver"

            # Download URL
            download_url = f"{self.chromedriver_base_url}/{version}/chromedriver_{platform_name}.zip"

            # Download và extract
            response = requests.get(download_url, timeout=30)
            if response.status_code == 200:
                # Save zip file
                zip_path = self.drivers_dir / "chromedriver.zip"
                with open(zip_path, 'wb') as f:
                    f.write(response.content)

                # Extract
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(self.drivers_dir)

                # Move executable to correct location
                extracted_path = self.drivers_dir / filename
                final_path = self.drivers_dir / filename

                # Set permissions (Unix systems)
                if self.system != "Windows":
                    os.chmod(final_path, 0o755)

                # Cleanup
                zip_path.unlink()

                print(f"✅ ChromeDriver downloaded: {final_path}")
                return str(final_path)
            else:
                print(f"❌ Failed to download ChromeDriver: HTTP {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ ChromeDriver download error: {e}")
            return None

    def get_chromedriver_path(self, auto_download=True):
        """Lấy đường dẫn ChromeDriver - ưu tiên bundled, sau đó local, cuối cùng download"""

        # 1. Thử bundled version (trong exe/app)
        bundled_path = self.get_bundled_chromedriver_path()
        if bundled_path:
            print(f"✅ Using bundled ChromeDriver: {bundled_path}")
            return bundled_path

        # 2. Thử local version (đã download)
        local_path = self.get_local_chromedriver_path()
        if local_path:
            print(f"✅ Using local ChromeDriver: {local_path}")
            return local_path

        # 3. Skip download (Chrome 115+ uses different distribution method)
        # Download is disabled to avoid 404 errors from deprecated URLs
        if False:  # Disabled auto_download due to ChromeDriver API changes
            downloaded_path = self.download_chromedriver()
            if downloaded_path:
                return downloaded_path

        # 4. Fallback về system ChromeDriver
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            system_path = ChromeDriverManager().install()
            print(f"✅ Using system ChromeDriver: {system_path}")
            return system_path
        except ImportError:
            print("❌ webdriver_manager not available")
        except Exception as e:
            print(f"❌ System ChromeDriver error: {e}")

        return None

    def create_chrome_options(self, profile_path=None, headless=False, debug_port=None):
        """Tạo Chrome options cho production"""
        options = Options()

        # Basic options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")  # Tăng tốc độ
        options.add_argument("--disable-javascript")  # Có thể bật lại nếu cần

        # Profile
        if profile_path:
            options.add_argument(f"--user-data-dir={profile_path}")
            options.add_argument("--profile-directory=Default")

        # Headless mode
        if headless:
            options.add_argument("--headless")

        # Debug port - 🔒 USE UNIQUE PORT để identify Chrome của app
        if debug_port:
            self.debug_port = debug_port
        else:
            # Tạo unique debug port để identify Chrome process của app
            import random
            self.debug_port = 9222 + random.randint(100, 999)
        
        options.add_argument(f"--remote-debugging-port={self.debug_port}")
        print(f"🔒 Using unique debug port: {self.debug_port}")

        # Production optimizations
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-component-update")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")

        # Anti-detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        return options

    def create_webdriver(self, profile_path=None, headless=False, debug_port=9222):
        """Tạo WebDriver instance cho production"""
        try:
            # Get ChromeDriver path
            chromedriver_path = self.get_chromedriver_path()
            if not chromedriver_path:
                raise Exception("ChromeDriver not found")

            # Create service
            service = Service(chromedriver_path)

            # Create options
            options = self.create_chrome_options(
                profile_path=profile_path,
                headless=headless,
                debug_port=debug_port
            )

            # Create driver
            driver = webdriver.Chrome(service=service, options=options)

            # 🔒 TRACK CHROME PROCESS: Lưu lại Chrome process được tạo bởi app
            try:
                import psutil
                # Find Chrome processes với debug port của app
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if (proc.info['name'] == 'chrome.exe' and 
                            proc.info['cmdline'] and
                            f'--remote-debugging-port={self.debug_port}' in ' '.join(proc.info['cmdline'])):
                            self.app_chrome_processes.append(proc.info['pid'])
                            print(f"🔒 Tracked app Chrome process: PID {proc.info['pid']}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except ImportError:
                print("⚠️ psutil not available - using fallback process tracking")
            except Exception as e:
                print(f"⚠️ Process tracking error: {e}")

            # Anti-detection script
            driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            """)

            print("✅ WebDriver created successfully")
            return driver

        except Exception as e:
            print(f"❌ WebDriver creation failed: {e}")
            return None

    def validate_setup(self):
        """Kiểm tra setup ChromeDriver"""
        print("🔍 Validating ChromeDriver setup...")

        # Check Chrome
        chrome_exe = self.resource_manager.find_chrome_executable()
        if chrome_exe:
            print(f"✅ Chrome found: {chrome_exe}")
            chrome_version = self.get_chrome_version()
            if chrome_version:
                print(f"✅ Chrome version: {chrome_version}")
        else:
            print("❌ Chrome not found")
            return False

        # Check ChromeDriver
        chromedriver_path = self.get_chromedriver_path(auto_download=False)
        if chromedriver_path:
            print(f"✅ ChromeDriver found: {chromedriver_path}")
        else:
            print("⚠️ ChromeDriver not found - will download when needed")

        return True

    def cleanup(self):
        """🔒 SAFE CLEANUP: Chỉ dọn dẹp Chrome processes của app, KHÔNG đụng Chrome của user"""
        try:
            cleaned_count = 0
            failed_count = 0
            
            # Method 1: Kill tracked Chrome processes by PID
            if self.app_chrome_processes:
                print(f"🔒 Cleaning up {len(self.app_chrome_processes)} tracked Chrome processes...")
                
                try:
                    import psutil
                    for pid in self.app_chrome_processes[:]:  # Copy list to avoid modification during iteration
                        try:
                            proc = psutil.Process(pid)
                            if proc.is_running() and proc.name() in ['chrome.exe', 'Google Chrome']:
                                proc.terminate()  # Gentle termination first
                                try:
                                    proc.wait(timeout=3)  # Wait up to 3 seconds
                                except psutil.TimeoutExpired:
                                    proc.kill()  # Force kill if needed
                                print(f"✅ Cleaned Chrome process PID {pid}")
                                cleaned_count += 1
                            self.app_chrome_processes.remove(pid)  # Remove from tracking
                        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
                            try:
                                self.app_chrome_processes.remove(pid)
                            except ValueError:
                                pass
                            continue
                        except Exception as e:
                            print(f"⚠️ Failed to clean process {pid}: {e}")
                            failed_count += 1
                            
                except ImportError:
                    print("⚠️ psutil not available for safe cleanup")
                    # Fallback: Kill by debug port signature
                    self._fallback_cleanup_by_port()
                    
            else:
                print("🔒 No tracked Chrome processes to clean up")

            # Method 2: Kill ChromeDriver processes (these are always safe to kill)
            try:
                if self.system == "Windows":
                    result = subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe'],
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        print("✅ ChromeDriver processes cleaned up")
                else:
                    result = subprocess.run(['pkill', '-f', 'chromedriver'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        print("✅ ChromeDriver processes cleaned up")
            except Exception as e:
                print(f"⚠️ ChromeDriver cleanup warning: {e}")

            if cleaned_count > 0:
                print(f"✅ SAFE CLEANUP completed: {cleaned_count} app Chrome processes cleaned, {failed_count} failed")
            else:
                print("✅ SAFE CLEANUP completed: No Chrome processes to clean")
                
            # Clear tracking list
            self.app_chrome_processes.clear()

        except Exception as e:
            print(f"⚠️ Safe cleanup error: {e}")
            
    def _fallback_cleanup_by_port(self):
        """Fallback cleanup method using command line signature"""
        try:
            if self.system == "Windows":
                # Use wmic to find Chrome with our debug port
                cmd = f'wmic process where "name=\'chrome.exe\' and commandline like \'%--remote-debugging-port={self.debug_port}%\'" get processid /value'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line.startswith('ProcessId='):
                            pid = line.split('=')[1].strip()
                            if pid.isdigit():
                                subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                                print(f"✅ Fallback killed Chrome PID {pid}")
            else:
                # Linux/macOS: Use pgrep with port signature
                cmd = f'pgrep -f "chrome.*--remote-debugging-port={self.debug_port}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    for pid in result.stdout.strip().split('\n'):
                        if pid.strip().isdigit():
                            subprocess.run(['kill', '-TERM', pid.strip()], capture_output=True)
                            print(f"✅ Fallback killed Chrome PID {pid}")
                            
        except Exception as e:
            print(f"⚠️ Fallback cleanup error: {e}")
