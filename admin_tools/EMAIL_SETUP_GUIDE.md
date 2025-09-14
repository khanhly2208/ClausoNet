"""
📧 HƯỚNG DẪN SETUP EMAIL THỰC TẾ CHO CLAUSONET 4.0 PRO
================================================================

🎯 MỤC TIÊU:
- Setup Gmail/Outlook để gửi license keys tự động
- Kích hoạt email workflow hoàn chỉnh cho ClausoNet 4.0 Pro
- Test gửi email thực tế cho trial và lifetime keys

🔧 BƯỚC 1: SETUP GMAIL (KHUYẾN NGHỊ)
================================================================

1.1. Tạo Gmail Business hoặc dùng Gmail cá nhân:
   • Email: clausonet.pro@gmail.com (hoặc email bạn chọn)
   • Mật khẩu: [password mạnh]

1.2. Bật 2-Factor Authentication:
   • Vào Google Account → Security
   • Bật "2-Step Verification"
   • Xác nhận bằng phone

1.3. Tạo App Password:
   • Vào Google Account → Security
   • Chọn "App passwords"
   • Chọn "Mail" và device "Other"
   • Tên: "ClausoNet License System"
   • Copy password 16 ký tự (ví dụ: abcd efgh ijkl mnop)

1.4. Cấu hình trong ClausoNet:
   ```python
   # Mở admin_license_gui.py hoặc chạy:
   from license_key_generator import LicenseKeyGenerator

   gen = LicenseKeyGenerator()
   gen.admin_email = "clausonet.pro@gmail.com"
   gen.admin_password = "abcd efgh ijkl mnop"  # App password
   gen.smtp_server = "smtp.gmail.com"
   gen.smtp_port = 587
   ```

🔧 BƯỚC 2: SETUP OUTLOOK (TÙY CHỌN)
================================================================

2.1. Tạo Outlook/Hotmail account:
   • Email: clausonet.pro@outlook.com
   • Mật khẩu: [password mạnh]

2.2. Bật App Password (tương tự Gmail):
   • Vào Account Security
   • Enable 2FA
   • Generate App Password

2.3. Cấu hình:
   ```python
   gen.admin_email = "clausonet.pro@outlook.com"
   gen.admin_password = "[app-password]"
   gen.smtp_server = "smtp-mail.outlook.com"
   gen.smtp_port = 587
   ```

🔧 BƯỚC 3: TEST GỬI EMAIL THỰC TẾ
================================================================

3.1. Chạy Admin GUI:
   ```
   cd c:\project\videoai\ClausoNet4.0\admin_tools
   python admin_license_gui.py
   ```

3.2. Cấu hình email trong tab "Settings":
   • Nhập admin email
   • Nhập app password
   • Save configuration

3.3. Test gửi email:
   • Tab "License Generator"
   • Tạo trial key hoặc lifetime key
   • Nhập email người nhận
   • Click "Generate & Send Email"

🔧 BƯỚC 4: KIỂM TRA KẾT QUẢ
================================================================

4.1. Kiểm tra email đã gửi:
   • Check Sent folder của admin email
   • Verify email delivered

4.2. Kiểm tra email nhận:
   • Check inbox của customer
   • Email subject: "ClausoNet 4.0 Pro - Your [Trial/Lifetime] License Key"
   • Email chứa license key và hướng dẫn

4.3. Test activation:
   • Mở ClausoNet 4.0 Pro
   • Settings → License
   • Nhập key từ email
   • Verify activation successful

📧 EMAIL TEMPLATE SẼ GỬI:
================================================================

Subject: ClausoNet 4.0 Pro - Your Trial License Key

Dear Customer,

Thank you for choosing ClausoNet 4.0 Pro!

🔑 YOUR LICENSE KEY: CNPRO-XXXX-XXXX-XXXX-XXXX

🚀 QUICK ACTIVATION GUIDE:
1. Download ClausoNet 4.0 Pro from: https://clausonet.com/download
2. Launch the application
3. Navigate to Settings → License
4. Enter your license key: CNPRO-XXXX-XXXX-XXXX-XXXX
5. Click "Activate License"

✨ FEATURES INCLUDED:
• Advanced AI Video Generation
• Multi-Language Support
• Premium Templates
• HD Export Quality
• Priority Support

Best regards,
The ClausoNet Team

🔧 TROUBLESHOOTING
================================================================

Lỗi 1: "Authentication failed"
   → Kiểm tra app password đúng chưa
   → Đảm bảo 2FA đã bật
   → Thử tạo app password mới

Lỗi 2: "Connection timeout"
   → Kiểm tra internet connection
   → Thử đổi SMTP port (465 cho SSL)
   → Check firewall settings

Lỗi 3: "Email rejected"
   → Kiểm tra email format đúng
   → Verify recipient email exists
   → Check spam folder

🎯 HOÀN THÀNH SETUP
================================================================

Sau khi setup xong:
✅ Email system hoạt động 100%
✅ License keys tự động gửi về email
✅ Professional branding cho business
✅ Customer tracking đầy đủ
✅ Revenue management tự động

📞 SUPPORT:
Nếu cần hỗ trợ setup, email: [your-support-email]
"""
