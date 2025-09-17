#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Google Gemini API Integration
Tích hợp với Google Gemini để xử lý văn bản và phân tích nội dung
"""

import os
import sys
import json
import time
import asyncio
from typing import Dict, Any, List, Optional, Union
import logging
from datetime import datetime
import requests
from pathlib import Path
import base64
import mimetypes

class GeminiClient:
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get('api_key', '')
        self.model = config.get('model', 'gemini-2.5-flash')
        self.max_tokens = config.get('max_tokens', 8192)
        self.temperature = config.get('temperature', 0.7)
        self.top_p = config.get('top_p', 0.9)
        self.top_k = config.get('top_k', 40)
        self.rate_limit = config.get('rate_limit', 60)

        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
        self.request_window_start = time.time()

        # Base URL
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

        self.setup_logging()
        self.validate_config()

    def setup_logging(self):
        """Thiết lập logging"""
        self.logger = logging.getLogger('GeminiClient')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def validate_config(self):
        """Validate configuration"""
        if not self.api_key:
            raise ValueError("API key is required for Gemini client")

        valid_models = [
            'gemini-pro', 'gemini-pro-vision', 'gemini-1.5-pro', 'gemini-1.5-flash',
            'gemini-2.0-flash-exp', 'gemini-2.5-flash'
        ]

        if self.model not in valid_models:
            self.logger.warning(f"Model {self.model} may not be supported. Valid models: {valid_models}")

    def get_headers(self) -> Dict[str, str]:
        """Lấy headers cho request"""
        return {
            'Content-Type': 'application/json',
            'x-goog-api-key': self.api_key,  # Use Google's standard header format
            'User-Agent': 'ClausoNet-4.0-Pro/1.0'
        }

    def check_rate_limit(self):
        """Kiểm tra rate limiting"""
        current_time = time.time()

        # Reset counter if window expired
        if current_time - self.request_window_start >= 60:  # 1 minute window
            self.request_count = 0
            self.request_window_start = current_time

        # Check if we've exceeded rate limit
        if self.request_count >= self.rate_limit:
            wait_time = 60 - (current_time - self.request_window_start)
            if wait_time > 0:
                self.logger.warning(f"Rate limit exceeded. Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                self.request_count = 0
                self.request_window_start = time.time()

        # Enforce minimum time between requests
        time_since_last = current_time - self.last_request_time
        min_interval = 60 / self.rate_limit  # seconds

        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            time.sleep(wait_time)

        self.last_request_time = time.time()
        self.request_count += 1

    def encode_image(self, image_path: str) -> Dict[str, str]:
        """Encode image để gửi đến Gemini Vision"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Get MIME type
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type or not mime_type.startswith('image/'):
                raise ValueError(f"Invalid image format: {image_path}")

            # Encode to base64
            encoded_image = base64.b64encode(image_data).decode('utf-8')

            return {
                'mime_type': mime_type,
                'data': encoded_image
            }

        except Exception as e:
            self.logger.error(f"Failed to encode image {image_path}: {e}")
            raise

    def generate_content(self,
                        prompt: str,
                        images: List[str] = None,
                        system_instruction: str = None,
                        generation_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Tạo nội dung từ prompt

        Args:
            prompt: Text prompt
            images: Danh sách đường dẫn ảnh (cho vision model)
            system_instruction: Hướng dẫn hệ thống
            generation_config: Cấu hình tạo nội dung

        Returns:
            Dict chứa kết quả
        """
        try:
            # Check rate limit
            self.check_rate_limit()

            # Prepare request data
            contents = []

            # Add system instruction if provided
            if system_instruction:
                contents.append({
                    "role": "system",
                    "parts": [{"text": system_instruction}]
                })

            # Prepare user content
            user_parts = [{"text": prompt}]

            # Add images if provided (for vision models)
            if images and self.model in ['gemini-pro-vision', 'gemini-1.5-pro', 'gemini-2.0-flash-exp', 'gemini-2.5-flash']:
                for image_path in images:
                    if os.path.exists(image_path):
                        encoded_image = self.encode_image(image_path)
                        user_parts.append({
                            "inline_data": encoded_image
                        })
                    else:
                        self.logger.warning(f"Image not found: {image_path}")

            contents.append({
                "role": "user",
                "parts": user_parts
            })

            # Generation config
            config = {
                "temperature": self.temperature,
                "topK": self.top_k,
                "topP": self.top_p,
                "maxOutputTokens": self.max_tokens,
                "candidateCount": 1  # 🔧 FIX: Chỉ trả về 1 kết quả duy nhất
            }

            if generation_config:
                config.update(generation_config)

            request_data = {
                "contents": contents,
                "generationConfig": config
            }

            # Build endpoint
            endpoint = f"{self.base_url}/models/{self.model}:generateContent"

            # Make request
            headers = self.get_headers()

            self.logger.info(f"Sending content generation request to {self.model}")
            start_time = time.time()

            response = requests.post(
                endpoint,
                json=request_data,
                headers=headers,
                timeout=120
            )

            response_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()

                # Extract response text
                response_text = ""
                if 'candidates' in result and result['candidates']:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        parts = candidate['content']['parts']
                        response_text = "\n".join(part.get('text', '') for part in parts)

                return {
                    'status': 'success',
                    'response': response_text,
                    'model': self.model,
                    'prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt,
                    'response_time': response_time,
                    'usage': result.get('usageMetadata', {}),
                    'candidates': len(result.get('candidates', [])),
                    'finish_reason': result.get('candidates', [{}])[0].get('finishReason'),
                    'created_at': datetime.now().isoformat()
                }

            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {'message': response.text}

                return {
                    'status': 'error',
                    'error_code': response.status_code,
                    'error_message': error_data.get('error', {}).get('message', response.text),
                    'error_details': error_data,
                    'response_time': response_time,
                    'prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt
                }

        except requests.exceptions.Timeout:
            return {
                'status': 'error',
                'error_message': 'Request timeout',
                'prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt
            }
        except Exception as e:
            self.logger.error(f"Content generation error: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt
            }

    def analyze_image(self, image_path: str, prompt: str = "Describe this image in detail") -> Dict[str, Any]:
        """Phân tích ảnh với Gemini Vision"""
        if self.model not in ['gemini-pro-vision', 'gemini-1.5-pro', 'gemini-2.0-flash-exp', 'gemini-2.5-flash']:
            return {
                'status': 'error',
                'error_message': f'Image analysis requires vision model, current model: {self.model}'
            }

        return self.generate_content(prompt=prompt, images=[image_path])

    def enhance_video_script(self, script: str, style: str = "professional") -> Dict[str, Any]:
        """Cải thiện script video"""
        enhancement_prompts = {
            "professional": "Enhance this video script to be more professional and engaging. Improve the narrative flow, add compelling transitions, and ensure the content is clear and impactful:",
            "creative": "Transform this video script into a more creative and artistic narrative. Add metaphors, vivid descriptions, and emotional depth:",
            "educational": "Rewrite this video script for educational purposes. Make it more structured, add clear explanations, and ensure it's easy to follow:",
            "commercial": "Optimize this video script for commercial/marketing purposes. Make it more persuasive, highlight benefits, and include call-to-action elements:"
        }

        prompt = enhancement_prompts.get(style, enhancement_prompts["professional"])
        prompt += f"\n\nOriginal script:\n{script}"

        return self.generate_content(prompt=prompt)

    def generate_video_concepts(self, topic: str, count: int = 5, style: str = "mixed") -> Dict[str, Any]:
        """Tạo concept cho video"""
        prompt = f"""Generate {count} creative video concepts for the topic: "{topic}"

For each concept, provide:
1. Title (catchy and engaging)
2. Brief description (2-3 sentences)
3. Visual style recommendation
4. Target audience
5. Estimated duration
6. Key scenes/shots

Style preference: {style}

Make each concept unique and engaging. Focus on visual storytelling and audience engagement."""

        return self.generate_content(prompt=prompt)

    def analyze_script_structure(self, script: str) -> Dict[str, Any]:
        """Phân tích cấu trúc script"""
        prompt = f"""Analyze this video script and provide detailed feedback:

1. Structure Analysis:
   - Opening effectiveness
   - Flow and transitions
   - Pacing
   - Conclusion strength

2. Content Quality:
   - Clarity of message
   - Engagement level
   - Target audience fit

3. Visual Opportunities:
   - Key scenes that need visuals
   - Suggested shot types
   - Visual storytelling elements

4. Improvements:
   - Specific suggestions for enhancement
   - Areas that need work
   - Additional elements to consider

Script to analyze:
{script}"""

        return self.generate_content(prompt=prompt)

    def generate_scene_descriptions(self, script: str) -> Dict[str, Any]:
        """Tạo mô tả chi tiết cho từng scene"""
        prompt = f"""Break down this video script into detailed scene descriptions suitable for video generation AI:

For each scene, provide:
1. Scene number and title
2. Detailed visual description (what the camera sees)
3. Setting and environment
4. Lighting suggestions
5. Camera angles and movements
6. Duration estimate
7. Any special effects needed

Make descriptions specific and detailed enough for AI video generation.

Script:
{script}"""

        return self.generate_content(prompt=prompt)

    def create_storyboard_text(self, script: str) -> Dict[str, Any]:
        """Tạo storyboard dưới dạng text"""
        prompt = f"""Create a detailed storyboard in text format for this video script:

Format each shot as:
SHOT X: [Type of shot]
- Visual: [Detailed description of what's shown]
- Action: [What happens in the shot]
- Duration: [Estimated seconds]
- Audio: [Dialog/music/sound effects]
- Transition: [How it connects to next shot]

Make it comprehensive and production-ready.

Script:
{script}"""

        return self.generate_content(prompt=prompt)

    def optimize_for_platform(self, script: str, platform: str) -> Dict[str, Any]:
        """Tối ưu script cho platform cụ thể"""
        platform_guidelines = {
            "youtube": "YouTube format (engaging hook in first 15 seconds, clear structure, strong call-to-action)",
            "tiktok": "TikTok format (vertical video, quick pace, trend-aware, under 60 seconds)",
            "instagram": "Instagram format (square or vertical, visually appealing, story-driven)",
            "facebook": "Facebook format (engaging thumbnail, subtitle-friendly, community-focused)",
            "linkedin": "LinkedIn format (professional tone, value-driven, business-oriented)"
        }

        guidelines = platform_guidelines.get(platform.lower(), "general social media format")

        prompt = f"""Optimize this video script for {platform}.

Platform requirements: {guidelines}

Ensure the script follows platform best practices:
- Optimal length and pacing
- Platform-specific engagement tactics
- Appropriate tone and style
- Technical considerations (aspect ratio, captions, etc.)

Original script:
{script}"""

        return self.generate_content(prompt=prompt)

    def generate_prompts_for_video_ai(self, script: str, video_duration: int = 48) -> Dict[str, Any]:
        """Dynamic template tạo prompts dựa trên user content với visual consistency hoàn hảo"""
        
        # 🎯 CALCULATE NUMBER OF PROMPTS BASED ON VIDEO DURATION
        prompts_needed = max(1, min(10, video_duration // 8))  # Min 1, Max 10 prompts
        actual_duration = prompts_needed * 8
        
        self.logger.info(f"🎬 Video Duration: {video_duration}s → {prompts_needed} prompts → {actual_duration}s actual")
        
        # 🎯 DYNAMIC PROMPT FORMAT BASED ON DURATION
        prompt_format = "\n".join([f"PROMPT {i+1}: [content]" for i in range(prompts_needed)])
        
        prompt = f"""PHASE 1: ANALYZE USER SCRIPT AND EXTRACT CORE ELEMENTS
First, carefully read this script: "{script}"

PHASE 2: CREATE CONSISTENT PROMPTS
Convert script to video prompts. Use EXACTLY this format:

{prompt_format}

CRITICAL CONSISTENCY RULES:
1. EXTRACT main characters from the user script - describe them with 2-3 specific visual details
2. EXTRACT main environment from the user script - describe with 2-3 specific visual details  
3. USE THE SAME character descriptions in EVERY prompt (copy exactly)
4. USE THE SAME environment description in EVERY prompt (copy exactly)
5. Each prompt = 8 seconds, one action only
6. MAXIMUM {prompts_needed} PROMPTS ONLY ({actual_duration} seconds total video)
7. PROMPT 2+ must start with "Same characters and setting:"

CONSISTENCY TEMPLATE:
- First, identify WHO are the main characters in the script
- Then, identify WHERE the story takes place
- Use these SAME elements in every single prompt

EXAMPLE STRUCTURE (adapt to YOUR script content):
PROMPT 1: [Main character with specific visual details] [action] in [specific environment with visual details]. [Camera angle].

PROMPT 2: Same characters and setting: [EXACT same character descriptions] [different action] in [EXACT same environment]. [Camera angle].

PROMPT 3: Same characters and setting: [EXACT same character descriptions] [different action] in [EXACT same environment]. [Camera angle].

IMPORTANT NOTES:
- DO NOT use cats/dogs/park unless they are in the user script
- EXTRACT characters and setting FROM THE USER SCRIPT ONLY
- Keep character descriptions identical across all prompts
- Keep environment description identical across all prompts
- Focus on the story progression while maintaining visual consistency

USER SCRIPT TO CONVERT: {script}

Generate EXACTLY {prompts_needed} prompts following the user's story content:"""

        return self.generate_content(prompt=prompt)

    def count_tokens(self, text: str) -> int:
        """Ước tính số token (approximate)"""
        # Rough estimation: 1 token ≈ 4 characters for English
        return len(text) // 4

    def get_supported_models(self) -> List[str]:
        """Lấy danh sách model được hỗ trợ"""
        return [
            'gemini-pro',
            'gemini-pro-vision',
            'gemini-1.5-pro',
            'gemini-1.5-flash',
            'gemini-2.0-flash-exp',
            'gemini-2.5-flash'
        ]

    def get_usage_statistics(self) -> Dict[str, Any]:
        """Lấy thống kê sử dụng"""
        return {
            'requests_in_current_window': self.request_count,
            'rate_limit': self.rate_limit,
            'window_start': datetime.fromtimestamp(self.request_window_start).isoformat(),
            'last_request': datetime.fromtimestamp(self.last_request_time).isoformat() if self.last_request_time else None,
            'current_model': self.model
        }

def create_client(config: Dict[str, Any]) -> GeminiClient:
    """Factory function để tạo Gemini client"""
    return GeminiClient(config)

if __name__ == "__main__":
    print("GeminiHandler module loaded successfully")
