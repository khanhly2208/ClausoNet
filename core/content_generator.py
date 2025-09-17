#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Content Generator
Module để tạo content sử dụng ChatGPT và Gemini AI
"""

import os
import sys
import json
import time
import asyncio
from typing import Dict, Any, List, Optional, Union
import logging
from datetime import datetime
from pathlib import Path

# Import API clients
try:
    from api.gemini_handler import GeminiClient
except ImportError:
    GeminiClient = None

try:
    from api.openai_connector import OpenAIClient
except ImportError:
    OpenAIClient = None

class ContentGenerator:
    """Tạo content sử dụng ChatGPT và Gemini AI"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.setup_logging()
        
        # Initialize API clients
        self.gemini_client = None
        self.openai_client = None
        
        self.initialize_clients()
    
    def setup_logging(self):
        """Thiết lập logging"""
        self.logger = logging.getLogger('ContentGenerator')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def initialize_clients(self):
        """Khởi tạo API clients"""
        # Initialize Gemini client
        gemini_config = self.config.get('gemini', {})
        if gemini_config.get('api_key') and GeminiClient:
            try:
                self.gemini_client = GeminiClient(gemini_config)
                self.logger.info("Gemini client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini client: {e}")
        
        # Initialize OpenAI client
        openai_config = self.config.get('openai', {})
        if openai_config.get('api_key') and OpenAIClient:
            try:
                self.openai_client = OpenAIClient(openai_config)
                self.logger.info("OpenAI client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def set_api_key(self, provider: str, api_key: str):
        """Cập nhật API key cho provider cụ thể"""
        if provider.lower() == 'gemini':
            if not self.config.get('gemini'):
                self.config['gemini'] = {}
            self.config['gemini']['api_key'] = api_key
            
            # Reinitialize Gemini client
            if GeminiClient:
                try:
                    # Ensure default model is set
                    if 'model' not in self.config['gemini']:
                        self.config['gemini']['model'] = 'gemini-2.5-flash'
                    self.gemini_client = GeminiClient(self.config['gemini'])
                    self.logger.info("Gemini client reinitialized with new API key")
                except Exception as e:
                    self.logger.error(f"Failed to reinitialize Gemini client: {e}")
        
        elif provider.lower() in ['openai', 'chatgpt']:
            if not self.config.get('openai'):
                self.config['openai'] = {}
            self.config['openai']['api_key'] = api_key
            
            # Reinitialize OpenAI client
            if OpenAIClient:
                try:
                    self.openai_client = OpenAIClient(self.config['openai'])
                    self.logger.info("OpenAI client reinitialized with new API key")
                except Exception as e:
                    self.logger.error(f"Failed to reinitialize OpenAI client: {e}")
    
    def is_provider_available(self, provider: str) -> bool:
        """Kiểm tra provider có sẵn không"""
        if provider.lower() == 'gemini':
            return self.gemini_client is not None
        elif provider.lower() in ['openai', 'chatgpt']:
            return self.openai_client is not None
        return False
    
    def get_available_providers(self) -> List[str]:
        """Lấy danh sách provider có sẵn"""
        providers = []
        if self.gemini_client:
            providers.append('gemini')
        if self.openai_client:
            providers.append('chatgpt')
        return providers
    
    def enhance_script(self, 
                      script: str, 
                      provider: str = 'gemini', 
                      style: str = 'professional',
                      custom_prompt: str = None) -> Dict[str, Any]:
        """
        Cải thiện script sử dụng AI
        
        Args:
            script: Script gốc cần cải thiện
            provider: 'gemini' hoặc 'chatgpt'
            style: Phong cách cải thiện
            custom_prompt: Prompt tùy chỉnh
        """
        if not script.strip():
            return {
                'status': 'error',
                'error_message': 'Script không được để trống'
            }
        
        provider = provider.lower()
        
        try:
            if provider == 'gemini' and self.gemini_client:
                if custom_prompt:
                    # Sử dụng custom prompt
                    full_prompt = f"{custom_prompt}\n\nScript gốc:\n{script}"
                    result = self.gemini_client.generate_content(prompt=full_prompt)
                else:
                    # Sử dụng method có sẵn
                    result = self.gemini_client.enhance_video_script(script, style)
                
                if result.get('status') == 'success':
                    return {
                        'status': 'success',
                        'enhanced_script': result.get('response', ''),
                        'provider': 'Gemini',
                        'original_script': script,
                        'style': style,
                        'response_time': result.get('response_time', 0),
                        'usage': result.get('usage', {}),
                        'created_at': datetime.now().isoformat()
                    }
                else:
                    return result
            
            elif provider in ['chatgpt', 'openai'] and self.openai_client:
                if custom_prompt:
                    # Sử dụng custom prompt
                    result = self.openai_client.generate_text(
                        prompt=f"{custom_prompt}\n\nScript gốc:\n{script}"
                    )
                else:
                    # Sử dụng method có sẵn
                    result = self.openai_client.enhance_video_script(script, style)
                
                if result.get('status') == 'success':
                    return {
                        'status': 'success',
                        'enhanced_script': result.get('response', ''),
                        'provider': 'ChatGPT',
                        'original_script': script,
                        'style': style,
                        'response_time': result.get('response_time', 0),
                        'usage': result.get('usage', {}),
                        'created_at': datetime.now().isoformat()
                    }
                else:
                    return result
            
            else:
                return {
                    'status': 'error',
                    'error_message': f'Provider {provider} không có sẵn hoặc chưa được cấu hình'
                }
        
        except Exception as e:
            self.logger.error(f"Error enhancing script with {provider}: {e}")
            return {
                'status': 'error',
                'error_message': f'Lỗi khi cải thiện script: {str(e)}'
            }
    
    def generate_video_prompts(self, 
                              script: str, 
                              provider: str = 'gemini',
                              style: str = 'cinematic',
                              video_duration: int = 48) -> Dict[str, Any]:
        """
        Tạo prompts cho AI video generation từ script
        
        Args:
            script: Script gốc
            provider: 'gemini' hoặc 'chatgpt'
            style: Phong cách video (cinematic, realistic, artistic, etc.)
        """
        if not script.strip():
            return {
                'status': 'error',
                'error_message': 'Script không được để trống'
            }
        
        provider = provider.lower()
        
        try:
            if provider == 'gemini' and self.gemini_client:
                result = self.gemini_client.generate_prompts_for_video_ai(script, video_duration)
                
                if result.get('status') == 'success':
                    return {
                        'status': 'success',
                        'video_prompts': result.get('response', ''),
                        'provider': 'Gemini',
                        'original_script': script,
                        'style': style,
                        'response_time': result.get('response_time', 0),
                        'usage': result.get('usage', {}),
                        'created_at': datetime.now().isoformat()
                    }
                else:
                    return result
            
            elif provider in ['chatgpt', 'openai'] and self.openai_client:
                result = self.openai_client.generate_video_prompts_for_ai(script, style)
                
                if result.get('status') == 'success':
                    return {
                        'status': 'success',
                        'video_prompts': result.get('response', ''),
                        'provider': 'ChatGPT',
                        'original_script': script,
                        'style': style,
                        'response_time': result.get('response_time', 0),
                        'usage': result.get('usage', {}),
                        'created_at': datetime.now().isoformat()
                    }
                else:
                    return result
            
            else:
                return {
                    'status': 'error',
                    'error_message': f'Provider {provider} không có sẵn hoặc chưa được cấu hình'
                }
        
        except Exception as e:
            self.logger.error(f"Error generating video prompts with {provider}: {e}")
            return {
                'status': 'error',
                'error_message': f'Lỗi khi tạo video prompts: {str(e)}'
            }
    
    def analyze_script(self, 
                      script: str, 
                      provider: str = 'gemini',
                      analysis_type: str = 'structure') -> Dict[str, Any]:
        """
        Phân tích script
        
        Args:
            script: Script cần phân tích
            provider: 'gemini' hoặc 'chatgpt'
            analysis_type: 'structure', 'effectiveness', 'scenes'
        """
        if not script.strip():
            return {
                'status': 'error',
                'error_message': 'Script không được để trống'
            }
        
        provider = provider.lower()
        
        try:
            if provider == 'gemini' and self.gemini_client:
                if analysis_type == 'structure':
                    result = self.gemini_client.analyze_script_structure(script)
                elif analysis_type == 'scenes':
                    result = self.gemini_client.generate_scene_descriptions(script)
                else:
                    # Default structure analysis
                    result = self.gemini_client.analyze_script_structure(script)
                
                if result.get('status') == 'success':
                    return {
                        'status': 'success',
                        'analysis': result.get('response', ''),
                        'provider': 'Gemini',
                        'analysis_type': analysis_type,
                        'original_script': script,
                        'response_time': result.get('response_time', 0),
                        'usage': result.get('usage', {}),
                        'created_at': datetime.now().isoformat()
                    }
                else:
                    return result
            
            elif provider in ['chatgpt', 'openai'] and self.openai_client:
                if analysis_type == 'effectiveness':
                    result = self.openai_client.analyze_script_effectiveness(script)
                elif analysis_type == 'storyboard':
                    result = self.openai_client.create_detailed_storyboard(script)
                else:
                    # Default effectiveness analysis
                    result = self.openai_client.analyze_script_effectiveness(script)
                
                if result.get('status') == 'success':
                    return {
                        'status': 'success',
                        'analysis': result.get('response', ''),
                        'provider': 'ChatGPT',
                        'analysis_type': analysis_type,
                        'original_script': script,
                        'response_time': result.get('response_time', 0),
                        'usage': result.get('usage', {}),
                        'created_at': datetime.now().isoformat()
                    }
                else:
                    return result
            
            else:
                return {
                    'status': 'error',
                    'error_message': f'Provider {provider} không có sẵn hoặc chưa được cấu hình'
                }
        
        except Exception as e:
            self.logger.error(f"Error analyzing script with {provider}: {e}")
            return {
                'status': 'error',
                'error_message': f'Lỗi khi phân tích script: {str(e)}'
            }
    
    def optimize_for_platform(self, 
                             script: str, 
                             platform: str,
                             provider: str = 'gemini',
                             duration: int = None) -> Dict[str, Any]:
        """
        Tối ưu script cho platform cụ thể
        
        Args:
            script: Script gốc
            platform: youtube, tiktok, instagram, linkedin, facebook
            provider: 'gemini' hoặc 'chatgpt'
            duration: Thời lượng mong muốn (giây)
        """
        if not script.strip():
            return {
                'status': 'error',
                'error_message': 'Script không được để trống'
            }
        
        provider = provider.lower()
        
        try:
            if provider == 'gemini' and self.gemini_client:
                result = self.gemini_client.optimize_for_platform(script, platform)
                
                if result.get('status') == 'success':
                    return {
                        'status': 'success',
                        'optimized_script': result.get('response', ''),
                        'provider': 'Gemini',
                        'platform': platform,
                        'duration': duration,
                        'original_script': script,
                        'response_time': result.get('response_time', 0),
                        'usage': result.get('usage', {}),
                        'created_at': datetime.now().isoformat()
                    }
                else:
                    return result
            
            elif provider in ['chatgpt', 'openai'] and self.openai_client:
                result = self.openai_client.optimize_for_platform(script, platform, duration)
                
                if result.get('status') == 'success':
                    return {
                        'status': 'success',
                        'optimized_script': result.get('response', ''),
                        'provider': 'ChatGPT',
                        'platform': platform,
                        'duration': duration,
                        'original_script': script,
                        'response_time': result.get('response_time', 0),
                        'usage': result.get('usage', {}),
                        'created_at': datetime.now().isoformat()
                    }
                else:
                    return result
            
            else:
                return {
                    'status': 'error',
                    'error_message': f'Provider {provider} không có sẵn hoặc chưa được cấu hình'
                }
        
        except Exception as e:
            self.logger.error(f"Error optimizing script for {platform} with {provider}: {e}")
            return {
                'status': 'error',
                'error_message': f'Lỗi khi tối ưu script cho {platform}: {str(e)}'
            }
    
    def generate_concepts(self, 
                         topic: str, 
                         provider: str = 'gemini',
                         count: int = 5,
                         style: str = 'mixed') -> Dict[str, Any]:
        """
        Tạo concepts cho video từ topic
        
        Args:
            topic: Chủ đề video
            provider: 'gemini' hoặc 'chatgpt'
            count: Số lượng concepts
            style: Phong cách concepts
        """
        if not topic.strip():
            return {
                'status': 'error',
                'error_message': 'Topic không được để trống'
            }
        
        provider = provider.lower()
        
        try:
            if provider == 'gemini' and self.gemini_client:
                result = self.gemini_client.generate_video_concepts(topic, count, style)
                
                if result.get('status') == 'success':
                    return {
                        'status': 'success',
                        'concepts': result.get('response', ''),
                        'provider': 'Gemini',
                        'topic': topic,
                        'count': count,
                        'style': style,
                        'response_time': result.get('response_time', 0),
                        'usage': result.get('usage', {}),
                        'created_at': datetime.now().isoformat()
                    }
                else:
                    return result
            
            elif provider in ['chatgpt', 'openai'] and self.openai_client:
                result = self.openai_client.generate_video_concepts(topic, count, "general")
                
                if result.get('status') == 'success':
                    return {
                        'status': 'success',
                        'concepts': result.get('response', ''),
                        'provider': 'ChatGPT',
                        'topic': topic,
                        'count': count,
                        'style': style,
                        'response_time': result.get('response_time', 0),
                        'usage': result.get('usage', {}),
                        'created_at': datetime.now().isoformat()
                    }
                else:
                    return result
            
            else:
                return {
                    'status': 'error',
                    'error_message': f'Provider {provider} không có sẵn hoặc chưa được cấu hình'
                }
        
        except Exception as e:
            self.logger.error(f"Error generating concepts with {provider}: {e}")
            return {
                'status': 'error',
                'error_message': f'Lỗi khi tạo concepts: {str(e)}'
            }
    
    def custom_generate(self, 
                       prompt: str, 
                       provider: str = 'gemini',
                       system_message: str = None) -> Dict[str, Any]:
        """
        Tạo content tùy chỉnh với prompt riêng
        
        Args:
            prompt: Prompt tùy chỉnh
            provider: 'gemini' hoặc 'chatgpt'
            system_message: System message (chỉ cho ChatGPT)
        """
        if not prompt.strip():
            return {
                'status': 'error',
                'error_message': 'Prompt không được để trống'
            }
        
        provider = provider.lower()
        
        try:
            if provider == 'gemini' and self.gemini_client:
                result = self.gemini_client.generate_content(
                    prompt=prompt,
                    system_instruction=system_message
                )
                
                if result.get('status') == 'success':
                    return {
                        'status': 'success',
                        'content': result.get('response', ''),
                        'provider': 'Gemini',
                        'prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt,
                        'response_time': result.get('response_time', 0),
                        'usage': result.get('usage', {}),
                        'created_at': datetime.now().isoformat()
                    }
                else:
                    return result
            
            elif provider in ['chatgpt', 'openai'] and self.openai_client:
                result = self.openai_client.generate_text(
                    prompt=prompt,
                    system_message=system_message
                )
                
                if result.get('status') == 'success':
                    return {
                        'status': 'success',
                        'content': result.get('response', ''),
                        'provider': 'ChatGPT',
                        'prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt,
                        'response_time': result.get('response_time', 0),
                        'usage': result.get('usage', {}),
                        'created_at': datetime.now().isoformat()
                    }
                else:
                    return result
            
            else:
                return {
                    'status': 'error',
                    'error_message': f'Provider {provider} không có sẵn hoặc chưa được cấu hình'
                }
        
        except Exception as e:
            self.logger.error(f"Error generating custom content with {provider}: {e}")
            return {
                'status': 'error',
                'error_message': f'Lỗi khi tạo content tùy chỉnh: {str(e)}'
            }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Lấy thống kê sử dụng từ các clients"""
        stats = {
            'providers_available': self.get_available_providers(),
            'gemini_stats': None,
            'openai_stats': None
        }
        
        if self.gemini_client:
            try:
                stats['gemini_stats'] = self.gemini_client.get_usage_statistics()
            except:
                pass
        
        if self.openai_client:
            try:
                stats['openai_stats'] = self.openai_client.get_usage_statistics()
            except:
                pass
        
        return stats

def create_content_generator(config: Dict[str, Any] = None) -> ContentGenerator:
    """Factory function để tạo ContentGenerator"""
    return ContentGenerator(config)

if __name__ == "__main__":
    print("ContentGenerator module loaded successfully") 