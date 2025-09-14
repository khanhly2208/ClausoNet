#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - API Manager
Quản lý tất cả các API clients và cung cấp interface thống nhất
"""

import os
import sys
import json
import yaml
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime

# Import API clients
try:
    from .google_veo3 import GoogleVeo3Client, create_client as create_veo_client
except ImportError:
    GoogleVeo3Client = None
    create_veo_client = None

try:
    from .gemini_handler import GeminiClient, create_client as create_gemini_client
except ImportError:
    GeminiClient = None
    create_gemini_client = None

try:
    from .openai_connector import OpenAIClient, create_client as create_openai_client
except ImportError:
    OpenAIClient = None
    create_openai_client = None

class APIManager:
    """Quản lý tất cả các API clients"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "config.yaml"
        self.config = {}
        self.clients = {}
        
        self.setup_logging()
        self.load_config()
        self.initialize_clients()
    
    def setup_logging(self):
        """Thiết lập logging"""
        self.logger = logging.getLogger('APIManager')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def load_config(self):
        """Load configuration từ file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f) or {}
                self.logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self.logger.warning(f"Configuration file not found: {self.config_path}")
                self.config = self.get_default_config()
                self.save_config()
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.config = self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Tạo config mặc định"""
        return {
            'google_veo3': {
                'project_id': '',
                'location': 'us-central1',
                'api_key': '',
                'model_version': 'veo-3-preview',
                'max_duration': 60,
                'resolution': '1080p',
                'rate_limit': 10
            },
            'gemini': {
                'api_key': '',
                'model': 'gemini-pro',
                'max_tokens': 8192,
                'temperature': 0.7,
                'top_p': 0.9,
                'top_k': 40,
                'rate_limit': 60
            },
            'openai': {
                'api_key': '',
                'organization': '',
                'model': 'gpt-4-turbo',
                'max_tokens': 4096,
                'temperature': 0.7,
                'top_p': 1.0,
                'frequency_penalty': 0.0,
                'presence_penalty': 0.0,
                'rate_limit': 500
            }
        }
    
    def save_config(self):
        """Lưu configuration ra file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            self.logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def initialize_clients(self):
        """Khởi tạo tất cả API clients"""
        # Initialize Google Veo 3
        if create_veo_client and self.config.get('google_veo3', {}).get('api_key'):
            try:
                self.clients['google_veo3'] = create_veo_client(self.config['google_veo3'])
                self.logger.info("Google Veo 3 client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Google Veo 3 client: {e}")
        
        # Initialize Gemini
        if create_gemini_client and self.config.get('gemini', {}).get('api_key'):
            try:
                self.clients['gemini'] = create_gemini_client(self.config['gemini'])
                self.logger.info("Gemini client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini client: {e}")
        
        # Initialize OpenAI
        if create_openai_client and self.config.get('openai', {}).get('api_key'):
            try:
                self.clients['openai'] = create_openai_client(self.config['openai'])
                self.logger.info("OpenAI client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def get_client(self, client_name: str):
        """Lấy client theo tên"""
        return self.clients.get(client_name)
    
    def is_client_available(self, client_name: str) -> bool:
        """Kiểm tra client có sẵn không"""
        return client_name in self.clients
    
    def get_available_clients(self) -> List[str]:
        """Lấy danh sách client có sẵn"""
        return list(self.clients.keys())
    
    def test_all_connections(self) -> Dict[str, Any]:
        """Test kết nối tới tất cả APIs"""
        results = {}
        
        for client_name, client in self.clients.items():
            try:
                start_time = datetime.now()
                
                if client_name == 'google_veo3':
                    # Test with simple video generation request
                    result = client.generate_video(
                        prompt="Test video generation",
                        duration=5,
                        resolution="720p"
                    )
                    status = result.get('status', 'unknown')
                
                elif client_name == 'gemini':
                    # Test with simple content generation
                    result = client.generate_content(prompt="Hello, this is a test.")
                    status = result.get('status', 'unknown')
                
                elif client_name == 'openai':
                    # Test with simple text generation
                    result = client.generate_text(prompt="Hello, this is a test.")
                    status = result.get('status', 'unknown')
                
                else:
                    status = 'unknown'
                    result = {'error': 'Unknown client type'}
                
                response_time = (datetime.now() - start_time).total_seconds()
                
                results[client_name] = {
                    'status': status,
                    'response_time': response_time,
                    'available': status == 'success',
                    'error': result.get('error_message') if status == 'error' else None
                }
                
            except Exception as e:
                results[client_name] = {
                    'status': 'error',
                    'available': False,
                    'error': str(e)
                }
        
        return results
    
    # Video Generation Methods
    def generate_video(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Tạo video sử dụng Google Veo 3"""
        if not self.is_client_available('google_veo3'):
            return {
                'status': 'error',
                'error_message': 'Google Veo 3 client not available'
            }
        
        return self.clients['google_veo3'].generate_video(prompt, **kwargs)
    
    def poll_video_status(self, operation_id: str) -> Dict[str, Any]:
        """Kiểm tra trạng thái video generation"""
        if not self.is_client_available('google_veo3'):
            return {
                'status': 'error',
                'error_message': 'Google Veo 3 client not available'
            }
        
        return self.clients['google_veo3'].poll_operation_status(operation_id)
    
    def wait_for_video_completion(self, operation_id: str, **kwargs) -> Dict[str, Any]:
        """Chờ video generation hoàn thành"""
        if not self.is_client_available('google_veo3'):
            return {
                'status': 'error',
                'error_message': 'Google Veo 3 client not available'
            }
        
        return self.clients['google_veo3'].wait_for_completion(operation_id, **kwargs)
    
    def download_video(self, video_uri: str, output_path: str) -> bool:
        """Download video"""
        if not self.is_client_available('google_veo3'):
            return False
        
        return self.clients['google_veo3'].download_video(video_uri, output_path)
    
    # Content Enhancement Methods
    def enhance_script_with_gemini(self, script: str, style: str = "professional") -> Dict[str, Any]:
        """Cải thiện script với Gemini"""
        if not self.is_client_available('gemini'):
            return {
                'status': 'error',
                'error_message': 'Gemini client not available'
            }
        
        return self.clients['gemini'].enhance_video_script(script, style)
    
    def enhance_script_with_openai(self, script: str, style: str = "professional") -> Dict[str, Any]:
        """Cải thiện script với OpenAI"""
        if not self.is_client_available('openai'):
            return {
                'status': 'error',
                'error_message': 'OpenAI client not available'
            }
        
        return self.clients['openai'].enhance_video_script(script, style)
    
    def analyze_image_with_gemini(self, image_path: str, prompt: str = "Describe this image") -> Dict[str, Any]:
        """Phân tích ảnh với Gemini Vision"""
        if not self.is_client_available('gemini'):
            return {
                'status': 'error',
                'error_message': 'Gemini client not available'
            }
        
        return self.clients['gemini'].analyze_image(image_path, prompt)
    
    def generate_video_concepts(self, topic: str, client: str = "gemini", **kwargs) -> Dict[str, Any]:
        """Tạo video concepts"""
        if client == "gemini" and self.is_client_available('gemini'):
            return self.clients['gemini'].generate_video_concepts(topic, **kwargs)
        elif client == "openai" and self.is_client_available('openai'):
            return self.clients['openai'].generate_video_concepts(topic, **kwargs)
        else:
            return {
                'status': 'error',
                'error_message': f'{client} client not available'
            }
    
    def create_storyboard(self, script: str, client: str = "openai") -> Dict[str, Any]:
        """Tạo storyboard"""
        if client == "openai" and self.is_client_available('openai'):
            return self.clients['openai'].create_detailed_storyboard(script)
        elif client == "gemini" and self.is_client_available('gemini'):
            return self.clients['gemini'].create_storyboard_text(script)
        else:
            return {
                'status': 'error',
                'error_message': f'{client} client not available'
            }
    
    def generate_video_prompts(self, script: str, client: str = "gemini") -> Dict[str, Any]:
        """Tạo prompts cho AI video generation"""
        if client == "gemini" and self.is_client_available('gemini'):
            return self.clients['gemini'].generate_prompts_for_video_ai(script)
        elif client == "openai" and self.is_client_available('openai'):
            return self.clients['openai'].generate_video_prompts_for_ai(script)
        else:
            return {
                'status': 'error',
                'error_message': f'{client} client not available'
            }
    
    def optimize_for_platform(self, script: str, platform: str, client: str = "openai") -> Dict[str, Any]:
        """Tối ưu script cho platform"""
        if client == "openai" and self.is_client_available('openai'):
            return self.clients['openai'].optimize_for_platform(script, platform)
        elif client == "gemini" and self.is_client_available('gemini'):
            return self.clients['gemini'].optimize_for_platform(script, platform)
        else:
            return {
                'status': 'error',
                'error_message': f'{client} client not available'
            }
    
    # Workflow Methods
    def full_video_workflow(self, 
                          initial_prompt: str,
                          enhancement_style: str = "professional",
                          platform: str = "youtube",
                          video_style: str = "cinematic",
                          duration: int = 30) -> Dict[str, Any]:
        """Workflow hoàn chỉnh từ prompt đến video"""
        workflow_results = {
            'initial_prompt': initial_prompt,
            'steps': [],
            'final_results': {}
        }
        
        try:
            # Step 1: Generate initial script
            self.logger.info("Step 1: Generating initial script...")
            if self.is_client_available('openai'):
                script_result = self.clients['openai'].generate_text(
                    f"Write a {duration}-second video script about: {initial_prompt}"
                )
                workflow_results['steps'].append({
                    'step': 1,
                    'description': 'Generate initial script',
                    'status': script_result.get('status'),
                    'result': script_result
                })
                
                if script_result.get('status') != 'success':
                    return workflow_results
                
                initial_script = script_result.get('response', '')
            else:
                workflow_results['steps'].append({
                    'step': 1,
                    'description': 'Generate initial script',
                    'status': 'error',
                    'error': 'OpenAI client not available'
                })
                return workflow_results
            
            # Step 2: Enhance script
            self.logger.info("Step 2: Enhancing script...")
            enhanced_result = self.enhance_script_with_openai(initial_script, enhancement_style)
            workflow_results['steps'].append({
                'step': 2,
                'description': 'Enhance script',
                'status': enhanced_result.get('status'),
                'result': enhanced_result
            })
            
            if enhanced_result.get('status') == 'success':
                final_script = enhanced_result.get('response', initial_script)
            else:
                final_script = initial_script
            
            # Step 3: Optimize for platform
            self.logger.info(f"Step 3: Optimizing for {platform}...")
            platform_result = self.optimize_for_platform(final_script, platform)
            workflow_results['steps'].append({
                'step': 3,
                'description': f'Optimize for {platform}',
                'status': platform_result.get('status'),
                'result': platform_result
            })
            
            if platform_result.get('status') == 'success':
                final_script = platform_result.get('response', final_script)
            
            # Step 4: Generate video prompts
            self.logger.info("Step 4: Generating video prompts...")
            prompts_result = self.generate_video_prompts(final_script)
            workflow_results['steps'].append({
                'step': 4,
                'description': 'Generate video prompts',
                'status': prompts_result.get('status'),
                'result': prompts_result
            })
            
            # Step 5: Generate video (if Google Veo 3 available)
            if self.is_client_available('google_veo3'):
                self.logger.info("Step 5: Generating video...")
                video_result = self.generate_video(
                    prompt=final_script[:500],  # Truncate if too long
                    duration=duration,
                    style=video_style
                )
                workflow_results['steps'].append({
                    'step': 5,
                    'description': 'Generate video',
                    'status': video_result.get('status'),
                    'result': video_result
                })
                
                workflow_results['final_results']['video'] = video_result
            else:
                workflow_results['steps'].append({
                    'step': 5,
                    'description': 'Generate video',
                    'status': 'skipped',
                    'error': 'Google Veo 3 client not available'
                })
            
            # Final results
            workflow_results['final_results'].update({
                'initial_script': initial_script,
                'final_script': final_script,
                'video_prompts': prompts_result.get('response', ''),
                'workflow_status': 'completed'
            })
            
        except Exception as e:
            self.logger.error(f"Workflow error: {e}")
            workflow_results['final_results']['workflow_status'] = 'error'
            workflow_results['final_results']['error'] = str(e)
        
        return workflow_results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Lấy trạng thái hệ thống"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'clients': {},
            'configuration': {
                'config_file': self.config_path,
                'config_exists': os.path.exists(self.config_path)
            }
        }
        
        # Check each client
        for client_name in ['google_veo3', 'gemini', 'openai']:
            client_config = self.config.get(client_name, {})
            has_api_key = bool(client_config.get('api_key'))
            is_initialized = self.is_client_available(client_name)
            
            status['clients'][client_name] = {
                'configured': has_api_key,
                'initialized': is_initialized,
                'status': 'ready' if (has_api_key and is_initialized) else 'not_configured'
            }
            
            if is_initialized:
                client = self.get_client(client_name)
                if hasattr(client, 'get_usage_statistics'):
                    status['clients'][client_name]['usage'] = client.get_usage_statistics()
        
        return status

def create_api_manager(config_path: str = None) -> APIManager:
    """Factory function để tạo API Manager"""
    return APIManager(config_path)

def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ClausoNet 4.0 Pro API Manager')
    parser.add_argument('--config', '-c', default='config.yaml', help='Configuration file path')
    parser.add_argument('--test', '-t', action='store_true', help='Test all API connections')
    parser.add_argument('--status', '-s', action='store_true', help='Show system status')
    
    args = parser.parse_args()
    
    # Create API manager
    manager = create_api_manager(args.config)
    
    if args.test:
        print("Testing API connections...")
        results = manager.test_all_connections()
        print(json.dumps(results, indent=2))
    
    if args.status:
        print("System status:")
        status = manager.get_system_status()
        print(json.dumps(status, indent=2))
    
    if not args.test and not args.status:
        print("API Manager initialized successfully!")
        print(f"Available clients: {manager.get_available_clients()}")

if __name__ == "__main__":
    main()
