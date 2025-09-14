# ClausoNet 4.0 Pro - Admin Key Generator Build Guide

## Tổng quan

Hướng dẫn này sẽ giúp bạn build GUI Admin Key Generator thành file EXE và deploy cho máy admin khác.

## Yêu cầu hệ thống

### Máy build (máy của bạn):

#### Windows:
- Windows 10/11
- Python 3.8+ đã cài đặt
- Internet connection để download packages

#### macOS:
- macOS 10.14+ (Mojave hoặc mới hơn)
- Python 3.8+ đã cài đặt
- Xcode Command Line Tools (khuyên dùng)
- Internet connection để download packages

### Máy admin (máy đích):

#### Windows:
- Windows 10/11
- Không cần Python (EXE đã bao gồm tất cả)

#### macOS:
- macOS 10.14+ (Mojave hoặc mới hơn)
- Không cần Python (.app bundle đã bao gồm tất cả)

## Các bước thực hiện

### Bước 1: Chuẩn bị môi trường

#### Windows

##### Cách 1: Tự động (Khuyên dùng)
```cmd
# Chạy trong thư mục admin_tools
setup_admin_env.bat
```

##### Cách 2: Thủ công
```cmd
# Cài đặt packages cần thiết
pip install customtkinter>=5.2.0
pip install pyinstaller>=5.13.0
pip install pillow>=10.0.0
```

#### macOS

##### Cách 1: Tự động (Khuyên dùng)
```bash
# Chạy trong thư mục admin_tools
chmod +x setup_admin_env_macos.sh
./setup_admin_env_macos.sh
```

##### Cách 2: Thủ công
```bash
# Cài đặt packages cần thiết
pip3 install customtkinter>=5.2.0
pip3 install pyinstaller>=5.13.0
pip3 install pillow>=10.0.0

# Cài đặt Xcode Command Line Tools (nếu chưa có)
xcode-select --install
```

### Bước 2: Build Executable

#### Windows - Build EXE

##### Cách 1: Tự động (Khuyên dùng)
```cmd
# Chạy trong thư mục admin_tools
build_and_deploy.bat
```

##### Cách 2: Thủ công
```cmd
# Build bằng Python script
python build_admin_key_exe.py

# Hoặc build nhanh (bỏ qua kiểm tra)
python build_admin_key_exe.py --quick
```

#### macOS - Build .app Bundle

##### Cách 1: Tự động (Khuyên dùng)
```bash
# Chạy trong thư mục admin_tools
chmod +x build_and_deploy_macos.sh
./build_and_deploy_macos.sh
```

##### Cách 2: Thủ công
```bash
# Build bằng Python script
python3 build_admin_key_macos.py

# Hoặc build nhanh (bỏ qua kiểm tra)
python3 build_admin_key_macos.py --quick
```

### Bước 3: Kiểm tra kết quả

Sau khi build thành công, bạn sẽ có:

```
admin_tools/
├── admin_key_package/               # Package hoàn chỉnh
│   ├── ClausoNet_AdminKeyGenerator.exe  # File EXE chính
│   ├── Start_AdminKeyGenerator.bat      # Script khởi chạy
│   ├── README_ADMIN.txt                 # Hướng dẫn sử dụng
│   └── admin_data/                      # Thư mục database
│       └── license_database.json       # Database rỗng
├── ClausoNet_AdminKeyGenerator_YYYYMMDD_HHMMSS.zip  # File deploy
└── dist/                            # Thư mục build PyInstaller
    └── ClausoNet_AdminKeyGenerator.exe
```

### Bước 4: Test cục bộ

```cmd
# Test EXE trên máy build
cd admin_key_package
ClausoNet_AdminKeyGenerator.exe

# Hoặc dùng batch file
Start_AdminKeyGenerator.bat
```

### Bước 5: Deploy cho máy admin

1. **Copy file ZIP**:
   - Tìm file `ClausoNet_AdminKeyGenerator_YYYYMMDD_HHMMSS.zip`
   - Copy sang máy admin (USB, email, mạng...)

2. **Giải nén trên máy admin**:
   ```cmd
   # Giải nén tại thư mục bất kỳ
   # Ví dụ: C:\ClausoNet_Admin\
   ```

3. **Chạy trên máy admin**:
   ```cmd
   # Double-click hoặc chạy
   Start_AdminKeyGenerator.bat
   
   # Hoặc chạy trực tiếp EXE
   ClausoNet_AdminKeyGenerator.exe
   ```

## Tính năng của Admin Key Generator

### Tab "Generate Keys"
- Tạo license key mới
- Chọn thời hạn: 7/30/90/365 ngày hoặc tùy chỉnh
- Nhập thông tin khách hàng và ghi chú
- Tự động tạo email template

### Tab "View Keys"
- Xem danh sách tất cả key đã tạo
- Lọc theo trạng thái (Active/All)
- Xóa key không cần thiết
- Copy key để gửi khách hàng

### Tab "Statistics"
- Thống kê tổng quan database
- Phân loại key theo loại
- Key được tạo gần đây

## Database

### Vị trí
- `admin_data/license_database.json`
- Tự động tạo khi chạy lần đầu

### Backup
- Database được lưu dưới dạng JSON
- Có thể copy/backup thủ công
- Tự động update khi tạo/xóa key

### Chuyển database sang máy khác
```cmd
# Copy toàn bộ thư mục admin_data
xcopy admin_data\ "C:\Target\admin_data\" /E /I
```

## Xử lý lỗi thường gặp

### Lỗi build

#### "PyInstaller not found"
```cmd
pip install pyinstaller>=5.13.0
```

#### "CustomTkinter not found"
```cmd
pip install customtkinter>=5.2.0
```

#### "Python not found"
- Cài đặt Python từ https://python.org
- Chọn "Add Python to PATH" khi cài

### Lỗi runtime

#### "DLL load failed"
- Cài đặt Visual C++ Redistributable
- Download từ Microsoft

#### "Database permission error"
- Chạy với quyền Administrator
- Kiểm tra quyền ghi thư mục

#### "GUI không hiển thị"
- Kiểm tra Windows scaling
- Chạy compatibility mode nếu cần

## Bảo mật

### Quan trọng
- ⚠️ **KHÔNG** chia sẻ file EXE với khách hàng
- ⚠️ **CHỈ** admin được sử dụng tool này
- ⚠️ Backup database thường xuyên

### Best practices
- Đặt password cho máy admin
- Backup `admin_data` folder định kỳ
- Không lưu database trên máy public
- Log các hoạt động tạo key

## Troubleshooting

### Build failed với UPX error
```python
# Trong admin_key_gui.spec, đổi:
upx=False  # thay vì upx=True
```

### EXE quá lớn
```python
# Thêm vào excludes trong spec file:
excludes=['numpy', 'pandas', 'matplotlib', 'scipy']
```

### Slow startup
- Sử dụng `--onedir` thay vì `--onefile`
- Exclude unnecessary modules

## Liên hệ hỗ trợ

- Email: support@clausonet.com
- Documentation: ADMIN_GUIDE.md
- Version: 1.0

---

**Lưu ý**: Tài liệu này dành cho admin/developer. Không chia sẻ với end-user. 