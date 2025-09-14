#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Resource Manager
Quản lý đường dẫn file và resource cho việc đóng gói exe/app
"""

import os
import sys
import platform
from pathlib import Path
import tempfile
import shutil
import json

class ResourceManager:
    """Quản lý tất cả đường dẫn và resource cho thương mại hóa"""

    def __init__(self):
        # Xác định chế độ chạy
        self.is_frozen = getattr(sys, 'frozen', False)
        self.is_dev_mode = not self.is_frozen

        # Xác định thư mục gốc của ứng dụng
        if self.is_frozen:
            # Khi chạy từ exe
            if platform.system() == "Darwin":  # macOS
                # Trên macOS, executable nằm trong .app/Contents/MacOS/
                self.app_dir = Path(sys.executable).parent.parent.parent
            else:
                # Windows/Linux
                self.app_dir = Path(sys.executable).parent
        else:
            # Khi chạy từ source code
            self.app_dir = Path(__file__).parent.parent

        # Tạo thư mục data ở user directory để tránh permission issues
        self.user_data_dir = self._get_user_data_dir()
        self.user_data_dir.mkdir(exist_ok=True)

        # Xác định các thư mục quan trọng
        self._setup_directories()

        # Copy resource cần thiết từ bundle
        self._ensure_resources()

    def _get_user_data_dir(self):
        """Lấy thư mục data của user"""
        system = platform.system()

        if system == "Windows":
            # Windows: C:\Users\Username\AppData\Local\ClausoNet4.0\
            return Path.home() / "AppData" / "Local" / "ClausoNet4.0"
        elif system == "Darwin":  # macOS
            # macOS: ~/Library/Application Support/ClausoNet4.0/
            return Path.home() / "Library" / "Application Support" / "ClausoNet4.0"
        else:  # Linux
            # Linux: ~/.local/share/ClausoNet4.0/
            return Path.home() / ".local" / "share" / "ClausoNet4.0"

    def _setup_directories(self):
        """Thiết lập các thư mục cần thiết"""
        # Thư mục dữ liệu user (có thể ghi được)
        self.data_dir = self.user_data_dir / "data"
        self.chrome_profiles_dir = self.user_data_dir / "chrome_profiles"
        self.output_dir = self.user_data_dir / "output"
        self.logs_dir = self.user_data_dir / "logs"
        self.temp_dir = self.user_data_dir / "temp"
        self.certs_dir = self.user_data_dir / "certs"
        self.admin_data_dir = self.user_data_dir / "admin_data"

        # Tạo tất cả thư mục
        for directory in [
            self.data_dir, self.chrome_profiles_dir, self.output_dir,
            self.logs_dir, self.temp_dir, self.certs_dir, self.admin_data_dir
        ]:
            directory.mkdir(exist_ok=True)

        # Thư mục sub-directories
        (self.data_dir / "profile_cookies").mkdir(exist_ok=True)
        (self.data_dir / "workflows").mkdir(exist_ok=True)
        (self.data_dir / "cache").mkdir(exist_ok=True)
        (self.data_dir / "templates").mkdir(exist_ok=True)

    def _ensure_resources(self):
        """Đảm bảo các file resource cần thiết tồn tại"""

        # 0. Copy admin_tools từ bundle nếu cần
        admin_tools_dir = self.user_data_dir / "admin_tools"
        if self.is_frozen and not admin_tools_dir.exists():
            bundled_admin_tools = self.app_dir / "admin_tools"
            if bundled_admin_tools.exists():
                shutil.copytree(bundled_admin_tools, admin_tools_dir)
                print(f"✅ Copied admin_tools from bundle: {bundled_admin_tools}")

        # 1. Config file
        config_file = self.data_dir / "config.yaml"
        if not config_file.exists():
            self._create_default_config(config_file)

        # 2. Settings file
        settings_file = self.data_dir / "settings.json"
        if not settings_file.exists():
            self._create_default_settings(settings_file)

        # 🗑️ OLD LICENSE SYSTEM - DISABLED FOR SIMPLIFIED SYSTEM
        # 3. License database (ADMIN ONLY - NOT FOR END USERS)
        # license_file = self.admin_data_dir / "license_database.json"
        # if not license_file.exists():
        #     # Thử copy từ exe bundle trước
        #     if self.is_frozen:
        #         bundled_admin_data = self.app_dir / "admin_data" / "license_database.json"
        #         if bundled_admin_data.exists():
        #             self.admin_data_dir.mkdir(exist_ok=True)
        #             shutil.copy2(bundled_admin_data, license_file)
        #             print(f"✅ Copied license database from bundle: {bundled_admin_data}")
        #         else:
        #             print(f"⚠️ Bundled license database not found: {bundled_admin_data}")
        #             self._create_default_license_db(license_file)
        #     else:
        #         # Dev mode - copy từ source
        #         source_license = self.app_dir / "admin_data" / "license_database.json"
        #         if source_license.exists():
        #             self.admin_data_dir.mkdir(exist_ok=True)
        #             shutil.copy2(source_license, license_file)
        #             print(f"✅ Copied license database from source: {source_license}")
        #         else:
        #             self._create_default_license_db(license_file)
        
        print("🔑 Using SimpleLicenseSystem - No admin license database needed")

        # 4. Workflows file
        workflows_file = self.data_dir / "workflows.json"
        if not workflows_file.exists():
            self._create_default_workflows(workflows_file)

    def _create_default_config(self, config_path):
        """Tạo config mặc định"""
        default_config = """# ClausoNet 4.0 Pro Configuration
# Cấu hình cho các API và tính năng

