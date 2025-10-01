#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Build Readiness Checker
Kiểm tra xem dự án đã sẵn sàng cho macOS build trên GitHub chưa
"""

import os
import sys
from pathlib import Path
import json

class BuildReadinessChecker:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.errors = []
        self.warnings = []
        self.checks_passed = 0
        self.checks_total = 0
        
    def check_file_exists(self, filepath, description):
        """Kiểm tra file có tồn tại không"""
        self.checks_total += 1
        full_path = self.project_dir / filepath
        
        if full_path.exists():
            print(f"✅ {description}")
            print(f"   → {filepath}")
            self.checks_passed += 1
            return True
        else:
            print(f"❌ {description}")
            print(f"   → Missing: {filepath}")
            self.errors.append(f"Missing file: {filepath}")
            return False
    
    def check_directory_exists(self, dirpath, description):
        """Kiểm tra thư mục có tồn tại không"""
        self.checks_total += 1
        full_path = self.project_dir / dirpath
        
        if full_path.exists() and full_path.is_dir():
            print(f"✅ {description}")
            print(f"   → {dirpath}")
            self.checks_passed += 1
            return True
        else:
            print(f"❌ {description}")
            print(f"   → Missing directory: {dirpath}")
            self.errors.append(f"Missing directory: {dirpath}")
            return False
    
    def check_requirements_txt(self):
        """Kiểm tra requirements.txt có đầy đủ không"""
        self.checks_total += 1
        req_file = self.project_dir / "requirements.txt"
        
        if not req_file.exists():
            print(f"❌ requirements.txt not found")
            self.errors.append("requirements.txt missing")
            return False
        
        required_packages = [
            'customtkinter',
            'selenium',
            'pillow',
            'pyinstaller',
            'requests',
            'pyyaml'
        ]
        
        with open(req_file, 'r') as f:
            content = f.read().lower()
        
        missing = []
        for pkg in required_packages:
            if pkg not in content:
                missing.append(pkg)
        
        if missing:
            print(f"❌ requirements.txt missing packages: {', '.join(missing)}")
            self.errors.append(f"Missing packages: {missing}")
            return False
        else:
            print(f"✅ requirements.txt has all critical packages")
            print(f"   → Found: {', '.join(required_packages)}")
            self.checks_passed += 1
            return True
    
    def check_workflow_file(self):
        """Kiểm tra workflow file syntax"""
        self.checks_total += 1
        workflow_file = self.project_dir / ".github" / "workflows" / "macos-build-fixed.yml"
        
        if not workflow_file.exists():
            print(f"❌ GitHub workflow file not found")
            self.errors.append("Workflow file missing")
            return False
        
        try:
            # Check basic YAML syntax
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            # Check for critical sections
            critical_sections = ['on:', 'jobs:', 'build-macos:', 'steps:']
            missing_sections = []
            
            for section in critical_sections:
                if section not in content:
                    missing_sections.append(section)
            
            if missing_sections:
                print(f"⚠️ Workflow file missing sections: {', '.join(missing_sections)}")
                self.warnings.append(f"Workflow missing: {missing_sections}")
            else:
                print(f"✅ GitHub workflow file looks valid")
                print(f"   → .github/workflows/macos-build-fixed.yml")
                self.checks_passed += 1
                return True
                
        except Exception as e:
            print(f"❌ Error reading workflow file: {e}")
            self.errors.append(f"Workflow file error: {e}")
            return False
    
    def check_main_entry_point(self):
        """Kiểm tra main entry point"""
        self.checks_total += 1
        main_file = self.project_dir / "gui" / "main_window.py"
        
        if not main_file.exists():
            print(f"❌ Main entry point not found: gui/main_window.py")
            self.errors.append("Main entry point missing")
            return False
        
        # Check file size (should be substantial)
        size = main_file.stat().st_size
        if size < 1000:  # Less than 1KB is suspicious
            print(f"⚠️ Main entry point seems too small ({size} bytes)")
            self.warnings.append("Main file suspiciously small")
        
        print(f"✅ Main entry point found")
        print(f"   → gui/main_window.py ({size:,} bytes)")
        self.checks_passed += 1
        return True
    
    def check_config_template(self):
        """Kiểm tra config template"""
        self.checks_total += 1
        config_template = self.project_dir / "config.yaml.template"
        
        if not config_template.exists():
            print(f"❌ Config template not found")
            self.errors.append("config.yaml.template missing")
            return False
        
        # Check for API key placeholders (not real keys)
        with open(config_template, 'r') as f:
            content = f.read()
        
        # Should have placeholder, not real keys
        if 'YOUR_GEMINI_API_KEY' in content or 'YOUR_OPENAI_API_KEY' in content:
            print(f"✅ Config template has proper placeholders")
            print(f"   → config.yaml.template")
            self.checks_passed += 1
            return True
        else:
            print(f"⚠️ Config template may contain real API keys!")
            self.warnings.append("Config may have real API keys - SECURITY RISK")
            return False
    
    def check_no_secrets(self):
        """Kiểm tra không có secrets trong code"""
        self.checks_total += 1
        
        # Check config.yaml (not template) doesn't have real keys
        config_file = self.project_dir / "config.yaml"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                content = f.read()
            
            # Check for Google API key pattern
            if 'AIzaSy' in content:
                print(f"⚠️ WARNING: config.yaml may contain real Google API key!")
                self.warnings.append("SECURITY: Real API keys in config.yaml")
                return False
            
            # Check for OpenAI key pattern
            if 'sk-' in content and len([line for line in content.split('\n') if 'sk-' in line and len(line) > 50]) > 0:
                print(f"⚠️ WARNING: config.yaml may contain real OpenAI API key!")
                self.warnings.append("SECURITY: Real OpenAI keys in config.yaml")
                return False
        
        print(f"✅ No obvious API keys detected in tracked files")
        self.checks_passed += 1
        return True
    
    def check_git_status(self):
        """Check git status"""
        self.checks_total += 1
        
        git_dir = self.project_dir / ".git"
        if not git_dir.exists():
            print(f"⚠️ Not a git repository")
            self.warnings.append("Not initialized as git repo")
            return False
        
        print(f"✅ Git repository initialized")
        self.checks_passed += 1
        return True
    
    def run_all_checks(self):
        """Chạy tất cả checks"""
        print("=" * 70)
        print("🔍 ClausoNet 4.0 Pro - Build Readiness Check")
        print("=" * 70)
        print()
        
        print("📋 Checking Core Files...")
        print("-" * 70)
        self.check_file_exists("gui/main_window.py", "Main entry point")
        self.check_file_exists("requirements.txt", "Python dependencies")
        self.check_file_exists("config.yaml.template", "Config template")
        print()
        
        print("📋 Checking Core Modules...")
        print("-" * 70)
        self.check_file_exists("core/engine.py", "AI Engine")
        self.check_file_exists("core/content_generator.py", "Content Generator")
        self.check_file_exists("core/simple_license_system.py", "License System")
        print()
        
        print("📋 Checking API Handlers...")
        print("-" * 70)
        self.check_file_exists("api/gemini_handler.py", "Gemini API Handler")
        self.check_file_exists("api/openai_connector.py", "OpenAI Connector")
        print()
        
        print("📋 Checking Utilities...")
        print("-" * 70)
        self.check_file_exists("utils/veo_automation.py", "Veo Automation")
        self.check_file_exists("utils/profile_manager.py", "Profile Manager")
        print()
        
        print("📋 Checking Required Directories...")
        print("-" * 70)
        self.check_directory_exists("data", "Data directory")
        self.check_directory_exists("assets", "Assets directory")
        self.check_directory_exists("admin_tools", "Admin tools directory")
        print()
        
        print("📋 Checking Build Configuration...")
        print("-" * 70)
        self.check_file_exists("build_main_macos.py", "macOS build script")
        self.check_file_exists("admin_tools/build_admin_key_macos.py", "Admin build script")
        self.check_workflow_file()
        print()
        
        print("📋 Checking Dependencies...")
        print("-" * 70)
        self.check_requirements_txt()
        print()
        
        print("📋 Security Checks...")
        print("-" * 70)
        self.check_config_template()
        self.check_no_secrets()
        print()
        
        print("📋 Git Status...")
        print("-" * 70)
        self.check_git_status()
        print()
        
        # Summary
        print("=" * 70)
        print("📊 SUMMARY")
        print("=" * 70)
        
        print(f"\n✅ Checks Passed: {self.checks_passed}/{self.checks_total}")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        print()
        
        # Final verdict
        if self.checks_passed == self.checks_total and not self.errors:
            print("🎉 BUILD READY! All checks passed!")
            print()
            print("📝 Next Steps:")
            print("   1. Commit and push to GitHub")
            print("   2. Go to Actions tab")
            print("   3. Run workflow: '🍎 macOS Build - ClausoNet 4.0 Pro'")
            print("   4. Wait for build completion (~20-30 mins)")
            print("   5. Download artifacts")
            print()
            return True
        elif self.errors:
            print("❌ NOT READY FOR BUILD")
            print("   Please fix the errors above before building.")
            print()
            return False
        else:
            print("⚠️  READY WITH WARNINGS")
            print("   Build may work but review warnings above.")
            print()
            return True

def main():
    checker = BuildReadinessChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

