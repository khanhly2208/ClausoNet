# 🍎 ClausoNet 4.0 Pro - macOS Build Guide on GitHub

## 📋 Mục Lục
1. [Tổng Quan](#tổng-quan)
2. [Chuẩn Bị Repository](#chuẩn-bị-repository)
3. [Cấu Hình GitHub Actions](#cấu-hình-github-actions)
4. [Chạy Build Workflow](#chạy-build-workflow)
5. [Troubleshooting](#troubleshooting)

---

## 🎯 Tổng Quan

### Build System
- **CI/CD**: GitHub Actions
- **Runner**: macos-latest
- **Build Tool**: PyInstaller 6.0+
- **Python**: 3.11
- **Output**: .app bundle + DMG installer

### Artifacts Created
1. **ClausoNet 4.0 Pro.app** - Main application
2. **Admin Tools** - Key generator .app
3. **DMG Files** - Distribution disk images
4. **ZIP Package** - Full release package

---

## 📦 Phase 1: Chuẩn Bị Repository

### Step 1.1: Kiểm Tra File Cần Thiết

**Checklist file bắt buộc:**
```bash
# Main application files
✅ gui/main_window.py           # Entry point (17,247 lines)
✅ requirements.txt              # Python dependencies
✅ config.yaml.template          # Configuration template

# Core modules
✅ core/engine.py
✅ core/content_generator.py
✅ core/simple_license_system.py

# API handlers
✅ api/gemini_handler.py
✅ api/openai_connector.py

# Utilities
✅ utils/veo_automation.py
✅ utils/profile_manager.py
✅ utils/resource_manager.py

# Assets
✅ assets/icon.png              # For .icns conversion

# Admin tools
✅ admin_tools/admin_key_gui.py
✅ admin_tools/build_admin_key_macos.py

# Build configuration
✅ .github/workflows/macos-build-fixed.yml
✅ build_main_macos.py
```

**Command để kiểm tra:**
```bash
cd ClausoNet4.0

# Check main files
ls -la gui/main_window.py requirements.txt config.yaml.template

# Check core modules
ls -la core/engine.py core/content_generator.py

# Check build scripts
ls -la build_main_macos.py admin_tools/build_admin_key_macos.py

# Check workflow
ls -la .github/workflows/macos-build-fixed.yml
```

### Step 1.2: Verify requirements.txt

**Nội dung hiện tại:**
```
customtkinter>=5.2.0
selenium>=4.15.0
requests>=2.31.0
pillow>=10.0.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
certifi>=2023.7.22
urllib3>=2.0.0
psutil>=5.9.0
pyperclip>=1.8.0
pyyaml>=6.0.0
pyinstaller>=6.0.0
packaging>=23.0
setuptools>=68.0.0
```

**✅ OK - Đã có đầy đủ!**

### Step 1.3: Check Icon Assets

```bash
# Verify icon exists
ls -la assets/icon.png

# If not, create default icon
cd assets
python3 create_png.py  # If script exists
```

---

## ⚙️ Phase 2: Cấu Hình GitHub Actions

### Step 2.1: Verify Workflow File

**File:** `.github/workflows/macos-build-fixed.yml`

**Đã được cập nhật với:**
- ✅ Enhanced security scan (OpenAI, Google API keys)
- ✅ Better error handling
- ✅ Build verification steps
- ✅ DMG creation
- ✅ Auto-release enabled

### Step 2.2: Setup GitHub Repository

**1. Push code lên GitHub:**
```bash
cd ClausoNet4.0

# Initialize git if not yet
git init

# Add all files
git add .

# Commit
git commit -m "Add macOS build workflow with enhanced security"

# Add remote (replace with your repo)
git remote add origin https://github.com/YOUR_USERNAME/ClausoNet4.0.git

# Push
git push -u origin main
```

**2. Enable GitHub Actions:**
- Go to GitHub repository
- Click **"Actions"** tab
- If disabled, click **"I understand my workflows, go ahead and enable them"**

### Step 2.3: Configure Repository Secrets (Optional)

**For Code Signing:**
```
Settings → Secrets and variables → Actions → New repository secret

Name: MACOS_CERTIFICATE_NAME
Value: Your Apple Developer certificate name
```

**Note:** Code signing không bắt buộc cho testing, nhưng cần cho distribution.

---

## 🚀 Phase 3: Chạy Build Workflow

### Method 1: Manual Trigger (Khuyến Nghị cho Testing)

**Steps:**
1. Go to **Actions** tab on GitHub
2. Click **"🍎 macOS Build - ClausoNet 4.0 Pro"** workflow
3. Click **"Run workflow"** button (bên phải)
4. Select options:
   - **Branch:** main
   - **Build type:** release
5. Click **"Run workflow"** (green button)

**Screenshot guide:**
```
GitHub → Actions → [Your Workflow] → Run workflow ▼
  ┌─────────────────────────────┐
  │ Use workflow from           │
  │ Branch: main            ▼   │
  │                             │
  │ Build type                  │
  │ ○ release  ○ debug          │
  │                             │
  │ [Run workflow]              │
  └─────────────────────────────┘
```

### Method 2: Push to Main Branch

```bash
# Make any change to trigger workflow
cd ClausoNet4.0

# Edit a file or just re-commit
git commit --allow-empty -m "Trigger macOS build"

# Push
git push origin main
```

**Workflow sẽ tự động chạy khi:**
- Push to `main` branch
- Push to `develop` branch  
- Create tag with `v*` pattern
- Open Pull Request to `main`

### Method 3: Create Release Tag

```bash
# Tag current commit
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push tag
git push origin v1.0.0
```

**→ Workflow chạy + tạo GitHub Release tự động!**

---

## 📊 Phase 4: Monitor Build Process

### Step 4.1: Watch Build Progress

**1. Go to Actions tab:**
```
GitHub → Actions → Click on running workflow
```

**2. Build stages (4 jobs):**
```
🔒 security-scan       (~2 minutes)
  ├─ Scan for secrets
  └─ Check API keys

🍎 build-macos        (~15-25 minutes)
  ├─ Setup Python 3.11
  ├─ Install dependencies
  ├─ Prepare assets (icon)
  ├─ Build main app
  ├─ Build admin tools
  ├─ Create DMG files
  └─ Package everything

🎉 create-release     (~3 minutes)
  ├─ Download artifacts
  ├─ Create ZIP package
  └─ Create GitHub Release

📊 build-summary      (~1 minute)
  └─ Generate summary report
```

**Total time: ~20-30 minutes**

### Step 4.2: Read Build Logs

**Check for errors:**
```
Click on job → Expand steps → Read output

Common log patterns:
✅ Success indicators:
   "✅ Dependencies verified"
   "✅ Main app built successfully"
   "✅ DMG created"

❌ Error indicators:
   "❌ Build failed"
   "ImportError: No module named"
   "FileNotFoundError"
```

---

## 📥 Phase 5: Download Artifacts

### Method 1: From Actions Artifacts

**Steps:**
1. Go to completed workflow run
2. Scroll down to **"Artifacts"** section
3. Download **"macos-build"** artifact (ZIP file)
4. Extract ZIP file

**Contents:**
```
macos-build/
├── ClausoNet 4.0 Pro.app/
├── admin_tools/
│   └── ClausoNet Admin Key Generator.app
├── ClausoNet-4.0-Pro-macOS.dmg
├── ClausoNet-AdminTools-macOS.dmg
├── config.yaml
└── INSTALLATION_GUIDE.txt
```

### Method 2: From GitHub Releases

**If release was created:**
1. Go to **Releases** tab
2. Find latest release
3. Download **"ClausoNet-4.0-Pro-macOS.zip"**

**Release includes:**
- Main app .app bundle
- Admin tools .app
- Both DMG files
- Installation guide
- Configuration template

---

## 🔧 Phase 6: Test Local Build

### Step 6.1: Install on macOS

**From DMG:**
```bash
# Mount DMG
open ClausoNet-4.0-Pro-macOS.dmg

# Drag to Applications
cp -r "/Volumes/ClausoNet 4.0 Pro/ClausoNet 4.0 Pro.app" /Applications/

# First launch (handle security)
xattr -d com.apple.quarantine "/Applications/ClausoNet 4.0 Pro.app"
open "/Applications/ClausoNet 4.0 Pro.app"
```

**From .app directly:**
```bash
# Extract from ZIP
unzip macos-build.zip

# Remove quarantine
cd macos-build
xattr -d com.apple.quarantine "ClausoNet 4.0 Pro.app"

# Launch
open "ClausoNet 4.0 Pro.app"
```

### Step 6.2: Verify Application

**Check list:**
```
✅ App launches without errors
✅ GUI displays correctly
✅ Can load config.yaml
✅ License system works
✅ Can generate content (with valid API keys)
✅ Chrome automation works
✅ Video download works
```

---

## 🐛 Troubleshooting

### Build Fails: Missing Dependencies

**Error:**
```
ImportError: No module named 'customtkinter'
```

**Solution:**
Check `requirements.txt` is in root directory and properly formatted.

### Build Fails: Icon Conversion

**Error:**
```
⚠️ Icon conversion failed
```

**Solution:**
Ensure `assets/icon.png` exists. Workflow will create default if missing.

### Build Fails: PyInstaller Error

**Error:**
```
❌ PyInstaller build failed!
```

**Solution:**
Check workflow logs for specific error. Common issues:
- Hidden import missing
- Data file path wrong
- Module not found

**Fix in workflow:**
```yaml
hiddenimports=[
    'your_missing_module',  # Add here
]
```

### App Won't Launch: Security Block

**Error:**
```
"ClausoNet 4.0 Pro" can't be opened because it is from an unidentified developer
```

**Solution:**
```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine "ClausoNet 4.0 Pro.app"

# Or: System Preferences → Security & Privacy → Click "Open Anyway"
```

### App Won't Launch: Damaged

**Error:**
```
"ClausoNet 4.0 Pro" is damaged and can't be opened
```

**Solution:**
```bash
# Reset extended attributes
xattr -cr "ClausoNet 4.0 Pro.app"

# Fix permissions
chmod -R 755 "ClausoNet 4.0 Pro.app"
```

### Workflow Disabled

**Error:**
```
This workflow has been disabled
```

**Solution:**
- Actions tab → Enable workflows
- Or: Settings → Actions → General → Allow all actions

### API Key Security Alert

**Error:**
```
⚠️ WARNING: API keys found in code!
```

**Solution:**
- NEVER commit actual API keys
- Use `config.yaml.template` only
- Keys should be `YOUR_GEMINI_API_KEY` placeholder

---

## 📚 Advanced Topics

### Custom Build Configuration

**Edit workflow file:**
```yaml
env:
  PYTHON_VERSION: '3.11'  # Change Python version
  PROJECT_NAME: 'Your App Name'  # Change app name
```

### Add More Dependencies

**1. Update requirements.txt:**
```bash
echo "your-new-package>=1.0.0" >> requirements.txt
git add requirements.txt
git commit -m "Add new dependency"
git push
```

**2. Workflow auto-installs on next build**

### Multiple Build Configurations

**Create workflow variants:**
```bash
cp .github/workflows/macos-build-fixed.yml .github/workflows/macos-build-debug.yml

# Edit macos-build-debug.yml
# Change to debug configuration
```

### Build Notifications

**Add Slack/Discord webhook:**
```yaml
- name: Notify on success
  if: success()
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
      -H 'Content-Type: application/json' \
      -d '{"text":"✅ macOS build successful!"}'
```

---

## 📖 Quick Reference

### Common Commands

**Trigger manual build:**
```bash
# Via GitHub CLI
gh workflow run "🍎 macOS Build - ClausoNet 4.0 Pro" --ref main

# Via API
curl -X POST \
  -H "Authorization: token YOUR_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/USER/REPO/actions/workflows/macos-build-fixed.yml/dispatches \
  -d '{"ref":"main"}'
```

**Check build status:**
```bash
# Via GitHub CLI
gh run list --workflow="macos-build-fixed.yml"

# View latest run
gh run view --log
```

**Download artifacts:**
```bash
# Via GitHub CLI
gh run download RUN_ID
```

### Useful Links

- **GitHub Actions Docs**: https://docs.github.com/actions
- **PyInstaller Docs**: https://pyinstaller.org/
- **macOS Code Signing**: https://developer.apple.com/support/code-signing/
- **CustomTkinter**: https://github.com/TomSchimansky/CustomTkinter

---

## 🎉 Success Checklist

**Before build:**
- ✅ All source files committed
- ✅ requirements.txt updated
- ✅ Icon assets prepared
- ✅ Workflow file configured
- ✅ Repository pushed to GitHub

**During build:**
- ✅ Security scan passes
- ✅ Dependencies install successfully
- ✅ Main app builds
- ✅ Admin tools build
- ✅ DMG files created

**After build:**
- ✅ Artifacts downloadable
- ✅ App launches on macOS
- ✅ Core features work
- ✅ No critical errors
- ✅ Ready for distribution

---

**Build Date:** 2025-10-01  
**Version:** 1.0  
**Platform:** macOS 10.14+  
**GitHub Actions:** Enabled  

🍎 **Happy Building!**

