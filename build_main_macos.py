#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Main Application Builder for macOS
Script để build ClausoNet main application thành .app bundle trên macOS
"""

import os
import sys
import subprocess
import shutil
import json
import platform
from pathlib import Path
from datetime import datetime

class ClausoNetMainBuilderMacOS:
    """Builder cho ClausoNet main application trên macOS"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.build_dir = self.project_dir / "build"
        self.dist_dir = self.project_dir / "dist" 
        self.assets_dir = self.project_dir / "assets"
        self.spec_file = self.project_dir / "clausonet_build.spec"
        
        print("🍎 ClausoNet 4.0 Pro - Main Application Builder for macOS")
        print("=" * 60)
        print(f"🖥️  Platform: {platform.system()} {platform.release()}")
        print(f"📁 Project directory: {self.project_dir}")
        
        # Check if running on macOS
        if platform.system() != "Darwin":
            print("❌ This script must be run on macOS!")
            print("💡 For Windows, use build_fixed_exe.py or build.py")
            sys.exit(1)
            
    def check_dependencies(self):
        """Kiểm tra các dependency cần thiết cho macOS"""
        print("\n🔍 Checking macOS dependencies...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            print(f"❌ Python version {python_version.major}.{python_version.minor} is too old")
            print("💡 Please upgrade to Python 3.8+")
            return False
        else:
            print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Required packages for main application
        required_packages = [
            ('PyInstaller', 'PyInstaller build tool'),
            ('customtkinter', 'GUI framework'),
            ('selenium', 'Web automation'),
            ('requests', 'HTTP client'),
            ('PIL', 'Image processing'),
        ]
        
        missing_packages = []
        
        for package_name, description in required_packages:
            try:
                if package_name == 'PIL':
                    import PIL
                    print(f"✅ {package_name} ({description})")
                else:
                    __import__(package_name.lower())
                    print(f"✅ {package_name} ({description})")
            except ImportError:
                print(f"❌ {package_name} not found - {description}")
                missing_packages.append(package_name)
        
        if missing_packages:
            print(f"\n💡 Install missing packages:")
            for pkg in missing_packages:
                if pkg == 'PIL':
                    print(f"   pip3 install pillow")
                else:
                    print(f"   pip3 install {pkg.lower()}")
            return False
            
        # Check macOS specific tools
        tools_to_check = [
            ('iconutil', 'Icon creation tool'),
            ('sips', 'Image processing tool'),
            ('hdiutil', 'DMG creation tool'),
        ]
        
        for tool, description in tools_to_check:
            try:
                result = subprocess.run(['which', tool], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ {tool} ({description})")
                else:
                    print(f"⚠️ {tool} not found - {description}")
            except Exception:
                print(f"⚠️ Cannot check {tool}")
        
        # Check required files
        required_files = [
            self.spec_file,
            self.project_dir / "gui" / "main_window.py",
        ]
        
        for file_path in required_files:
            if file_path.exists():
                print(f"✅ {file_path.name} found")
            else:
                print(f"❌ {file_path.name} not found")
                return False
        
        return True
        
    def prepare_assets(self):
        """Chuẩn bị assets cho macOS build"""
        print("\n🎨 Preparing assets for macOS...")
        
        # Ensure assets directory exists
        self.assets_dir.mkdir(exist_ok=True)
        
        # Check/create icon
        icon_icns = self.assets_dir / "icon.icns"
        icon_png = self.assets_dir / "icon.png"
        
        if icon_icns.exists():
            print(f"✅ macOS icon found: {icon_icns}")
            return str(icon_icns)
        elif icon_png.exists():
            print(f"🖼️ Converting PNG to ICNS: {icon_png}")
            if self._create_icns_from_png(icon_png, icon_icns):
                return str(icon_icns)
        
        # Create default icon if none found
        print("⚠️ No icon found, creating default...")
        if self._create_default_icon(icon_icns):
            return str(icon_icns)
            
        print("❌ Could not create icon")
        return None
        
    def _create_icns_from_png(self, png_path, icns_path):
        """Tạo .icns từ .png sử dụng sips và iconutil"""
        try:
            # Create iconset directory
            iconset_dir = icns_path.parent / f"{icns_path.stem}.iconset"
            iconset_dir.mkdir(exist_ok=True)
            
            # Define required sizes for macOS
            sizes = [
                (16, "icon_16x16.png"),
                (32, "icon_16x16@2x.png"),
                (32, "icon_32x32.png"),
                (64, "icon_32x32@2x.png"),
                (128, "icon_128x128.png"),
                (256, "icon_128x128@2x.png"),
                (256, "icon_256x256.png"),
                (512, "icon_256x256@2x.png"),
                (512, "icon_512x512.png"),
                (1024, "icon_512x512@2x.png")
            ]
            
            # Create all required sizes using sips
            for size, filename in sizes:
                subprocess.run([
                    'sips', '-z', str(size), str(size),
                    str(png_path),
                    '--out', str(iconset_dir / filename)
                ], capture_output=True)
            
            # Convert to icns using iconutil
            result = subprocess.run([
                'iconutil', '-c', 'icns',
                str(iconset_dir),
                '-o', str(icns_path)
            ], capture_output=True, text=True)
            
            # Clean up iconset directory
            shutil.rmtree(iconset_dir)
            
            if result.returncode == 0:
                print(f"✅ Created ICNS icon: {icns_path}")
                return True
            else:
                print(f"❌ Icon creation failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Icon creation error: {e}")
            return False
            
    def _create_default_icon(self, icns_path):
        """Tạo icon mặc định"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple icon
            img = Image.new('RGBA', (512, 512), (30, 144, 255, 255))  # Dodger blue
            draw = ImageDraw.Draw(img)
            
            # Draw ClausoNet logo concept
            # Main circle
            draw.ellipse([50, 50, 462, 462], fill=(255, 255, 255, 255))
            draw.ellipse([80, 80, 432, 432], fill=(30, 144, 255, 255))
            
            # Inner design
            draw.ellipse([150, 150, 362, 362], fill=(255, 255, 255, 255))
            draw.ellipse([180, 180, 332, 332], fill=(30, 144, 255, 255))
            
            # Center dot
            draw.ellipse([230, 230, 282, 282], fill=(255, 255, 255, 255))
            
            # Add text
            try:
                font_large = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 36)
                font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            draw.text((180, 300), "ClausoNet", fill=(255, 255, 255, 255), font=font_large)
            draw.text((210, 340), "4.0 Pro", fill=(255, 255, 255, 255), font=font_small)
            
            # Save as PNG first
            png_path = icns_path.with_suffix('.png')
            img.save(png_path)
            
            # Convert to icns
            return self._create_icns_from_png(png_path, icns_path)
            
        except ImportError:
            print("⚠️ PIL not available for default icon creation")
            return False
        except Exception as e:
            print(f"❌ Default icon creation error: {e}")
            return False
            
    def check_chromedriver(self):
        """Kiểm tra ChromeDriver"""
        print("\n🚗 Checking ChromeDriver...")
        
        possible_locations = [
            self.project_dir / "drivers" / "chromedriver",
            self.project_dir / "tools" / "chromedriver" / "chromedriver",
        ]
        
        for location in possible_locations:
            if location.exists():
                print(f"✅ ChromeDriver found: {location}")
                return True
                
        print("⚠️ ChromeDriver not found")
        print("💡 Download ChromeDriver for macOS from:")
        print("   https://chromedriver.chromium.org/")
        print("   Place it in drivers/ or tools/chromedriver/")
        return False
        
    def build_app(self):
        """Build .app bundle using PyInstaller"""
        print("\n🔨 Building ClausoNet 4.0 Pro for macOS...")
        
        # Clean previous builds
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            print("🗑️ Cleaned dist directory")
            
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            print("🗑️ Cleaned build directory")
            
        # Prepare assets
        self.prepare_assets()
        
        # Build command
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm", 
            str(self.spec_file)
        ]
        
        print(f"🚀 Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, cwd=self.project_dir, 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Build successful!")
                
                # Check if .app was created
                app_path = self.dist_dir / "ClausoNet 4.0 Pro.app"
                if app_path.exists():
                    print(f"✅ .app bundle created: {app_path}")
                    
                    # Get app size
                    size = self._get_directory_size(app_path)
                    print(f"📏 App bundle size: {size / 1024 / 1024:.1f} MB")
                    
                    return True
                else:
                    print(f"❌ .app bundle not found at: {app_path}")
                    print("Available files:")
                    if self.dist_dir.exists():
                        for item in self.dist_dir.iterdir():
                            print(f"  - {item}")
                    return False
            else:
                print("❌ Build failed!")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False
            
    def _get_directory_size(self, path):
        """Tính kích thước thư mục"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception:
            pass
        return total_size
        
    def create_dmg(self):
        """Tạo DMG file cho distribution"""
        print("\n💿 Creating DMG for distribution...")
        
        app_path = self.dist_dir / "ClausoNet 4.0 Pro.app"
        if not app_path.exists():
            print("❌ .app bundle not found, cannot create DMG")
            return None
            
        dmg_name = f"ClausoNet_4.0_Pro_macOS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dmg"
        dmg_path = self.project_dir / dmg_name
        
        try:
            cmd = [
                'hdiutil', 'create',
                '-srcfolder', str(app_path),
                '-volname', 'ClausoNet 4.0 Pro',
                '-format', 'UDZO',  # Compressed
                '-imagekey', 'zlib-level=9',  # Maximum compression
                str(dmg_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Created DMG: {dmg_path}")
                print(f"📏 DMG size: {dmg_path.stat().st_size / 1024 / 1024:.1f} MB")
                return dmg_path
            else:
                print(f"❌ DMG creation failed: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Failed to create DMG: {e}")
            return None
            
    def create_deployment_package(self):
        """Tạo package deployment hoàn chỉnh"""
        print("\n📦 Creating deployment package...")
        
        package_dir = self.project_dir / "macos_deployment_package"
        
        # Clean and create package directory
        if package_dir.exists():
            shutil.rmtree(package_dir)
        package_dir.mkdir()
        
        # Copy .app bundle
        app_source = self.dist_dir / "ClausoNet 4.0 Pro.app"
        app_dest = package_dir / "ClausoNet 4.0 Pro.app"
        
        if app_source.exists():
            shutil.copytree(app_source, app_dest)
            print(f"✅ Copied .app bundle: {app_dest}")
        else:
            print(f"❌ .app bundle not found: {app_source}")
            return False
            
        # Create installation instructions
        readme_content = f'''# ClausoNet 4.0 Pro - macOS Installation

## Installation

1. **Drag and Drop**:
   - Drag "ClausoNet 4.0 Pro.app" to your Applications folder
   - Or run directly from this location

2. **First Launch**:
   - Double-click the app to launch
   - If you see a security warning:
     - Right-click → Open → Open anyway
     - Or go to System Preferences → Security & Privacy → Allow

3. **Alternative Security Fix**:
   ```bash
   xattr -d com.apple.quarantine "ClausoNet 4.0 Pro.app"
   ```

## System Requirements

- macOS 10.14+ (Mojave or later)
- 4GB+ RAM recommended
- 1GB+ free disk space
- Internet connection for video generation

## Features

- AI-powered video generation
- Modern macOS-native interface
- Automated workflow processing
- License key activation system

## Support

- Email: support@clausonet.com
- Version: 4.0.1
- Build Date: {datetime.now().strftime("%Y-%m-%d")}

## Security Notes

This application is distributed outside the Mac App Store and may trigger
Gatekeeper warnings. This is normal for developer-distributed software.

---
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Platform: macOS
'''
        
        readme_file = package_dir / "README_INSTALLATION.txt"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"✅ Created installation guide: {readme_file}")
        
        # Create launcher script (optional)
        launcher_script = '''#!/bin/bash
# ClausoNet 4.0 Pro Launcher for macOS

echo "🍎 Launching ClausoNet 4.0 Pro..."
open "ClausoNet 4.0 Pro.app"
'''
        
        launcher_file = package_dir / "Launch_ClausoNet.sh"
        with open(launcher_file, 'w', encoding='utf-8') as f:
            f.write(launcher_script)
        os.chmod(launcher_file, 0o755)
        print(f"✅ Created launcher script: {launcher_file}")
        
        print(f"✅ Deployment package created: {package_dir}")
        return True
        
    def run_full_build(self):
        """Chạy toàn bộ quá trình build cho macOS"""
        print("🚀 Starting ClausoNet 4.0 Pro macOS build process...")
        print("=" * 60)
        
        steps = [
            ("Check dependencies", self.check_dependencies),
            ("Check ChromeDriver", self.check_chromedriver),
            ("Build .app bundle", self.build_app),
            ("Create DMG", self.create_dmg),
            ("Create deployment package", self.create_deployment_package)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 Step: {step_name}")
            
            if step_name == "Check ChromeDriver":
                # This is not critical, just show warning
                step_func()
                continue
                
            result = step_func()
            
            if step_name == "Create DMG":
                # This step returns the DMG path or None
                if result is None:
                    print(f"⚠️ Warning: {step_name} failed, but continuing...")
                    continue
            elif step_name == "Create deployment package":
                if not result:
                    print(f"⚠️ Warning: {step_name} failed, but .app is ready")
                    continue
            elif not result:
                print(f"❌ Failed at: {step_name}")
                print("\n💡 Please fix the issues above and try again")
                return False
                
        print("\n" + "=" * 60)
        print("🎉 ClausoNet 4.0 Pro macOS BUILD COMPLETE!")
        print("=" * 60)
        print()
        print("📋 What was created:")
        print(f"   📱 App: dist/ClausoNet 4.0 Pro.app")
        print(f"   💿 DMG: ClausoNet_4.0_Pro_macOS_*.dmg")
        print(f"   📦 Package: macos_deployment_package/")
        print()
        print("📋 Next steps:")
        print("1. Test the .app locally:")
        print("   open 'dist/ClausoNet 4.0 Pro.app'")
        print("2. Distribute the DMG file to end users")
        print("3. Users can drag .app to Applications folder")
        print()
        print("🍎 macOS Distribution Notes:")
        print("   - First run requires security approval")
        print("   - Provide installation instructions to users")
        print("   - DMG file is ready for distribution")
        print("   - No code signing required for internal distribution")
        
        return True

def main():
    """Main function"""
    try:
        builder = ClausoNetMainBuilderMacOS()
        
        if len(sys.argv) > 1 and sys.argv[1] == "--quick":
            # Quick build - minimal checks
            print("⚡ Quick build mode")
            builder.build_app()
            builder.create_dmg()
        else:
            # Full build process
            builder.run_full_build()
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Build cancelled by user")
    except Exception as e:
        print(f"\n❌ Build failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 