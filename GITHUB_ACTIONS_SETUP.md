# 🚀 GitHub Actions Setup Guide

## Tổng quan

Hướng dẫn này sẽ giúp bạn setup GitHub Actions để tự động build ClausoNet 4.0 Pro cho cả Windows và macOS **mà không cần máy Mac**.

## 🎯 Kết quả sau khi setup

- ✅ **Tự động build** khi push code
- ✅ **Windows EXE** + **macOS .app** cùng lúc
- ✅ **DMG files** cho macOS distribution
- ✅ **Automatic releases** với download links
- ✅ **FREE** - Không tốn tiền

## 📋 Setup Steps (5 phút)

### Bước 1: Tạo GitHub Repository

```bash
# Nếu chưa có repo
cd ClausoNet4.0
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ClausoNet4.0.git
git push -u origin main
```

### Bước 2: Workflow đã được tạo sẵn

File workflow đã được tạo tại:
```
ClausoNet4.0/.github/workflows/build-all-platforms.yml
```

### Bước 3: Push workflow lên GitHub

```bash
git add .github/
git commit -m "Add GitHub Actions workflow for multi-platform builds"
git push
```

### Bước 4: Xem magic happen! ✨

1. Vào **GitHub.com** → Your repository
2. Click tab **"Actions"**
3. Bạn sẽ thấy workflow đang chạy!

## 🔄 Workflow Triggers

### Tự động chạy khi:
- ✅ Push lên branch `main` hoặc `develop`
- ✅ Tạo Pull Request
- ✅ Manual trigger (nút "Run workflow")

### Không chạy khi:
- ❌ Chỉ sửa file `.md` (documentation)
- ❌ Push lên branch khác

## 📦 Build Outputs

### Sau mỗi lần build, bạn sẽ có:

#### Windows Build:
```
windows-build.zip
├── ClausoNet4.0Pro.exe           # Main application
├── admin_tools/
│   ├── ClausoNet_AdminKeyGenerator.exe
│   ├── Start_AdminKeyGenerator.bat
│   └── admin_data/
└── README.txt
```

#### macOS Build:
```
macos-build.zip
├── ClausoNet 4.0 Pro.app         # Main application
├── admin_tools/
│   ├── ClausoNet Admin Key Generator.app
│   ├── Launch_AdminKeyGenerator.sh
│   └── admin_data/
├── ClausoNet-4.0-Pro-macOS.dmg   # Distribution DMG
├── ClausoNet-AdminTools-macOS.dmg
└── INSTALLATION_GUIDE.txt
```

## 📥 Cách download builds

### Option 1: Artifacts (Mỗi build)
1. GitHub → Actions → Click vào build run
2. Scroll xuống "Artifacts" section
3. Download `windows-build` và `macos-build`

### Option 2: Releases (Chỉ main branch)
1. GitHub → Releases tab
2. Download latest release
3. Có cả Windows ZIP và macOS ZIP/DMG

## 🎛️ Workflow Configuration

### Environment Variables (có thể thay đổi):
```yaml
env:
  PYTHON_VERSION: '3.11'          # Python version to use
  PROJECT_NAME: 'ClausoNet 4.0 Pro'
```

### Build Triggers (có thể customize):
```yaml
on:
  push:
    branches: [ main, develop ]    # Thêm branches khác nếu cần
  pull_request:
    branches: [ main ]
  workflow_dispatch:               # Manual trigger
```

## 🔧 Customization

### Thêm build cho branch khác:
```yaml
on:
  push:
    branches: [ main, develop, feature/* ]
```

### Chạy theo schedule:
```yaml
on:
  schedule:
    - cron: '0 2 * * 0'  # Chạy 2AM mỗi Chủ nhật
```

### Thêm notifications:
```yaml
- name: Notify on success
  if: success()
  run: echo "Build thành công! 🎉"
```

## 📊 Build Time & Resources

### Typical Build Times:
- **Windows build**: 8-12 phút
- **macOS build**: 10-15 phút
- **Total**: ~20-25 phút

