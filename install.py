#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Installation Script
Tự động cài đặt tất cả dependencies và thiết lập môi trường
"""

import os
import sys
import subprocess
import platform
import json
from pathlib import Path

def run_command(command, description=""):
    """Chạy command và hiển thị kết quả"""
    print(f"\n{'='*50}")
    if description:
        print(f"📦 {description}")
    print(f"🔄 Executing: {command}")
    print(f"{'='*50}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Success!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Kiểm tra phiên bản Python"""
    print("🐍 Checking Python version...")
    version = sys.version_info

    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def check_pip():
    """Kiểm tra pip"""
    print("📦 Checking pip...")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"],
                              capture_output=True, text=True, check=True)
        print(f"✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print("❌ pip not found")
        return False

def upgrade_pip():
    """Upgrade pip"""
    return run_command(
        f'"{sys.executable}" -m pip install --upgrade pip',
        "Upgrading pip"
    )

def install_requirements():
    """Cài đặt requirements.txt"""
    requirements_file = Path(__file__).parent / "requirements.txt"

    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        return False

    return run_command(
        f'"{sys.executable}" -m pip install -r "{requirements_file}"',
        "Installing requirements from requirements.txt"
    )

def install_optional_gpu():
    """GPU support not needed for API-only version"""
    print("\n🎮 GPU Support Installation")
    print("⏭️ Skipping GPU support - using API-only mode")
    return True

def install_ffmpeg():
    """Cài đặt FFmpeg"""
    print("\n🎬 FFmpeg Installation")
    system = platform.system().lower()

    if system == "windows":
        print("📋 For Windows:")
        print("1. Download FFmpeg from: https://ffmpeg.org/download.html")
        print("2. Extract to C:\\ffmpeg")
        print("3. Add C:\\ffmpeg\\bin to your PATH environment variable")
        print("4. Restart your command prompt")

        choice = input("Have you installed FFmpeg? [y/N]: ").lower()
        return choice in ['y', 'yes']

    elif system == "linux":
        print("🐧 Installing FFmpeg on Linux...")
        # Try different package managers
        commands = [
            "sudo apt-get update && sudo apt-get install -y ffmpeg",
            "sudo yum install -y ffmpeg",
            "sudo dnf install -y ffmpeg",
            "sudo pacman -S ffmpeg"
        ]

        for cmd in commands:
            if run_command(cmd, f"Installing FFmpeg with {cmd.split()[1]}"):
                return True

        print("❌ Could not install FFmpeg automatically")
        print("Please install FFmpeg manually for your Linux distribution")
        return False

    elif system == "darwin":
        print("🍎 Installing FFmpeg on macOS...")
        if run_command("brew install ffmpeg", "Installing FFmpeg with Homebrew"):
            return True
        else:
            print("❌ Homebrew not found or failed")
            print("Please install Homebrew first: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            return False

    return False

def create_config_file():
    """Tạo file config mẫu"""
    config_file = Path(__file__).parent / "config.yaml"

    if config_file.exists():
        choice = input("config.yaml already exists. Overwrite? [y/N]: ").lower()
        if choice not in ['y', 'yes']:
            print("⏭️ Keeping existing config.yaml")
            return True

    config_content = """# ClausoNet 4.0 Pro Configuration
# Replace with your actual API keys

google_veo3:
  project_id: "your-google-project-id"
  location: "us-central1"
  api_key: "your-google-api-key"
  model_version: "veo-3-preview"
  max_duration: 60
  resolution: "1080p"
  rate_limit: 10

gemini:
  api_key: "your-gemini-api-key"
  model: "gemini-pro"
  max_tokens: 8192
  temperature: 0.7
  top_p: 0.9
  top_k: 40
  rate_limit: 60

openai:
  api_key: "your-openai-api-key"
  organization: "your-openai-organization"  # optional
  model: "gpt-4-turbo"
  max_tokens: 4096
  temperature: 0.7
  top_p: 1.0
  frequency_penalty: 0.0
  presence_penalty: 0.0
  rate_limit: 500

# System settings
system:
  log_level: "INFO"
  log_file: "logs/clausonet.log"
  output_directory: "output"
  temp_directory: "temp"
  cache_directory: "data/cache"

# GUI settings
gui:
  theme: "dark"
  language: "en"
  window_size: [1200, 800]
  auto_save: true

# Performance settings
performance:
  max_workers: 4
  chunk_size: 1024
  cache_enabled: true
  gpu_acceleration: false
"""

    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        print(f"✅ Created config template: {config_file}")
        print("📝 Please edit config.yaml with your actual API keys")
        return True
    except Exception as e:
        print(f"❌ Failed to create config.yaml: {e}")
        return False

def create_directories():
    """Tạo các thư mục cần thiết"""
    directories = [
        "logs",
        "output",
        "temp",
        "data/cache",
        "data/assets",
        "data/templates"
    ]

    print("📁 Creating directories...")
    base_path = Path(__file__).parent

    for dir_name in directories:
        dir_path = base_path / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created: {dir_path}")
        except Exception as e:
            print(f"❌ Failed to create {dir_path}: {e}")
            return False

    return True



def main():
    """Main installation process"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    ClausoNet 4.0 Pro                        ║
║                   Installation Script                       ║
║                                                              ║
║         Advanced AI Video Generation Tool                   ║
╚══════════════════════════════════════════════════════════════╝
    """)

    print("🚀 Starting installation process...")

    # Check system requirements
    if not check_python_version():
        print("❌ Python version requirement not met!")
        sys.exit(1)

    if not check_pip():
        print("❌ pip not available!")
        sys.exit(1)

    # Installation steps
    steps = [
        ("Upgrading pip", upgrade_pip),
        ("Installing Python packages", install_requirements),
        ("Installing optional GPU support", install_optional_gpu),
        ("Installing FFmpeg", install_ffmpeg),
        ("Creating directories", create_directories),
        ("Creating config file", create_config_file),
        ("Testing installation", test_installation)
    ]

    failed_steps = []

    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        if not step_func():
            failed_steps.append(step_name)
            print(f"⚠️ {step_name} failed, but continuing...")

    # Summary
    print(f"\n{'='*60}")
    print("📋 INSTALLATION SUMMARY")
    print(f"{'='*60}")

    if failed_steps:
        print("⚠️ Some steps failed:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\nPlease check the errors above and install manually if needed.")
    else:
        print("✅ All steps completed successfully!")

    print(f"\n📝 Next steps:")
    print(f"1. Edit config.yaml with your API keys")
    print(f"2. Run: python -m core.engine --help")
    print(f"3. Test API connections: python -m api --test")

    print(f"\n🎉 ClausoNet 4.0 Pro installation completed!")

if __name__ == "__main__":
    main()
