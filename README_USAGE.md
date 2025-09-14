# ClausoNet 4.0 Pro - Hướng Dẫn Sử Dụng

## 🔐 Hệ Thống License Gắn Máy

ClausoNet 4.0 Pro sử dụng hệ thống license gắn máy (machine-bound license) để bảo vệ phần mềm. Mỗi license chỉ hoạt động trên 1 máy tính duy nhất và không thể chia sẻ.

### 📋 Quy Trình Kích Hoạt License

#### Bước 1: Chạy Ứng Dụng Lần Đầu
```bash
# Cách 1: Dùng batch file (khuyến nghị)
run_app.bat

# Cách 2: Chạy trực tiếp
python gui/main_window.py
```

#### Bước 2: Lấy Hardware ID
- Ứng dụng sẽ hiển thị dialog license
- Copy **Hardware ID** hiển thị trong dialog
- Gửi Hardware ID này cho vendor để nhận license key

#### Bước 3: Nhận và Nhập License Key
- Vendor sẽ tạo license key dựa trên Hardware ID của bạn
- Nhập license key vào dialog (format: `CNPRO-XXXX-XXXX-XXXX-XXXX`)
- Click "Activate License"

#### Bước 4: Hoàn Thành
- License sẽ được lưu vào file `license/clausonet.lic`
- Ứng dụng khởi động và sẵn sàng sử dụng

### 🛠️ Tools Quản Lý License

#### 1. License Admin GUI (Dành cho Vendor/Admin)
```bash
# Chạy tool admin
run_license_admin.bat

# Hoặc
python utils/license_admin_gui.py
```

**Chức năng:**
- 🔑 **Generate License**: Tạo license key cho customer
- 🖥️ **Hardware Scanner**: Quét thông tin hardware của máy
- 📋 **License Database**: Quản lý database license
- ⚙️ **Bulk Operations**: Tạo hàng loạt license

#### 2. Command Line Tools
```bash
# Xem hardware ID hiện tại
python utils/license_wizard.py --generate-hardware-id

# Kích hoạt license với key
python utils/license_wizard.py --activate CNPRO-XXXX-XXXX-XXXX-XXXX

# Kiểm tra trạng thái license
python utils/license_wizard.py --check

# Làm mới hardware binding
python utils/license_wizard.py --refresh-hardware
```

### 🔒 Bảo Mật License

#### Hardware Fingerprinting
License được gắn với các thông tin hardware:
- 🖥️ CPU ID
- 🔧 Motherboard Serial Number
- 🌐 MAC Address
- 🪟 Windows Product ID
- 💾 BIOS Information
- 🖥️ Platform Info

#### Mã Hóa
- License file được mã hóa AES-256
- Key được derive từ Hardware ID + Salt
- Không thể copy license giữa các máy khác nhau

### 📁 Cấu Trúc File

```
ClausoNet4.0/
├── license/                 # Thư mục license
│   └── clausonet.lic       # File license đã kích hoạt
├── admin_data/             # Data cho admin tool
│   └── license_database.json
├── utils/
│   ├── license_admin_gui.py # Tool admin
│   ├── license_wizard.py   # Command line tool
│   └── admin_requirements.txt
├── run_app.bat             # Chạy ứng dụng chính
├── run_license_admin.bat   # Chạy admin tool
└── README_USAGE.md         # File này
```

### ❗ Lưu Ý Quan Trọng

1. **Backup License**: Sao lưu file `license/clausonet.lic` để khôi phục khi cần
2. **Hardware Change**: Nếu thay đổi hardware lớn, cần license mới
3. **One Machine Only**: Mỗi license chỉ hoạt động trên 1 máy
4. **Expiry Date**: Kiểm tra ngày hết hạn license
5. **Network**: Cần internet để kích hoạt license lần đầu

### 🆘 Troubleshooting

#### "License file not found"
- Chạy lại ứng dụng, sẽ có dialog kích hoạt
- Hoặc dùng command: `python utils/license_wizard.py --activate YOUR_KEY`

#### "Hardware mismatch"
- License đã được kích hoạt trên máy khác
- Cần license mới cho máy hiện tại

#### "License has expired"
- License đã hết hạn
- Liên hệ vendor để gia hạn

#### Import Error
```bash
# Cài đặt dependencies
pip install -r requirements.txt
pip install -r utils/admin_requirements.txt
```

### 📞 Hỗ Trợ

Nếu gặp vấn đề, vui lòng cung cấp:
1. Hardware ID của máy
2. License key đang sử dụng
3. Thông báo lỗi chi tiết
4. Thông tin hệ điều hành

---
**ClausoNet 4.0 Pro** - AI Video Generation Tool với License Bảo Mật 