# API Configuration
apis:
  gemini:
    enabled: true
    api_key: ""  # Nhập API key của bạn
    model: "gemini-2.5-flash"
    max_tokens: 8192
    temperature: 0.7
    top_p: 0.9
    top_k: 40
    rate_limit: 60

  openai:
    enabled: true
    api_key: ""  # Nhập API key của bạn
    model: "gpt-4-turbo"

# Application Settings
app:
  name: "ClausoNet 4.0 Pro"
  version: "1.0.0"

  # Default Settings
  defaults:
    video_format: "mp4"
    video_quality: "high"
    audio_format: "aac"
    max_concurrent_jobs: 3

  # UI Settings
  ui:
    theme: "dark"
    language: "vi"
    auto_save: true
    backup_workflows: true

# Logging Configuration
logging:
  level: "INFO"
  max_size: "10MB"
  backup_count: 5
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Security Settings
security:
  encryption_key: ""
  license_check: true
  hardware_binding: true

# Performance Settings
performance:
  cache_enabled: true
  cache_size: "1GB"
  parallel_processing: true
  gpu_acceleration: false
"""
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(default_config)

    def _create_default_settings(self, settings_path):
        """Tạo settings mặc định"""
        default_settings = {
            "theme": "dark",
            "language": "vi",
            "auto_save": True,
            "last_profile": "",
            "api_keys": {
                "gemini": "",
                "openai": ""
            },
            "preferences": {
                "auto_login": False,
                "save_cookies": True,
                "debug_mode": False
            }
        }
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(default_settings, f, indent=2, ensure_ascii=False)

    def _create_default_license_db(self, license_path):
        """Tạo license database mặc định"""
        default_license = {
            "licenses": [],
            "settings": {
                "require_license": True,
                "trial_days": 7,
                "hardware_binding": True
            }
        }
        with open(license_path, 'w', encoding='utf-8') as f:
            json.dump(default_license, f, indent=2, ensure_ascii=False)

    def _create_default_workflows(self, workflows_path):
        """Tạo workflows mặc định"""
        default_workflows = {
            "workflows": [],
            "templates": [],
            "version": "1.0.0"
        }
        with open(workflows_path, 'w', encoding='utf-8') as f:
            json.dump(default_workflows, f, indent=2, ensure_ascii=False)

    # ===== PHƯƠNG THỨC CÔNG KHAI =====

    def get_data_path(self, filename=""):
        """Lấy đường dẫn đến thư mục/file data"""
        if filename:
            return str(self.data_dir / filename)
        return str(self.data_dir)

    def get_chrome_profiles_path(self, profile_name=""):
        """Lấy đường dẫn đến thư mục Chrome profiles"""
        if profile_name:
            return str(self.chrome_profiles_dir / profile_name)
        return str(self.chrome_profiles_dir)

    def get_output_path(self, filename=""):
        """Lấy đường dẫn đến thư mục output"""
        if filename:
            return str(self.output_dir / filename)
        return str(self.output_dir)

    def get_logs_path(self, filename=""):
        """Lấy đường dẫn đến thư mục logs"""
        if filename:
            return str(self.logs_dir / filename)
        return str(self.logs_dir)

    def get_temp_path(self, filename=""):
        """Lấy đường dẫn đến thư mục temp"""
        if filename:
            return str(self.temp_dir / filename)
        return str(self.temp_dir)

    def get_admin_data_path(self, filename=""):
        """Lấy đường dẫn đến thư mục admin data"""
        if filename:
            return str(self.admin_data_dir / filename)
        return str(self.admin_data_dir)

    def get_config_path(self):
        """Lấy đường dẫn đến file config"""
        return str(self.data_dir / "config.yaml")

    def get_settings_path(self):
        """Lấy đường dẫn đến file settings"""
        return str(self.data_dir / "settings.json")

    def get_license_db_path(self):
        """Lấy đường dẫn đến license database"""
        return str(self.admin_data_dir / "license_database.json")

    def get_workflows_path(self):
        """Lấy đường dẫn đến workflows file"""
        return str(self.data_dir / "workflows.json")

    def find_chrome_executable(self):
        """Tìm Chrome executable trên hệ thống"""
        system = platform.system()

        # Chrome paths cho từng OS
        chrome_paths = {
            "Windows": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                str(Path.home() / "AppData/Local/Google/Chrome/Application/chrome.exe")
            ],
            "Darwin": [  # macOS
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            ],
            "Linux": [
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/snap/bin/chromium"
            ]
        }

        paths = chrome_paths.get(system, [])

        # Tìm Chrome executable
        for path in paths:
            if Path(path).exists():
                return path

        # Thử tìm bằng which/where command
        try:
            import subprocess
            if system == "Windows":
                result = subprocess.run(['where', 'chrome'], capture_output=True, text=True)
            else:
                result = subprocess.run(['which', 'google-chrome'], capture_output=True, text=True)

            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        return None

    def get_bundled_chromedriver_path(self):
        """Lấy đường dẫn đến ChromeDriver được đóng gói (sẽ implement sau)"""
        system = platform.system()

        if self.is_frozen:
            # Khi chạy từ exe, ChromeDriver sẽ được bundle
            if system == "Windows":
                return str(self.app_dir / "drivers" / "chromedriver.exe")
            else:
                return str(self.app_dir / "drivers" / "chromedriver")
        else:
            # Development mode - download tự động
            return None

    def cleanup_temp_files(self):
        """Dọn dẹp file tạm"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(exist_ok=True)
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

    def get_system_info(self):
        """Lấy thông tin hệ thống"""
        return {
            "platform": platform.system(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "is_frozen": self.is_frozen,
            "app_dir": str(self.app_dir),
            "user_data_dir": str(self.user_data_dir)
        }

# Global instance
resource_manager = ResourceManager()
