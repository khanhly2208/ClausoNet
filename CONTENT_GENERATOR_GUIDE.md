# ClausoNet 4.0 Pro - Content Generator Guide

## Tổng quan

Content Generator là module chính để tạo và cải thiện nội dung video sử dụng ChatGPT và Gemini AI. Module này tích hợp vào GUI và có thể được sử dụng độc lập.

## Cấu hình API Keys

### 1. Cập nhật file config.yaml

```yaml
apis:
  # Google Gemini - Content Generation
  gemini:
    enabled: true
    api_key: "YOUR_GEMINI_API_KEY_HERE"  # Nhập API key của Gemini
    model: "gemini-pro"
    max_tokens: 8192
    temperature: 0.7
    rate_limit: 60
  
  # OpenAI ChatGPT - Content Enhancement
  openai:
    enabled: true
    api_key: "YOUR_OPENAI_API_KEY_HERE"  # Nhập API key của OpenAI
    model: "gpt-4-turbo"
    max_tokens: 4096
    temperature: 0.7
    rate_limit: 500
```

### 2. Lấy API Keys

#### Gemini API Key:
1. Truy cập: https://makersuite.google.com/app/apikey
2. Tạo API key mới
3. Copy và paste vào config.yaml

#### OpenAI API Key:
1. Truy cập: https://platform.openai.com/api-keys
2. Tạo API key mới
3. Copy và paste vào config.yaml

## Các chức năng chính

### 1. Cải thiện Script (enhance_script)

```python
from core.content_generator import ContentGenerator

# Khởi tạo
generator = ContentGenerator(config)

# Cải thiện script
result = generator.enhance_script(
    script="Your video script here...",
    provider="gemini",  # hoặc "chatgpt"
    style="professional"  # professional, creative, educational, commercial
)

if result['status'] == 'success':
    enhanced_script = result['enhanced_script']
    print(enhanced_script)
```

### 2. Tạo Video Prompts (generate_video_prompts)

```python
# Tạo prompts cho AI video generation
result = generator.generate_video_prompts(
    script="Your script here...",
    provider="gemini",
    style="cinematic"  # cinematic, realistic, artistic
)

if result['status'] == 'success':
    video_prompts = result['video_prompts']
    print(video_prompts)
```

### 3. Phân tích Script (analyze_script)

```python
# Phân tích cấu trúc script
result = generator.analyze_script(
    script="Your script here...",
    provider="chatgpt",
    analysis_type="structure"  # structure, effectiveness, scenes
)

if result['status'] == 'success':
    analysis = result['analysis']
    print(analysis)
```

### 4. Tối ưu cho Platform (optimize_for_platform)

```python
# Tối ưu script cho platform cụ thể
result = generator.optimize_for_platform(
    script="Your script here...",
    platform="youtube",  # youtube, tiktok, instagram, linkedin, facebook
    provider="gemini",
    duration=120  # seconds (optional)
)

if result['status'] == 'success':
    optimized_script = result['optimized_script']
    print(optimized_script)
```

### 5. Tạo Concepts (generate_concepts)

```python
# Tạo concepts cho video từ topic
result = generator.generate_concepts(
    topic="Artificial Intelligence",
    provider="chatgpt",
    count=5,
    style="mixed"
)

if result['status'] == 'success':
    concepts = result['concepts']
    print(concepts)
```

### 6. Tạo Content Tùy chỉnh (custom_generate)

```python
# Tạo content với prompt tùy chỉnh
result = generator.custom_generate(
    prompt="Create a 60-second video script about sustainable technology",
    provider="gemini",
    system_message="You are a professional video scriptwriter"  # Chỉ cho ChatGPT
)

if result['status'] == 'success':
    content = result['content']
    print(content)
```

## Sử dụng trong GUI

### 1. Workflow Tab