### GitHub Actions Limits (FREE):
- ✅ **2,000 phút/tháng** (đủ cho ~80-100 builds)
- ✅ **500MB storage** cho artifacts
- ✅ **Unlimited** public repositories

### Resource Usage:
- **Windows runner**: 2-core CPU, 7GB RAM, 14GB SSD
- **macOS runner**: 3-core CPU, 14GB RAM, 14GB SSD
- **Ubuntu runner**: 2-core CPU, 7GB RAM, 14GB SSD

## 🐛 Troubleshooting

### Build fails với "Module not found":
```yaml
# Thêm vào dependencies step
- name: Install additional dependencies
  run: pip install missing-module-name
```

### Build fails với "Permission denied":
```yaml
# Thêm executable permissions
- name: Make scripts executable
  run: chmod +x *.sh
```

### macOS build fails với icon:
```yaml
# Skip icon creation nếu lỗi
- name: Build without icon
  run: python3 build_main_macos.py --no-icon
```

### Out of storage space:
```yaml
# Clean up between steps
- name: Clean build artifacts
  run: rm -rf build/ dist/
```

## 💡 Pro Tips

### 1. **Branch Protection**:
```
Settings → Branches → Add rule
☑️ Require status checks to pass before merging
☑️ Require branches to be up to date before merging
```

### 2. **Secrets Management**:
```
Settings → Secrets and variables → Actions
Add secrets for API keys, certificates, etc.
```

### 3. **Caching Dependencies**:
```yaml
- name: Cache Python packages
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

### 4. **Matrix Builds** (multiple Python versions):
```yaml
strategy:
  matrix:
    python-version: ['3.9', '3.10', '3.11']
```

## 🎯 Advanced Features

### Auto-increment Version:
```yaml
- name: Bump version
  run: |
    VERSION=$(date +'%Y.%m.%d')-build.${{ github.run_number }}
    echo "VERSION=$VERSION" >> $GITHUB_ENV
```

### Code Signing (Future):
```yaml
- name: Sign macOS app
  env:
    DEVELOPER_ID: ${{ secrets.DEVELOPER_ID }}
  run: codesign --sign "$DEVELOPER_ID" "ClausoNet 4.0 Pro.app"
```

### Upload to Cloud Storage:
```yaml
- name: Upload to AWS S3
  uses: aws-actions/configure-aws-credentials@v2
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

## 📈 Monitoring & Analytics

### Build Status Badge:
Thêm vào README.md:
```markdown
![Build Status](https://github.com/YOUR_USERNAME/ClausoNet4.0/workflows/🚀%20Build%20ClausoNet%204.0%20Pro%20-%20All%20Platforms/badge.svg)
```

### Email Notifications:
```yaml
- name: Send email on failure
  if: failure()
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 587
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    to: your-email@example.com
    subject: "ClausoNet Build Failed"
```

## ✅ Checklist Setup

- [ ] Repository tạo trên GitHub
- [ ] File `.github/workflows/build-all-platforms.yml` đã push
- [ ] First build đã chạy thành công
- [ ] Downloaded và test artifacts
- [ ] Branch protection rules setup (optional)
- [ ] Notifications setup (optional)

## 🎉 Kết quả

Sau khi setup xong, workflow của bạn sẽ là:

```
1. Code trên Windows như bình thường
2. git push origin main
3. GitHub Actions tự động:
   ✅ Build Windows EXE
   ✅ Build macOS .app + DMG
   ✅ Create release với download links
4. Users download và sử dụng trên platform của họ
```

**🚀 Professional deployment pipeline chỉ với 5 phút setup!**

---

## 📞 Support

Nếu gặp vấn đề:
1. Check **Actions** tab → Build logs
2. Google error message + "GitHub Actions"
3. Check GitHub Actions [documentation](https://docs.github.com/en/actions)
4. Ask trong GitHub Issues

**Happy building! 🎯** 