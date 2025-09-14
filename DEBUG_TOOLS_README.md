# 🔧 VEO WORKFLOW DEBUG TOOLS

Bộ công cụ debug để kiểm tra và phân tích automation workflow của Google Veo.

## 📁 Files

### 1. `debug_tools.bat` - Menu chính
- Chạy file này để truy cập tất cả debug tools
- Giao diện menu đơn giản

### 2. `quick_veo_test.py` - Test nhanh (60s)
**Mục đích:** Test nhanh các selector chính
**Thời gian:** ~60 giây
**Tính năng:**
- Test tất cả selector quan trọng
- Hiển thị thống kê elements
- Browser mở 60s để inspect manual
- Không cần interaction

**Chạy:**
```bash
python quick_veo_test.py
```

### 3. `step_by_step_debug.py` - Debug từng bước
**Mục đích:** Debug chi tiết từng bước workflow
**Thời gian:** 10-30 phút (tùy user)
**Tính năng:**
- Debug từng bước một cách có kiểm soát
- Highlight elements trên page
- Take screenshots cho mỗi bước
- User confirmation cho mỗi action
- Auto mode hoặc interactive mode

**Workflow steps:**
1. Navigation to Google Veo
2. Find New Project Button
3. Find Settings Button  
4. Find Model Dropdown
5. Find Prompt Input & Test typing

**Chạy:**
```bash
python step_by_step_debug.py
```

### 4. `debug_veo_workflow.py` - Debug toàn diện
**Mục đích:** Debug workflow hoàn chỉnh với interactive mode
**Thời gian:** 20-60 phút
**Tính năng:**
- Full automated workflow test
- Interactive debug mode với commands
- Screenshot tự động khi có lỗi
- Element scanning và analysis
- Video detection testing

**Interactive Commands:**
- `scan` - Scan page elements
- `click N` - Click button số N
- `type` - Test prompt input
- `videos` - Scan for videos
- `shot` - Take screenshot
- `url` - Show current URL
- `quit` - Exit

**Chạy:**
```bash
python debug_veo_workflow.py
```

## 🚀 Cách sử dụng

### Option 1: Sử dụng Menu (Khuyến nghị)
```bash
debug_tools.bat
```
Chọn tool từ menu.

### Option 2: Chạy trực tiếp
```bash
# Test nhanh
python quick_veo_test.py

# Debug từng bước
python step_by_step_debug.py

# Debug toàn diện
python debug_veo_workflow.py
```

## 📸 Screenshots

Tất cả tools sẽ tự động lưu screenshots vào folder `debug_screenshots/`:
- `quick_veo_test.py`: Ít screenshots, focus vào overview
- `step_by_step_debug.py`: Screenshots cho mỗi bước
- `debug_veo_workflow.py`: Screenshots khi có error và manual shots

## 🎯 Khi nào dùng tool nào?

### Quick Test - Khi cần:
- ✅ Kiểm tra nhanh selector có hoạt động không
- ✅ Xem overview elements trên page
- ✅ Test quick mà không cần interaction

### Step-by-Step - Khi cần:
- ✅ Debug chi tiết từng bước workflow
- ✅ Xem chính xác element nào được found
- ✅ Test click behavior của từng element
- ✅ Kiểm soát hoàn toàn quá trình debug

### Full Workflow - Khi cần:
- ✅ Test toàn bộ workflow automation
- ✅ Interactive debugging với nhiều commands
- ✅ Phân tích sâu về page structure
- ✅ Test video detection

## 🔧 Requirements

```bash
pip install selenium webdriver-manager
```

## 📋 Debug Output

### Console Output
- ✅ Success messages (green)
- ❌ Error messages (red)  
- 🔍 Debug info (blue)
- ⚠️ Warnings (yellow)

### Screenshot Files
- Naming: `step_XX_description_timestamp.png`
- Location: `debug_screenshots/`
- Auto-generated cho mỗi bước quan trọng

## 🎨 Element Highlighting

**Step-by-Step Debugger:**
- 🔴 Red border + Yellow background: New Project buttons
- 🔵 Blue border + Light blue background: Other elements

## 💡 Tips

1. **Luôn chạy Step-by-Step trước** khi có vấn đề với automation
2. **Check screenshots** để hiểu chính xác element nào được found
3. **Dùng Interactive mode** của Full Workflow để test manual commands
4. **Browser profile** sẽ được tạo tự động trong `chrome_profiles/` hoặc user data dir

## 🐛 Troubleshooting

### Chrome không mở được:
- Cài đặt `webdriver-manager`: `pip install webdriver-manager`
- Kiểm tra Chrome có được cài đặt không
- Chạy với admin rights nếu cần

### Elements không tìm thấy:
- Chạy `step_by_step_debug.py` để xem element highlighting
- Check screenshots để hiểu page structure
- Google Veo có thể đã thay đổi interface

### Screenshots không lưu:
- Kiểm tra quyền write vào folder
- Tạo folder `debug_screenshots` manually nếu cần

## 📞 Debug Commands Summary

### Quick Test:
- Auto test tất cả selectors
- 60s browser inspect time

### Step-by-Step:
- Enter: Continue to next step
- 's': Take manual screenshot  
- 'q': Quit debugging

### Full Workflow Interactive:
- `scan`: Scan elements
- `click N`: Test click button N
- `type`: Test prompt typing
- `videos`: Scan videos
- `shot`: Manual screenshot
- `quit`: Exit