1. **Nhập Script**: Paste script vào ô "Your Form (txt)"
2. **Chọn Provider**: Sử dụng dropdown "ChatGPT|Gemini API"
3. **Process Script**: Click vào script input để tự động cải thiện (tính năng sẽ được thêm)

### 2. Settings Tab

1. **Cập nhật API Keys**: Nhập API keys vào các ô tương ứng
2. **Chọn Model**: Chọn model phù hợp
3. **Save Settings**: Lưu cấu hình

## Xử lý Lỗi

### Lỗi thường gặp:

1. **"Provider không có sẵn"**
   - Kiểm tra API key trong config.yaml
   - Đảm bảo API key hợp lệ

2. **"Rate limit exceeded"**
   - Đợi một chút rồi thử lại
   - Giảm tần suất requests

3. **"Invalid API key"**
   - Kiểm tra API key
   - Tạo API key mới nếu cần

4. **"Content generator chưa được khởi tạo"**
   - Restart ứng dụng
   - Kiểm tra file config.yaml

## Tích hợp vào Workflow

### Example Usage:

```python
# 1. Load config
config = load_config()

# 2. Initialize generator
generator = ContentGenerator(config['apis'])

# 3. Process user input
user_script = "..."
enhanced_script = generator.enhance_script(user_script, provider="gemini")

# 4. Generate video prompts
video_prompts = generator.generate_video_prompts(enhanced_script, provider="chatgpt")

# 5. Use prompts for video generation
# (Integrate with Google Veo 3 or other video AI)
```

## Performance Tips

1. **Provider Selection**:
   - Gemini: Tốt cho content generation, nhanh hơn
   - ChatGPT: Tốt cho analysis và enhancement, chất lượng cao hơn

2. **Rate Limiting**:
   - Gemini: 60 requests/minute
   - OpenAI: 500 requests/minute (tùy plan)

3. **Token Management**:
   - Chia script dài thành nhiều phần nhỏ
   - Sử dụng summary cho script quá dài

4. **Error Handling**:
   - Luôn check result['status']
   - Implement retry logic cho network errors

## Debug và Monitoring

### Kiểm tra Status:

```python
# Xem providers có sẵn
available = generator.get_available_providers()
print(f"Available providers: {available}")

# Xem thống kê sử dụng
stats = generator.get_usage_stats()
print(json.dumps(stats, indent=2))

# Kiểm tra provider cụ thể
is_gemini_ready = generator.is_provider_available('gemini')
is_chatgpt_ready = generator.is_provider_available('chatgpt')
```

### Logs:

- Check console output cho initialization messages
- Error messages sẽ hiển thị trong GUI
- Log files trong thư mục ./logs/

## Sample Script cho Testing

```text
Welcome to the future of artificial intelligence. In this video, we'll explore how AI 
is revolutionizing content creation, from automated video generation to intelligent 
script writing. Join us as we dive into the cutting-edge technologies that are 
reshaping the digital landscape and empowering creators worldwide.

We'll cover three main topics:
1. AI-powered video generation tools
2. Intelligent content optimization
3. The future of creative automation

Whether you're a content creator, marketer, or tech enthusiast, this video will 
provide valuable insights into the AI revolution that's happening right now.
```

## Troubleshooting

### Common Issues:

1. **Module not found errors**:
   ```bash
   cd ClausoNet4.0
   python -m pip install -r requirements.txt
   ```

2. **YAML parsing errors**:
   - Check config.yaml syntax
   - Use proper indentation (spaces, not tabs)

3. **API connection errors**:
   - Check internet connection
   - Verify API endpoints are accessible
   - Check API key permissions

4. **GUI integration issues**:
   - Restart application
   - Check Python path setup
   - Verify all imports are working

## Support

Nếu gặp vấn đề:

1. Check logs trong ./logs/
2. Verify API keys và config
3. Test với script đơn giản trước
4. Check network connectivity
5. Update dependencies nếu cần

---

**Note**: Đảm bảo giữ API keys bảo mật và không commit vào git repository! 