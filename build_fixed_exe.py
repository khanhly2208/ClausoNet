#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Enhanced Build Script with Profile & Automation Fixes
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

class FixedBuilder:
    """Enhanced builder với fixes cho profile & automation"""

    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.system = platform.system()
        
        print(f"🚀 ClausoNet 4.0 Pro - Fixed Builder")
        print(f"📁 Project: {self.project_dir}")
        print(f"💻 Platform: {self.system}")
        print("=" * 60)

    def check_pyinstaller(self):
        """Check if PyInstaller is available"""
        try:
            import PyInstaller
            print(f"✅ PyInstaller version: {PyInstaller.__version__}")
            return True
        except ImportError:
            print("❌ PyInstaller not found")
            print("Installing PyInstaller...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
                print("✅ PyInstaller installed successfully")
                return True
            except subprocess.CalledProcessError:
                print("❌ Failed to install PyInstaller")
                return False

    def verify_fixes(self):
        """Verify that all fixes are in place"""
        print("🔍 Verifying fixes...")
        
        fixes_status = {}
        
        # Check Profile Manager fix
        profile_manager_path = self.project_dir / "utils" / "profile_manager.py"
        if profile_manager_path.exists():
            content = profile_manager_path.read_text(encoding='utf-8')
            if "resource_manager.chrome_profiles_dir" in content:
                fixes_status['profile_manager'] = "✅ ResourceManager integration"
            else:
                fixes_status['profile_manager'] = "❌ Missing ResourceManager integration"
        
        # Check Main Window cookies fix
        main_window_path = self.project_dir / "gui" / "main_window.py"
        if main_window_path.exists():
            content = main_window_path.read_text(encoding='utf-8')
            if "resource_manager.data_dir" in content:
                fixes_status['cookies_path'] = "✅ Cookie path fix"
            else:
                fixes_status['cookies_path'] = "❌ Missing cookie path fix"
            
            if "ProductionChromeDriverManager" in content:
                fixes_status['chrome_manager'] = "✅ Chrome manager fix"
            else:
                fixes_status['chrome_manager'] = "❌ Missing Chrome manager fix"
        
        # Check Spec file fix
        spec_path = self.project_dir / "clausonet_build.spec"
        if spec_path.exists():
            content = spec_path.read_text(encoding='utf-8')
            if "license_database.json" in content:
                fixes_status['spec_license'] = "✅ License database in spec"
            else:
                fixes_status['spec_license'] = "❌ Missing license database in spec"
        
        print("📋 Fixes Status:")
        for fix_name, status in fixes_status.items():
            print(f"   {status} - {fix_name}")
        
        # Check if all fixes are OK
        all_fixes_ok = all("✅" in status for status in fixes_status.values())
        
        if all_fixes_ok:
            print("✅ All fixes verified successfully!")
        else:
            print("❌ Some fixes are missing!")
            
        return all_fixes_ok

    def check_license_database(self):
        """Check license database"""
        print("🔑 Checking license database...")
        
        # Check in user directory (ResourceManager path)
        try:
            from utils.resource_manager import resource_manager
            license_path = Path(resource_manager.admin_data_dir) / "license_database.json"
            
            if license_path.exists():
                print(f"✅ License database found: {license_path}")
                
                # Check content
                import json
                with open(license_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                keys_count = len(data.get('keys', []))
                print(f"📊 Database contains {keys_count} license keys")
                
                if keys_count > 0:
                    print("✅ License database is populated")
                    return True
                else:
                    print("⚠️ License database is empty")
                    return False
            else:
                print(f"❌ License database not found at: {license_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking license database: {e}")
            return False

    def check_chromedriver(self):
        """Check ChromeDriver"""
        print("🚗 Checking ChromeDriver...")
        
        drivers_dir = self.project_dir / "drivers"
        driver_name = "chromedriver.exe" if self.system == "Windows" else "chromedriver"
        driver_path = drivers_dir / driver_name
        
        if driver_path.exists():
            print(f"✅ ChromeDriver found: {driver_path}")
            return True
        else:
            print(f"❌ ChromeDriver not found: {driver_path}")
            print("💡 Please download ChromeDriver and place it in drivers/ directory")
            return False

    def build_exe(self):
        """Build executable using PyInstaller"""
        print("🔨 Building executable...")
        
        spec_file = self.project_dir / "clausonet_build.spec"
        if not spec_file.exists():
            print(f"❌ Spec file not found: {spec_file}")
            return False
        
        # Clean previous build
        dist_dir = self.project_dir / "dist"
        build_dir = self.project_dir / "build"
        
        if dist_dir.exists():
            import shutil
            shutil.rmtree(dist_dir)
            print("🗑️ Cleaned dist directory")
            
        if build_dir.exists():
            import shutil
            shutil.rmtree(build_dir)
            print("🗑️ Cleaned build directory")
        
        # Build command
        cmd = [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", str(spec_file)]
        
        print(f"🚀 Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, cwd=str(self.project_dir), 
                                  capture_output=True, text=True, timeout=900)  # 15 minutes
            
            if result.returncode == 0:
                print("✅ Build successful!")
                
                # Check output
                if self.system == "Windows":
                    exe_path = dist_dir / "ClausoNet4.0Pro.exe"
                    if exe_path.exists():
                        size_mb = exe_path.stat().st_size / (1024 * 1024)
                        print(f"📊 Executable: {exe_path} ({size_mb:.1f} MB)")
                        return True
                elif self.system == "Darwin":
                    app_path = dist_dir / "ClausoNet 4.0 Pro.app"
                    if app_path.exists():
                        print(f"📊 App Bundle: {app_path}")
                        return True
                
                print("⚠️ Build completed but executable not found")
                return False
            else:
                print(f"❌ Build failed:")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Build timeout (15 minutes)")
            return False
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False

    def create_test_script(self):
        """Create test script for the built exe"""
        test_script = f"""
@echo off
echo 🧪 Testing ClausoNet 4.0 Pro Executable
echo =======================================

echo 📁 Checking executable...
if exist "dist\\ClausoNet4.0Pro.exe" (
    echo ✅ Executable found
    
    echo 🚀 Starting ClausoNet 4.0 Pro...
    echo 💡 Check the following:
    echo    1. License activation works
    echo    2. Profile creation works
    echo    3. Cookie extraction works  
    echo    4. Workflow automation works
    echo    5. Google Veo integration works
    
    start /wait "ClausoNet Test" "dist\\ClausoNet4.0Pro.exe"
    
    echo ✅ Test complete
) else (
    echo ❌ Executable not found!
    echo Please build the project first
)

pause
"""
        
        test_file = self.project_dir / "test_exe.bat"
        test_file.write_text(test_script, encoding='utf-8')
        print(f"✅ Created test script: {test_file}")

    def run_full_build(self):
        """Run complete build process"""
        print("🚀 Starting complete build process...")
        print("=" * 60)
        
        steps = [
            ("Check PyInstaller", self.check_pyinstaller),
            ("Verify fixes", self.verify_fixes),
            ("Check license database", self.check_license_database),
            ("Check ChromeDriver", self.check_chromedriver),
            ("Build executable", self.build_exe),
            ("Create test script", self.create_test_script),
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 Step: {step_name}")
            if step_name == "Create test script":
                # Always create test script
                step_func()
            else:
                result = step_func()
                if not result:
                    print(f"❌ Failed at: {step_name}")
                    print("\n💡 Please fix the issues above and try again")
                    return False
        
        print("\n" + "=" * 60)
        print("🎉 BUILD PROCESS COMPLETE!")
        print("=" * 60)
        print()
        print("📋 Next steps:")
        print("1. Run test_exe.bat to test the executable")
        print("2. Test profile creation and automation")
        print("3. Verify Google Veo integration works")
        print("4. Check license activation on different machines")
        print()
        print("🎯 Built executable:")
        if self.system == "Windows":
            print("   dist/ClausoNet4.0Pro.exe")
        elif self.system == "Darwin":
            print("   dist/ClausoNet 4.0 Pro.app")
            
        return True

def main():
    """Main function"""
    builder = FixedBuilder()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "verify":
            builder.verify_fixes()
        elif command == "license":
            builder.check_license_database()
        elif command == "chrome":
            builder.check_chromedriver()
        elif command == "build":
            builder.build_exe()
        elif command == "test":
            builder.create_test_script()
        elif command == "all":
            builder.run_full_build()
        else:
            print("❌ Unknown command:", command)
            print("Usage: python build_fixed_exe.py [verify|license|chrome|build|test|all]")
    else:
        # Default: full build
        builder.run_full_build()

if __name__ == "__main__":
    main()
