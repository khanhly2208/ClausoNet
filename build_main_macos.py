#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - macOS Build Script
Builds the main application for macOS using PyInstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

class MacOSMainBuilder:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.dist_dir = self.project_dir / "dist"
        self.build_dir = self.project_dir / "build"
        self.app_name = "ClausoNet 4.0 Pro"
        
    def clean_build_dirs(self):
        """Clean previous build artifacts"""
        print("🧹 Cleaning previous build...")
        for dir_path in [self.dist_dir, self.build_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"   Removed: {dir_path}")
        
    def check_requirements(self):
        """Check if all required files exist"""
        print("🔍 Checking requirements...")
        
        required_files = [
            "gui/main_window.py",
            "config.yaml.template"
        ]
        
        required_dirs = [
            "data",
            "assets", 
            "api",
            "core",
            "utils"
        ]
        
        missing = []
        
        for file_path in required_files:
            if not (self.project_dir / file_path).exists():
                missing.append(f"File: {file_path}")
                
        for dir_path in required_dirs:
            if not (self.project_dir / dir_path).exists():
                missing.append(f"Directory: {dir_path}")
                
        if missing:
            print("❌ Missing requirements:")
            for item in missing:
                print(f"   - {item}")
            return False
            
        print("✅ All requirements found")
        return True
        
    def prepare_config(self):
        """Prepare config.yaml from template"""
        print("⚙️ Preparing configuration...")
        
        template_file = self.project_dir / "config.yaml.template"
        config_file = self.project_dir / "config.yaml"
        
        if template_file.exists():
            shutil.copy2(template_file, config_file)
            print(f"   Copied: {template_file} -> {config_file}")
        else:
            print("⚠️ config.yaml.template not found, creating minimal config...")
            with open(config_file, 'w') as f:
                f.write("""# ClausoNet 4.0 Pro Configuration
apis:
  gemini:
    enabled: true
    api_key: "YOUR_GEMINI_API_KEY"
    model: "gemini-2.5-flash"
""")
            
    def prepare_icon(self):
        """Prepare macOS icon"""
        print("🎨 Preparing icon...")
        
        assets_dir = self.project_dir / "assets"
        icon_icns = assets_dir / "icon.icns"
        icon_png = assets_dir / "icon.png"
        
        if not icon_icns.exists() and icon_png.exists():
            print("   Converting PNG to ICNS...")
            try:
                # Create iconset directory
                iconset_dir = assets_dir / "icon.iconset"
                iconset_dir.mkdir(exist_ok=True)
                
                # Generate different sizes
                sizes = [16, 32, 128, 256, 512]
                for size in sizes:
                    cmd = [
                        "sips", "-z", str(size), str(size), 
                        str(icon_png), 
                        "--out", str(iconset_dir / f"icon_{size}x{size}.png")
                    ]
                    subprocess.run(cmd, check=True, capture_output=True)
                    
                    # Create @2x versions
                    if size <= 256:
                        cmd = [
                            "sips", "-z", str(size*2), str(size*2),
                            str(icon_png),
                            "--out", str(iconset_dir / f"icon_{size}x{size}@2x.png")
                        ]
                        subprocess.run(cmd, check=True, capture_output=True)
                
                # Convert to icns
                cmd = ["iconutil", "-c", "icns", str(iconset_dir)]
                subprocess.run(cmd, check=True, capture_output=True)
                
                print(f"   Created: {icon_icns}")
                
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Icon conversion failed: {e}")
                
        elif icon_icns.exists():
            print(f"   Using existing: {icon_icns}")
        else:
            print("⚠️ No icon found, will use default")
            
    def build_app(self):
        """Build the macOS app using PyInstaller"""
        print("🏗️ Building macOS application...")
        
        # PyInstaller command
        cmd = [
            "pyinstaller",
            "--clean",
            "--noconfirm",
            "--name", self.app_name,
            "--windowed",
            "--onedir",
            "--add-data", "data:data",
            "--add-data", "assets:assets",
            "--add-data", "config.yaml:.",
            "--hidden-import", "tkinter",
            "--hidden-import", "customtkinter", 
            "--hidden-import", "selenium",
            "--hidden-import", "PIL",
            "--hidden-import", "requests",
            "--hidden-import", "yaml",
            "--hidden-import", "json",
            "--exclude-module", "pytest",
            "--exclude-module", "unittest",
            str(self.project_dir / "gui" / "main_window.py")
        ]
        
        # Add icon if available
        icon_path = self.project_dir / "assets" / "icon.icns"
        if icon_path.exists():
            cmd.extend(["--icon", str(icon_path)])
            
        print(f"   Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ Build completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed: {e}")
            print(f"   stdout: {e.stdout}")
            print(f"   stderr: {e.stderr}")
            return False
            
    def verify_build(self):
        """Verify the built application"""
        print("🔍 Verifying build...")
        
        app_path = self.dist_dir / f"{self.app_name}.app"
        
        if not app_path.exists():
            print(f"❌ App not found: {app_path}")
            return False
            
        # Check app structure
        contents_dir = app_path / "Contents"
        macos_dir = contents_dir / "MacOS"
        
        if not contents_dir.exists():
            print(f"❌ Contents directory missing: {contents_dir}")
            return False
            
        if not macos_dir.exists():
            print(f"❌ MacOS directory missing: {macos_dir}")
            return False
            
        # List contents
        print(f"✅ App structure:")
        print(f"   📁 {app_path}")
        print(f"   📁 {contents_dir}")
        for item in contents_dir.iterdir():
            print(f"      📄 {item.name}")
            
        print(f"   📁 {macos_dir}")
        for item in macos_dir.iterdir():
            print(f"      🔧 {item.name}")
            
        return True
        
    def cleanup(self):
        """Clean up temporary files"""
        print("🧹 Cleaning up...")
        
        # Remove temporary config.yaml if created from template
        config_file = self.project_dir / "config.yaml"
        template_file = self.project_dir / "config.yaml.template"
        
        if config_file.exists() and template_file.exists():
            # Only remove if it matches template (no real API keys)
            with open(config_file, 'r') as f:
                content = f.read()
            if "YOUR_GEMINI_API_KEY" in content:
                config_file.unlink()
                print("   Removed temporary config.yaml")
                
        # Remove build directory but keep dist
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            print("   Removed build directory")
            
    def build(self):
        """Main build process"""
        print(f"🍎 Building {self.app_name} for macOS")
        print(f"📁 Project: {self.project_dir}")
        
        # Build steps
        steps = [
            ("Clean", self.clean_build_dirs),
            ("Check Requirements", self.check_requirements),
            ("Prepare Config", self.prepare_config),
            ("Prepare Icon", self.prepare_icon),
            ("Build App", self.build_app),
            ("Verify Build", self.verify_build),
            ("Cleanup", self.cleanup)
        ]
        
        for step_name, step_func in steps:
            print(f"\n🔄 {step_name}...")
            try:
                if not step_func():
                    print(f"❌ {step_name} failed")
                    return False
            except Exception as e:
                print(f"❌ {step_name} error: {e}")
                return False
                
        print(f"\n🎉 Build completed successfully!")
        print(f"📦 Output: {self.dist_dir / f'{self.app_name}.app'}")
        return True

def main():
    """Main entry point"""
    builder = MacOSMainBuilder()
    success = builder.build()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 