#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - System Initializer
Auto-creates all necessary files and directories for cross-platform compatibility
Tự động tạo tất cả file và thư mục cần thiết cho tương thích đa nền tảng
"""

import os
import sys
import json
import platform
import shutil
import subprocess
import requests
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import time
import yaml

class SystemInitializer:
    def __init__(self, app_root: Optional[str] = None):
        """Initialize the system checker and creator"""
        if app_root:
            self.app_root = Path(app_root)
        else:
            # Auto-detect app root (ClausoNet4.0 directory)
            self.app_root = Path(__file__).parent.parent

        self.system = platform.system()
        self.architecture = platform.machine().lower()

        # Create logs directory first
        self.logs_dir = self.app_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)

        # Setup logging
        self.setup_logging()

        # Define all required directories
        self.required_dirs = [
            "admin_data",
            "chrome_profiles",
            "data/cache",
            "data/templates",
            "data/workflows",
            "output",
            "temp",
            "logs",
            "certs",
            "backups"
        ]

        # Define required files with their templates
        self.required_files = {
            "config.yaml": self.create_default_config,
            "admin_data/license_database.json": self.create_license_database,
            "data/workflows/default_workflow.json": self.create_default_workflow,
            "data/templates/video_templates.json": self.create_video_templates,
            "logs/.gitkeep": lambda: "",
            "temp/.gitkeep": lambda: "",
            "output/.gitkeep": lambda: ""
        }

        self.logger.info(f"🎯 SystemInitializer started for {self.system} {self.architecture}")

    def setup_logging(self):
        """Setup logging system"""
        log_file = self.logs_dir / "system_init.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('SystemInit')

    def initialize_all(self) -> Dict[str, Any]:
        """Complete system initialization - main entry point"""
        results = {
            "success": True,
            "steps_completed": [],
            "errors": [],
            "chrome_info": {},
            "selenium_info": {},
            "system_info": {}
        }

        try:
            self.logger.info("🚀 Starting complete system initialization...")

            # Step 1: Create directories
            self.logger.info("📁 Creating required directories...")
            self.create_directories()
            results["steps_completed"].append("directories_created")

            # Step 2: Create config files
            self.logger.info("📝 Creating configuration files...")
            self.create_config_files()
            results["steps_completed"].append("config_files_created")

            # Step 3: Setup Chrome and ChromeDriver
            self.logger.info("🌐 Setting up Chrome and ChromeDriver...")
            chrome_result = self.setup_chrome_system()
            results["chrome_info"] = chrome_result
            results["steps_completed"].append("chrome_setup")

            # Step 4: Setup Selenium
            self.logger.info("🔧 Setting up Selenium WebDriver...")
            selenium_result = self.setup_selenium_webdriver()
            results["selenium_info"] = selenium_result
            results["steps_completed"].append("selenium_setup")

            # Step 5: Create admin data
            self.logger.info("👤 Setting up admin and license system...")
            self.setup_admin_system()
            results["steps_completed"].append("admin_setup")

            # Step 6: Verify permissions
            self.logger.info("🔐 Verifying system permissions...")
            self.setup_permissions()
            results["steps_completed"].append("permissions_setup")

            # Step 7: System info collection
            results["system_info"] = self.collect_system_info()
            results["steps_completed"].append("system_info_collected")

            self.logger.info("✅ System initialization completed successfully!")

        except Exception as e:
            self.logger.error(f"❌ System initialization failed: {e}")
            results["success"] = False
            results["errors"].append(str(e))

        return results

    def create_directories(self):
        """Create all required directories"""
        for dir_path in self.required_dirs:
            full_path = self.app_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"✅ Created directory: {dir_path}")

    def create_config_files(self):
        """Create all required configuration files"""
        for file_path, creator_func in self.required_files.items():
            full_path = self.app_root / file_path

            if not full_path.exists():
                try:
                    content = creator_func()

                    # Create parent directory if needed
                    full_path.parent.mkdir(parents=True, exist_ok=True)

                    # Write file based on extension
                    if file_path.endswith('.json'):
                        with open(full_path, 'w', encoding='utf-8') as f:
                            if isinstance(content, (dict, list)):
                                json.dump(content, f, indent=2, ensure_ascii=False)
                            else:
                                f.write(content)
                    elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
                        with open(full_path, 'w', encoding='utf-8') as f:
                            if isinstance(content, dict):
                                yaml.dump(content, f, default_flow_style=False, allow_unicode=True)
                            else:
                                f.write(content)
                    else:
                        with open(full_path, 'w', encoding='utf-8') as f:
                            f.write(str(content))

                    self.logger.info(f"✅ Created config file: {file_path}")

                except Exception as e:
                    self.logger.error(f"❌ Failed to create {file_path}: {e}")
            else:
                self.logger.info(f"ℹ️ Config file already exists: {file_path}")

    def setup_chrome_system(self) -> Dict[str, Any]:
        """Setup Chrome browser detection and ChromeDriver"""
        result = {
            "chrome_found": False,
            "chrome_path": None,
            "chrome_version": None,
            "chromedriver_path": None,
            "chromedriver_version": None,
            "installation_method": None
        }

        try:
            # Find Chrome executable
            chrome_path = self.find_chrome_executable()
            if chrome_path:
                result["chrome_found"] = True
                result["chrome_path"] = chrome_path
                result["chrome_version"] = self.get_chrome_version(chrome_path)
                self.logger.info(f"✅ Chrome found: {chrome_path} (v{result['chrome_version']})")
            else:
                self.logger.warning("⚠️ Chrome not found - will try to use system default")

            # Setup ChromeDriver
            chromedriver_result = self.setup_chromedriver(result["chrome_version"])
            result.update(chromedriver_result)

        except Exception as e:
            self.logger.error(f"❌ Chrome setup failed: {e}")
            result["error"] = str(e)

        return result

    def find_chrome_executable(self) -> Optional[str]:
        """Find Chrome executable across different operating systems"""
        chrome_paths = {
            "Windows": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(
                    os.getenv('USERNAME', '')
                ),
                r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            ],
            "Darwin": [  # macOS
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chrome.app/Contents/MacOS/Google Chrome",
                f"/Users/{os.getenv('USER', '')}/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            ],
            "Linux": [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/snap/bin/chromium",
                "/opt/google/chrome/chrome"
            ]
        }

        # Check predefined paths
        for path in chrome_paths.get(self.system, []):
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path

        # Try command line detection
        try:
            if self.system in ["Darwin", "Linux"]:
                # Unix-like systems
                commands = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]
                for cmd in commands:
                    try:
                        result = subprocess.run(['which', cmd], capture_output=True, text=True, timeout=5)
                        if result.returncode == 0 and result.stdout.strip():
                            return result.stdout.strip()
                    except:
                        continue
            elif self.system == "Windows":
                # Windows - check registry
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
                    pass  # winreg not available
        except:
            pass

        return None

    def get_chrome_version(self, chrome_path: str) -> Optional[str]:
        """Get Chrome version"""
        try:
            if self.system == "Windows":
                result = subprocess.run([chrome_path, "--version"], capture_output=True, text=True, timeout=10)
            else:
                result = subprocess.run([chrome_path, "--version"], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                # Extract version from output like "Google Chrome 120.0.6099.109"
                version_line = result.stdout.strip()
                import re
                match = re.search(r'(\d+)\.(\d+)\.(\d+)\.(\d+)', version_line)
                if match:
                    return match.group(0)
        except:
            pass

        return None

    def setup_chromedriver(self, chrome_version: Optional[str] = None) -> Dict[str, Any]:
        """Setup ChromeDriver with webdriver-manager"""
        result = {
            "chromedriver_path": None,
            "chromedriver_version": None,
            "installation_method": "webdriver-manager"
        }

        try:
            # Try webdriver-manager first (recommended)
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service

                driver_path = ChromeDriverManager().install()
                result["chromedriver_path"] = driver_path
                result["installation_method"] = "webdriver-manager"

                # Get ChromeDriver version
                try:
                    version_result = subprocess.run([driver_path, "--version"],
                                                  capture_output=True, text=True, timeout=5)
                    if version_result.returncode == 0:
                        import re
                        match = re.search(r'(\d+)\.(\d+)\.(\d+)\.(\d+)', version_result.stdout)
                        if match:
                            result["chromedriver_version"] = match.group(0)
                except:
                    pass

                self.logger.info(f"✅ ChromeDriver installed via webdriver-manager: {driver_path}")
                return result

            except ImportError:
                self.logger.warning("⚠️ webdriver-manager not available, trying manual installation...")

            # Manual ChromeDriver installation as fallback
            manual_result = self.install_chromedriver_manually(chrome_version)
            result.update(manual_result)

        except Exception as e:
            self.logger.error(f"❌ ChromeDriver setup failed: {e}")
            result["error"] = str(e)

        return result

    def install_chromedriver_manually(self, chrome_version: Optional[str] = None) -> Dict[str, Any]:
        """Manually install ChromeDriver"""
        result = {
            "chromedriver_path": None,
            "chromedriver_version": None,
            "installation_method": "manual"
        }

        try:
            # Create drivers directory
            drivers_dir = self.app_root / "drivers"
            drivers_dir.mkdir(exist_ok=True)

            # Determine ChromeDriver version needed
            if not chrome_version:
                chrome_version = "120.0.6099"  # Fallback to stable version

            major_version = chrome_version.split('.')[0]

            # ChromeDriver download URLs
            base_url = "https://chromedriver.storage.googleapis.com"

            # Get available versions
            try:
                response = requests.get(f"{base_url}/LATEST_RELEASE_{major_version}", timeout=10)
                if response.status_code == 200:
                    chromedriver_version = response.text.strip()
                else:
                    # Fallback versions for common Chrome versions
                    version_map = {
                        "120": "120.0.6099.109",
                        "119": "119.0.6045.105",
                        "118": "118.0.5993.70",
                        "117": "117.0.5938.92"
                    }
                    chromedriver_version = version_map.get(major_version, "120.0.6099.109")
            except:
                chromedriver_version = "120.0.6099.109"  # Ultimate fallback

            # Determine platform suffix
            platform_map = {
                "Windows": "win32.zip",
                "Darwin": "mac64.zip" if self.architecture in ["x86_64", "amd64"] else "mac_arm64.zip",
                "Linux": "linux64.zip"
            }

            platform_suffix = platform_map.get(self.system, "linux64.zip")
            download_url = f"{base_url}/{chromedriver_version}/chromedriver_{platform_suffix}"

            # Download ChromeDriver
            self.logger.info(f"📥 Downloading ChromeDriver {chromedriver_version}...")
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            zip_path = drivers_dir / f"chromedriver_{chromedriver_version}.zip"
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Extract ChromeDriver
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(drivers_dir)

            # Find extracted executable
            chromedriver_name = "chromedriver.exe" if self.system == "Windows" else "chromedriver"
            chromedriver_path = drivers_dir / chromedriver_name

            if chromedriver_path.exists():
                # Make executable on Unix systems
                if self.system in ["Darwin", "Linux"]:
                    os.chmod(chromedriver_path, 0o755)

                result["chromedriver_path"] = str(chromedriver_path)
                result["chromedriver_version"] = chromedriver_version

                self.logger.info(f"✅ ChromeDriver installed manually: {chromedriver_path}")
            else:
                raise Exception("ChromeDriver executable not found after extraction")

            # Cleanup
            zip_path.unlink()

        except Exception as e:
            self.logger.error(f"❌ Manual ChromeDriver installation failed: {e}")
            result["error"] = str(e)

        return result

    def setup_selenium_webdriver(self) -> Dict[str, Any]:
        """Setup Selenium WebDriver with optimal configuration"""
        result = {
            "selenium_version": None,
            "webdriver_available": False,
            "test_successful": False
        }

        try:
            # Check Selenium installation
            import selenium
            result["selenium_version"] = selenium.__version__
            self.logger.info(f"✅ Selenium version: {selenium.__version__}")

            # Test WebDriver creation
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options

            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")

            try:
                # Try with webdriver-manager first
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    from selenium.webdriver.chrome.service import Service
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)
                except ImportError:
                    driver = webdriver.Chrome(options=options)

                # Quick test
                driver.get("data:text/html,<html><body><h1>Test</h1></body></html>")
                title = driver.title
                driver.quit()

                result["webdriver_available"] = True
                result["test_successful"] = True
                self.logger.info("✅ Selenium WebDriver test successful")

            except Exception as e:
                self.logger.warning(f"⚠️ WebDriver test failed: {e}")
                result["webdriver_available"] = False
                result["test_error"] = str(e)

        except ImportError:
            self.logger.error("❌ Selenium not installed")
            result["error"] = "Selenium not installed"

        return result

    def setup_admin_system(self):
        """Setup admin and license system"""
        try:
            # Create admin data directory
            admin_dir = self.app_root / "admin_data"
            admin_dir.mkdir(exist_ok=True)

            # Initialize license system
            license_db_path = admin_dir / "license_database.json"
            if not license_db_path.exists():
                license_data = self.create_license_database()
                with open(license_db_path, 'w', encoding='utf-8') as f:
                    json.dump(license_data, f, indent=2, ensure_ascii=False)
                self.logger.info("✅ License database created")

            # NOTE: Sample license creation disabled for production builds
            # Create sample license for testing - DISABLED
            # try:
            #     sys.path.append(str(self.app_root))
            #     from admin_tools.license_key_generator import LicenseKeyGenerator
            #     generator = LicenseKeyGenerator()
            #     sample_key = generator.create_sample_license_for_testing()
            #     if sample_key:
            #         self.logger.info(f"✅ Sample license created: {sample_key}")
            # except Exception as e:
            #     self.logger.warning(f"⚠️ Could not create sample license: {e}")
            self.logger.info("✅ Admin system setup complete (production mode - no sample licenses)")

        except Exception as e:
            self.logger.error(f"❌ Admin system setup failed: {e}")

    def setup_permissions(self):
        """Setup system permissions for macOS/Linux"""
        if self.system in ["Darwin", "Linux"]:
            try:
                # Make scripts executable
                script_files = [
                    "install.sh",
                    "run_app.sh"
                ]

                for script in script_files:
                    script_path = self.app_root / script
                    if script_path.exists():
                        os.chmod(script_path, 0o755)
                        self.logger.info(f"✅ Made executable: {script}")

                # Set permissions for drivers directory
                drivers_dir = self.app_root / "drivers"
                if drivers_dir.exists():
                    for file in drivers_dir.rglob("*"):
                        if file.is_file() and not file.suffix:
                            os.chmod(file, 0o755)

                self.logger.info("✅ Permissions setup completed")

            except Exception as e:
                self.logger.warning(f"⚠️ Permissions setup failed: {e}")

    def collect_system_info(self) -> Dict[str, Any]:
        """Collect system information for debugging"""
        info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "app_root": str(self.app_root),
            "current_dir": os.getcwd(),
            "user": os.getenv('USER') or os.getenv('USERNAME', 'unknown'),
            "path_sep": os.sep,
            "environment": dict(os.environ) if len(os.environ) < 100 else "too_large"
        }

        return info

    # Template creators for default files
    def create_default_config(self) -> Dict[str, Any]:
        """Create default config.yaml content"""
        return {
            "apis": {
                "gemini": {
                    "enabled": True,
                    "api_key": "YOUR_GEMINI_API_KEY",
                    "model": "gemini-2.5-flash",
                    "max_tokens": 8192,
                    "temperature": 0.7
                },
                "openai": {
                    "enabled": True,
                    "api_key": "YOUR_OPENAI_API_KEY",
                    "model": "gpt-4-turbo"
                }
            },
            "app": {
                "name": "ClausoNet 4.0 Pro",
                "version": "1.0.0",
                "paths": {
                    "output": "./output",
                    "temp": "./temp",
                    "cache": "./data/cache",
                    "templates": "./data/templates",
                    "workflows": "./data/workflows"
                },
                "defaults": {
                    "video_format": "mp4",
                    "video_quality": "high",
                    "max_concurrent_jobs": 3
                },
                "ui": {
                    "theme": "dark",
                    "language": "en",
                    "auto_save": True
                }
            },
            "logging": {
                "level": "INFO",
                "file": "./logs/clausonet.log",
                "max_size": "10MB",
                "backup_count": 5
            },
            "security": {
                "license_check": True,
                "hardware_binding": True
            },
            "performance": {
                "cache_enabled": True,
                "parallel_processing": True,
                "gpu_acceleration": False
            }
        }

    def create_license_database(self) -> Dict[str, Any]:
        """Create default license database"""
        from datetime import datetime

        return {
            "keys": [],
            "customers": [],
            "statistics": {
                "total_keys_generated": 0,
                "trial_keys": 0,
                "monthly_keys": 0,
                "quarterly_keys": 0,
                "lifetime_keys": 0,
                "multi_device_keys": 0,
                "keys_activated": 0,
                "revenue_tracked": 0.0
            },
            "created_at": datetime.utcnow().isoformat(),
            "version": "1.0"
        }

    def create_default_workflow(self) -> Dict[str, Any]:
        """Create default workflow template"""
        return {
            "name": "Default Video Generation Workflow",
            "version": "1.0",
            "steps": [
                {
                    "id": "generate_prompt",
                    "type": "ai_generation",
                    "description": "Generate video prompt using AI"
                },
                {
                    "id": "create_video",
                    "type": "video_creation",
                    "description": "Create video using Google Veo"
                },
                {
                    "id": "download_result",
                    "type": "download",
                    "description": "Download generated video"
                }
            ],
            "settings": {
                "auto_save": True,
                "backup_enabled": True,
                "timeout": 300
            }
        }

    def create_video_templates(self) -> Dict[str, Any]:
        """Create video templates"""
        return {
            "templates": [
                {
                    "name": "Professional",
                    "description": "Professional video template",
                    "settings": {
                        "quality": "high",
                        "duration": 30,
                        "style": "professional"
                    }
                },
                {
                    "name": "Creative",
                    "description": "Creative video template",
                    "settings": {
                        "quality": "high",
                        "duration": 60,
                        "style": "creative"
                    }
                }
            ]
        }

# Main initialization function
def initialize_system(app_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Main entry point for system initialization

    Args:
        app_root: Path to application root directory (auto-detected if None)

    Returns:
        Dict with initialization results
    """
    try:
        initializer = SystemInitializer(app_root)
        return initializer.initialize_all()
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "steps_completed": [],
            "errors": [str(e)]
        }

# Quick test function
def test_system() -> bool:
    """Quick system test"""
    try:
        result = initialize_system()
        return result.get("success", False)
    except:
        return False

if __name__ == "__main__":
    print("🚀 ClausoNet 4.0 Pro - System Initializer")
    print("=" * 50)

    result = initialize_system()

    if result["success"]:
        print("✅ System initialization completed successfully!")
        print(f"📋 Steps completed: {len(result['steps_completed'])}")
        for step in result["steps_completed"]:
            print(f"  ✓ {step}")
    else:
        print("❌ System initialization failed!")
        for error in result.get("errors", []):
            print(f"  ✗ {error}")

    print("\n📊 System Information:")
    system_info = result.get("system_info", {})
    for key, value in system_info.items():
        if key not in ["environment"]:  # Skip large environment dict
            print(f"  {key}: {value}")
