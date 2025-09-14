#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Google Veo 3 API Integration
Tích hợp với Google Veo 3 để tạo video từ text prompts
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

class GoogleVeo3Client:
    def __init__(self, config: Dict[str, Any]):
        self.project_id = config.get('project_id', '')
        self.location = config.get('location', 'us-central1')
        self.api_key = config.get('api_key', '')
        self.model_version = config.get('model_version', 'veo-3-preview')
        self.max_duration = config.get('max_duration', 60)
        self.resolution = config.get('resolution', '1080p')
        self.rate_limit = config.get('rate_limit', 10)

        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
        self.request_window_start = time.time()

        # Authentication
        self.credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self.access_token = None
        self.token_expiry = None

        self.setup_logging()
        self.initialize_client()

    def setup_logging(self):
        """Thiết lập logging"""
        self.logger = logging.getLogger('GoogleVeo3Client')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def initialize_client(self):
        """Khởi tạo client"""
        try:
            if self.credentials_path and os.path.exists(self.credentials_path):
                # Use service account credentials
                self.setup_service_account_auth()
            elif self.api_key:
                # Use API key authentication
                self.logger.info("Using API key authentication")
            else:
                raise ValueError("No valid authentication method found")

        except Exception as e:
            self.logger.error(f"Failed to initialize Google Veo 3 client: {e}")
            raise

    def setup_service_account_auth(self):
        """Thiết lập xác thực service account"""
        try:
            from google.auth import default
            from google.auth.transport.requests import Request

            credentials, _ = default()

            if credentials.expired:
                credentials.refresh(Request())

            self.access_token = credentials.token
            self.token_expiry = credentials.expiry
            self.logger.info("Service account authentication configured")

        except ImportError:
            self.logger.error("Google Auth library not installed. Run: pip install google-auth")
            raise
        except Exception as e:
            self.logger.error(f"Failed to setup service account auth: {e}")
            raise

    def get_auth_headers(self) -> Dict[str, str]:
        """Lấy headers xác thực"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'ClausoNet-4.0-Pro/1.0'
        }

        if self.access_token:
            # Check if token needs refresh
            if self.token_expiry and datetime.now() >= self.token_expiry:
                self.setup_service_account_auth()

            headers['Authorization'] = f'Bearer {self.access_token}'
        elif self.api_key:
            headers['X-API-Key'] = self.api_key

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

        # Enforce minimum time between requests
        time_since_last = current_time - self.last_request_time
        min_interval = 60 / self.rate_limit  # seconds

        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            time.sleep(wait_time)

        self.last_request_time = time.time()
        self.request_count += 1

    def validate_prompt(self, prompt: str) -> bool:
        """Validate prompt content"""
        if not prompt or len(prompt.strip()) == 0:
            return False

        if len(prompt) > 2000:  # Arbitrary limit
            self.logger.warning("Prompt is very long, may be truncated")

        # Check for potentially problematic content
        blocked_terms = ['violence', 'explicit', 'harmful']
        prompt_lower = prompt.lower()

        for term in blocked_terms:
            if term in prompt_lower:
                self.logger.warning(f"Prompt contains potentially blocked term: {term}")

        return True

    def generate_video(self,
                      prompt: str,
                      duration: int = None,
                      resolution: str = None,
                      style: str = "realistic",
                      aspect_ratio: str = "16:9",
                      additional_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Tạo video từ text prompt

        Args:
            prompt: Text description của video
            duration: Thời lượng video (giây)
            resolution: Độ phân giải (720p, 1080p, 4k)
            style: Style của video (realistic, artistic, animated)
            aspect_ratio: Tỷ lệ khung hình (16:9, 4:3, 1:1)
            additional_params: Các tham số bổ sung

        Returns:
            Dict chứa thông tin về video được tạo
        """
        try:
            # Validate inputs
            if not self.validate_prompt(prompt):
                raise ValueError("Invalid prompt")

            # Use default values if not provided
            duration = duration or self.max_duration
            resolution = resolution or self.resolution

            # Check rate limit
            self.check_rate_limit()

            # Prepare request
            request_data = {
                "prompt": prompt,
                "duration_seconds": min(duration, self.max_duration),
                "resolution": resolution,
                "style": style,
                "aspect_ratio": aspect_ratio,
                "model": self.model_version
            }

            if additional_params:
                request_data.update(additional_params)

            # Build API endpoint
            endpoint = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/videoGeneration:generate"

            # Make request
            headers = self.get_auth_headers()

            self.logger.info(f"Sending video generation request: {prompt[:50]}...")
            start_time = time.time()

            response = requests.post(
                endpoint,
                json=request_data,
                headers=headers,
                timeout=300  # 5 minutes timeout
            )

            response_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()

                # Extract video information
                video_info = {
                    'status': 'success',
                    'prompt': prompt,
                    'duration': duration,
                    'resolution': resolution,
                    'style': style,
                    'aspect_ratio': aspect_ratio,
                    'response_time': response_time,
                    'request_id': result.get('requestId'),
                    'video_uri': result.get('videoUri'),
                    'operation_id': result.get('operationId'),
                    'estimated_completion_time': result.get('estimatedCompletionTime'),
                    'created_at': datetime.now().isoformat()
                }

                # If operation is async, we may need to poll for completion
                if result.get('operationId'):
                    video_info['status'] = 'processing'
                    video_info['poll_url'] = f"{endpoint}/operations/{result['operationId']}"

                self.logger.info(f"Video generation initiated successfully in {response_time:.2f}s")
                return video_info

            else:
                error_info = {
                    'status': 'error',
                    'error_code': response.status_code,
                    'error_message': response.text,
                    'response_time': response_time,
                    'prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt
                }

                self.logger.error(f"Video generation failed: {response.status_code} - {response.text}")
                return error_info

        except requests.exceptions.Timeout:
            self.logger.error("Request timeout")
            return {
                'status': 'error',
                'error_message': 'Request timeout',
                'prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt
            }
        except Exception as e:
            self.logger.error(f"Video generation error: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt
            }

    def poll_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """Kiểm tra trạng thái operation"""
        try:
            endpoint = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/operations/{operation_id}"

            headers = self.get_auth_headers()
            response = requests.get(endpoint, headers=headers, timeout=30)

            if response.status_code == 200:
                result = response.json()

                status_info = {
                    'operation_id': operation_id,
                    'status': 'completed' if result.get('done', False) else 'processing',
                    'progress': result.get('metadata', {}).get('progressPercentage', 0),
                    'error': result.get('error'),
                    'result': result.get('response')
                }

                if result.get('done', False) and result.get('response'):
                    status_info['video_uri'] = result['response'].get('videoUri')

                return status_info
            else:
                return {
                    'operation_id': operation_id,
                    'status': 'error',
                    'error_message': f"HTTP {response.status_code}: {response.text}"
                }

        except Exception as e:
            return {
                'operation_id': operation_id,
                'status': 'error',
                'error_message': str(e)
            }

    def wait_for_completion(self, operation_id: str, max_wait_time: int = 600, poll_interval: int = 10) -> Dict[str, Any]:
        """Chờ operation hoàn thành"""
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            status = self.poll_operation_status(operation_id)

            if status['status'] == 'completed':
                self.logger.info(f"Operation {operation_id} completed successfully")
                return status
            elif status['status'] == 'error':
                self.logger.error(f"Operation {operation_id} failed: {status.get('error_message')}")
                return status

            self.logger.info(f"Operation {operation_id} progress: {status.get('progress', 0)}%")
            time.sleep(poll_interval)

        # Timeout
        self.logger.warning(f"Operation {operation_id} timeout after {max_wait_time} seconds")
        return {
            'operation_id': operation_id,
            'status': 'timeout',
            'error_message': f'Operation timeout after {max_wait_time} seconds'
        }

    def download_video(self, video_uri: str, output_path: str) -> bool:
        """Download video từ URI"""
        try:
            self.logger.info(f"Downloading video from: {video_uri}")

            headers = self.get_auth_headers()
            response = requests.get(video_uri, headers=headers, stream=True, timeout=300)

            if response.status_code == 200:
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)

                with open(output_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                file_size = output_file.stat().st_size
                self.logger.info(f"Video downloaded successfully: {output_path} ({file_size} bytes)")
                return True
            else:
                self.logger.error(f"Failed to download video: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            self.logger.error(f"Video download error: {e}")
            return False

    def get_supported_resolutions(self) -> List[str]:
        """Lấy danh sách độ phân giải được hỗ trợ"""
        return ['720p', '1080p', '4k']

    def get_supported_styles(self) -> List[str]:
        """Lấy danh sách style được hỗ trợ"""
        return ['realistic', 'artistic', 'animated', 'cinematic', 'documentary']

    def get_supported_aspect_ratios(self) -> List[str]:
        """Lấy danh sách aspect ratio được hỗ trợ"""
        return ['16:9', '4:3', '1:1', '9:16']

    def estimate_processing_time(self, duration: int, resolution: str) -> int:
        """Ước tính thời gian xử lý (giây)"""
        base_time = duration * 2  # 2 seconds processing per 1 second video

        resolution_multiplier = {
            '720p': 1.0,
            '1080p': 1.5,
            '4k': 3.0
        }

        multiplier = resolution_multiplier.get(resolution, 1.0)
        return int(base_time * multiplier)

    def get_usage_statistics(self) -> Dict[str, Any]:
        """Lấy thống kê sử dụng"""
        return {
            'requests_in_current_window': self.request_count,
            'rate_limit': self.rate_limit,
            'window_start': datetime.fromtimestamp(self.request_window_start).isoformat(),
            'last_request': datetime.fromtimestamp(self.last_request_time).isoformat() if self.last_request_time else None
        }

def create_client(config: Dict[str, Any]) -> GoogleVeo3Client:
    """Factory function để tạo Google Veo 3 client"""
    return GoogleVeo3Client(config)

if __name__ == "__main__":
    print("GoogleVeo3 module loaded successfully")
