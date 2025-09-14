#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - OpenAI API Integration
Tích hợp với OpenAI (ChatGPT) để xử lý văn bản và cải thiện nội dung
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

class OpenAIClient:
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get('api_key', '')
        self.organization = config.get('organization', '')
        self.model = config.get('model', 'gpt-4-turbo')
        self.max_tokens = config.get('max_tokens', 4096)
        self.temperature = config.get('temperature', 0.7)
        self.top_p = config.get('top_p', 1.0)
        self.frequency_penalty = config.get('frequency_penalty', 0.0)
        self.presence_penalty = config.get('presence_penalty', 0.0)
        self.rate_limit = config.get('rate_limit', 500)  # requests per minute

        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
        self.request_window_start = time.time()

        # Base URL
        self.base_url = "https://api.openai.com/v1"

        self.setup_logging()
        self.validate_config()

    def setup_logging(self):
        """Thiết lập logging"""
        self.logger = logging.getLogger('OpenAIClient')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def validate_config(self):
        """Validate configuration"""
        if not self.api_key:
            raise ValueError("API key is required for OpenAI client")

        valid_models = [
            'gpt-4', 'gpt-4-turbo', 'gpt-4-turbo-preview',
            'gpt-3.5-turbo', 'gpt-3.5-turbo-16k',
            'text-davinci-003', 'text-davinci-002'
        ]

        if self.model not in valid_models:
            self.logger.warning(f"Model {self.model} may not be supported. Valid models: {valid_models}")

    def get_headers(self) -> Dict[str, str]:
        """Lấy headers cho request"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'ClausoNet-4.0-Pro/1.0'
        }

        if self.organization:
            headers['OpenAI-Organization'] = self.organization

        return headers

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

        # Enforce minimum time between requests for high rate limits
        if self.rate_limit > 100:
            time_since_last = current_time - self.last_request_time
            min_interval = 60 / self.rate_limit  # seconds

            if time_since_last < min_interval:
                wait_time = min_interval - time_since_last
                time.sleep(wait_time)

        self.last_request_time = time.time()
        self.request_count += 1

    def chat_completion(self,
                       messages: List[Dict[str, str]],
                       system_message: str = None,
                       temperature: float = None,
                       max_tokens: int = None,
                       functions: List[Dict[str, Any]] = None,
                       function_call: Union[str, Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Chat completion API call

        Args:
            messages: Danh sách messages
            system_message: System message
            temperature: Temperature override
            max_tokens: Max tokens override
            functions: Function definitions
            function_call: Function call specification

        Returns:
            Dict chứa kết quả
        """
        try:
            # Check rate limit
            self.check_rate_limit()

            # Prepare messages
            chat_messages = []

            # Add system message if provided
            if system_message:
                chat_messages.append({
                    "role": "system",
                    "content": system_message
                })

            # Add user messages
            chat_messages.extend(messages)

            # Prepare request data
            request_data = {
                "model": self.model,
                "messages": chat_messages,
                "temperature": temperature if temperature is not None else self.temperature,
                "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
                "top_p": self.top_p,
                "frequency_penalty": self.frequency_penalty,
                "presence_penalty": self.presence_penalty
            }

            # Add functions if provided
            if functions:
                request_data["functions"] = functions
                if function_call:
                    request_data["function_call"] = function_call

            # Build endpoint
            endpoint = f"{self.base_url}/chat/completions"

            # Make request
            headers = self.get_headers()

            self.logger.info(f"Sending chat completion request to {self.model}")
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

                # Extract response
                choice = result['choices'][0]
                message = choice['message']

                return {
                    'status': 'success',
                    'response': message.get('content', ''),
                    'function_call': message.get('function_call'),
                    'model': self.model,
                    'response_time': response_time,
                    'usage': result.get('usage', {}),
                    'finish_reason': choice.get('finish_reason'),
                    'created_at': datetime.now().isoformat()
                }

            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {'message': response.text}

                return {
                    'status': 'error',
                    'error_code': response.status_code,
                    'error_message': error_data.get('error', {}).get('message', response.text),
                    'error_type': error_data.get('error', {}).get('type'),
                    'error_details': error_data,
                    'response_time': response_time
                }

        except requests.exceptions.Timeout:
            return {
                'status': 'error',
                'error_message': 'Request timeout'
            }
        except Exception as e:
            self.logger.error(f"Chat completion error: {e}")
            return {
                'status': 'error',
                'error_message': str(e)
            }

    def generate_text(self, prompt: str, system_message: str = None, **kwargs) -> Dict[str, Any]:
        """Generate text từ prompt đơn giản"""
        messages = [{"role": "user", "content": prompt}]
        return self.chat_completion(messages, system_message=system_message, **kwargs)

    def enhance_video_script(self, script: str, style: str = "professional") -> Dict[str, Any]:
        """Cải thiện script video"""
        style_instructions = {
            "professional": "Enhance this video script to be more professional, clear, and engaging. Improve narrative flow, add compelling transitions, and ensure the content is impactful and well-structured.",
            "creative": "Transform this video script into a more creative and artistic narrative. Add metaphors, vivid descriptions, emotional depth, and innovative storytelling techniques.",
            "educational": "Rewrite this video script for educational purposes. Make it more structured with clear explanations, logical progression, and easy-to-follow content that facilitates learning.",
            "commercial": "Optimize this video script for commercial/marketing purposes. Make it more persuasive, highlight key benefits, include strong call-to-action elements, and focus on audience engagement.",
            "documentary": "Adapt this video script for documentary style. Add factual depth, investigative elements, compelling narrative structure, and authoritative tone.",
            "entertainment": "Make this video script more entertaining and engaging. Add humor, interesting hooks, dynamic pacing, and elements that capture and maintain viewer attention."
        }

        system_message = style_instructions.get(style, style_instructions["professional"])

        messages = [
            {"role": "user", "content": f"Please enhance this video script:\n\n{script}"}
        ]

        return self.chat_completion(messages, system_message=system_message)

    def generate_video_concepts(self, topic: str, count: int = 5, target_audience: str = "general") -> Dict[str, Any]:
        """Tạo concept cho video"""
        system_message = f"""You are a creative video content strategist. Generate {count} unique and engaging video concepts for the given topic. Consider the target audience: {target_audience}.

For each concept, provide:
1. Catchy title
2. Brief description (2-3 sentences)
3. Visual style recommendation
4. Key scenes or shots
5. Estimated duration
6. Unique selling point

Make each concept distinct and compelling."""

        messages = [
            {"role": "user", "content": f"Generate video concepts for topic: {topic}"}
        ]

        return self.chat_completion(messages, system_message=system_message)

    def create_detailed_storyboard(self, script: str) -> Dict[str, Any]:
        """Tạo storyboard chi tiết"""
        system_message = """You are a professional storyboard artist and video director. Create a detailed storyboard breakdown for the given video script.

For each shot, provide:
- Shot number and type (wide, medium, close-up, etc.)
- Detailed visual description
- Camera movement (pan, tilt, zoom, static)
- Lighting and mood
- Duration estimate
- Audio elements (dialogue, music, sound effects)
- Transition to next shot

Format the output clearly and make it production-ready."""

        messages = [
            {"role": "user", "content": f"Create a detailed storyboard for this script:\n\n{script}"}
        ]

        return self.chat_completion(messages, system_message=system_message)

    def analyze_script_effectiveness(self, script: str, platform: str = "youtube") -> Dict[str, Any]:
        """Phân tích hiệu quả của script"""
        system_message = f"""You are a video marketing expert specializing in {platform} content. Analyze the given video script and provide comprehensive feedback on its effectiveness.

Evaluate:
1. Hook effectiveness (first 15 seconds)
2. Narrative structure and flow
3. Audience engagement potential
4. Platform optimization
5. Call-to-action strength
6. Pacing and timing
7. Visual storytelling opportunities
8. Areas for improvement

Provide specific, actionable recommendations."""

        messages = [
            {"role": "user", "content": f"Analyze this video script for {platform}:\n\n{script}"}
        ]

        return self.chat_completion(messages, system_message=system_message)

    def generate_video_prompts_for_ai(self, script: str, style: str = "cinematic") -> Dict[str, Any]:
        """Tạo prompts cho AI tạo video"""
        system_message = f"""You are an expert in AI video generation prompts. Convert the given video script into detailed, specific prompts suitable for AI video generation tools like Google Veo or Runway.

Requirements:
- Break script into sequential scenes/shots
- Each prompt should be detailed and specific
- Include visual style ({style}), camera angles, lighting, mood
- Keep each prompt under 200 words
- Number prompts sequentially
- Ensure continuity between scenes

Style preference: {style}"""

        messages = [
            {"role": "user", "content": f"Convert this script into AI video generation prompts:\n\n{script}"}
        ]

        return self.chat_completion(messages, system_message=system_message)

    def optimize_for_platform(self, script: str, platform: str, duration: int = None) -> Dict[str, Any]:
        """Tối ưu script cho platform cụ thể"""
        platform_specs = {
            "youtube": {
                "format": "Landscape (16:9)",
                "optimal_length": "5-15 minutes for most content",
                "hook": "Strong hook in first 15 seconds",
                "features": "Chapters, end screens, cards, thumbnails",
                "audience": "Diverse, search-driven"
            },
            "tiktok": {
                "format": "Vertical (9:16)",
                "optimal_length": "15-60 seconds",
                "hook": "Immediate visual impact, first 3 seconds crucial",
                "features": "Trends, sounds, effects, hashtags",
                "audience": "Young, mobile-first, short attention span"
            },
            "instagram": {
                "format": "Square (1:1) or Vertical (9:16) for Reels",
                "optimal_length": "15-30 seconds for Reels, up to 60 minutes for IGTV",
                "hook": "Visually appealing, story-driven",
                "features": "Stories, Reels, IGTV, Shopping",
                "audience": "Visual-focused, lifestyle-oriented"
            },
            "linkedin": {
                "format": "Landscape (16:9) or Square (1:1)",
                "optimal_length": "30 seconds to 3 minutes",
                "hook": "Professional value proposition",
                "features": "Native video, professional context",
                "audience": "Professionals, B2B, career-focused"
            },
            "facebook": {
                "format": "Square (1:1) or Landscape (16:9)",
                "optimal_length": "1-3 minutes",
                "hook": "Engaging, shareable content",
                "features": "Auto-play, captions, sharing",
                "audience": "Diverse demographics, community-focused"
            }
        }

        platform_info = platform_specs.get(platform.lower(), platform_specs["youtube"])

        system_message = f"""You are a social media content strategist specializing in {platform}. Optimize the given video script for this platform.

Platform specifications:
- Format: {platform_info['format']}
- Optimal length: {platform_info['optimal_length']}
- Hook strategy: {platform_info['hook']}
- Key features: {platform_info['features']}
- Target audience: {platform_info['audience']}

{"Target duration: " + str(duration) + " seconds" if duration else ""}

Ensure the optimized script maximizes engagement and performance on {platform}."""

        messages = [
            {"role": "user", "content": f"Optimize this script for {platform}:\n\n{script}"}
        ]

        return self.chat_completion(messages, system_message=system_message)

    def generate_script_variations(self, script: str, count: int = 3, variation_type: str = "tone") -> Dict[str, Any]:
        """Tạo các biến thể của script"""
        variation_instructions = {
            "tone": "Create variations with different tones (formal, casual, humorous, dramatic, etc.)",
            "length": "Create variations with different lengths (short, medium, long versions)",
            "audience": "Create variations for different target audiences (beginners, experts, general)",
            "style": "Create variations with different presentation styles (narrative, instructional, conversational)",
            "platform": "Create variations optimized for different platforms (YouTube, TikTok, LinkedIn)"
        }

        system_message = f"""Create {count} variations of the given video script. Variation focus: {variation_instructions.get(variation_type, variation_instructions['tone'])}

Ensure each variation:
- Maintains the core message
- Has a distinct approach or style
- Is clearly labeled with its variation type
- Provides the same key information but presented differently"""

        messages = [
            {"role": "user", "content": f"Create {count} {variation_type} variations of this script:\n\n{script}"}
        ]

        return self.chat_completion(messages, system_message=system_message)

    def generate_captions_and_subtitles(self, script: str, format_type: str = "srt") -> Dict[str, Any]:
        """Tạo captions và subtitles"""
        system_message = f"""Generate captions/subtitles for the given video script in {format_type} format.

Requirements:
- Break text into appropriate subtitle chunks (max 2 lines, 42 characters per line)
- Time segments appropriately (2-6 seconds per subtitle)
- Ensure readability and proper synchronization
- Include speaker identification if multiple speakers
- Add [Music], [Sound effects] notations where appropriate

Format: {format_type.upper()}"""

        messages = [
            {"role": "user", "content": f"Generate {format_type} captions for this script:\n\n{script}"}
        ]

        return self.chat_completion(messages, system_message=system_message)

    def extract_key_quotes(self, script: str, count: int = 5) -> Dict[str, Any]:
        """Trích xuất quotes quan trọng từ script"""
        system_message = f"""Extract {count} key quotes from the given video script that would work well as:
- Social media posts
- Thumbnails text
- Highlight clips
- Marketing materials

For each quote:
- Provide the exact text
- Explain why it's impactful
- Suggest best use case
- Recommend visual treatment"""

        messages = [
            {"role": "user", "content": f"Extract key quotes from this script:\n\n{script}"}
        ]

        return self.chat_completion(messages, system_message=system_message)

    def count_tokens(self, text: str) -> int:
        """Ước tính số token (approximate)"""
        # Rough estimation: 1 token ≈ 0.75 words for English
        words = len(text.split())
        return int(words / 0.75)

    def get_supported_models(self) -> List[str]:
        """Lấy danh sách model được hỗ trợ"""
        return [
            'gpt-4-turbo',
            'gpt-4',
            'gpt-4-turbo-preview',
            'gpt-3.5-turbo',
            'gpt-3.5-turbo-16k',
            'text-davinci-003',
            'text-davinci-002'
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

def create_client(config: Dict[str, Any]) -> OpenAIClient:
    """Factory function để tạo OpenAI client"""
    return OpenAIClient(config)

def test_client():
    """Test function"""
    config = {
        'api_key': 'your-api-key',
        'organization': 'your-org-id',  # optional
        'model': 'gpt-4-turbo',
        'max_tokens': 4096,
        'temperature': 0.7,
        'rate_limit': 500
    }

    client = create_client(config)

    # Test text generation
    result = client.generate_text(
        prompt="Write a creative 30-second video script about artificial intelligence"
    )

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_client()
