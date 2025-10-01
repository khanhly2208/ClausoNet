#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Content Generator
AI-powered content generation for video scripts and prompts
"""

import asyncio
import logging
import json
import re
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import hashlib


class ContentGenerator:
    """
    AI Content Generator for ClausoNet 4.0 Pro
    Handles content generation, script processing, and AI interactions
    """
    
    def __init__(self, api_config: Dict[str, Any] = None):
        self.api_config = api_config or {}
        self.logger = logging.getLogger('ContentGenerator')
        self.setup_logging()
        
        # Content processing settings
        self.max_content_length = 10000
        self.min_content_length = 10
        self.default_language = 'vi'
        
        # API clients
        self.gemini_client = None
        self.openai_client = None
        
        # Cache for generated content
        self.content_cache = {}
        self.cache_max_size = 100
        
        self.initialize_apis()
    
    def setup_logging(self):
        """Setup logging for content generator"""
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def initialize_apis(self):
        """Initialize API clients based on configuration"""
        try:
            # Initialize Gemini API if configured
            gemini_config = self.api_config.get('gemini', {})
            if gemini_config.get('api_key'):
                self.logger.info("Gemini API configuration found")
                # Note: Actual Gemini client would be initialized here
                # For now, we'll simulate the API
                
            # Initialize OpenAI API if configured  
            openai_config = self.api_config.get('openai', {})
            if openai_config.get('api_key'):
                self.logger.info("OpenAI API configuration found")
                # Note: Actual OpenAI client would be initialized here
                
            self.logger.info("Content generator APIs initialized")
            
        except Exception as e:
            self.logger.error(f"API initialization error: {e}")
    
    def generate_content(self, prompt: str, content_type: str = "script", 
                        provider: str = "auto", **kwargs) -> Dict[str, Any]:
        """
        Generate content using AI
        
        Args:
            prompt: Input prompt for generation
            content_type: Type of content (script, description, etc.)
            provider: AI provider to use (gemini, openai, auto)
            **kwargs: Additional parameters
            
        Returns:
            Dict with generated content and metadata
        """
        try:
            # Validate input
            if not prompt or len(prompt.strip()) < self.min_content_length:
                return {
                    'success': False,
                    'error': 'Prompt too short or empty',
                    'content': ''
                }
            
            if len(prompt) > self.max_content_length:
                prompt = prompt[:self.max_content_length]
                self.logger.warning("Prompt truncated to maximum length")
            
            # Check cache first
            cache_key = self._generate_cache_key(prompt, content_type, provider)
            if cache_key in self.content_cache:
                self.logger.info("Returning cached content")
                return self.content_cache[cache_key]
            
            # Generate content based on provider
            if provider == "auto":
                provider = self._select_best_provider()
            
            result = self._generate_with_provider(prompt, content_type, provider, **kwargs)
            
            # Cache the result
            if result['success'] and len(self.content_cache) < self.cache_max_size:
                self.content_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Content generation error: {e}")
            return {
                'success': False,
                'error': str(e),
                'content': prompt  # Return original as fallback
            }
    
    def _generate_with_provider(self, prompt: str, content_type: str, 
                              provider: str, **kwargs) -> Dict[str, Any]:
        """Generate content with specific provider"""
        
        if provider == "gemini":
            return self._generate_with_gemini(prompt, content_type, **kwargs)
        elif provider == "openai":
            return self._generate_with_openai(prompt, content_type, **kwargs)
        else:
            # Fallback to simple processing
            return self._generate_fallback(prompt, content_type, **kwargs)
    
    def _generate_with_gemini(self, prompt: str, content_type: str, **kwargs) -> Dict[str, Any]:
        """Generate content using Gemini API"""
        try:
            # For now, simulate Gemini API response
            # In real implementation, this would call the actual API
            
            processed_content = self._enhance_content(prompt, content_type)
            
            return {
                'success': True,
                'content': processed_content,
                'provider': 'gemini',
                'content_type': content_type,
                'timestamp': datetime.now().isoformat(),
                'processing_time': 0.5
            }
            
        except Exception as e:
            self.logger.error(f"Gemini API error: {e}")
            return self._generate_fallback(prompt, content_type)
    
    def _generate_with_openai(self, prompt: str, content_type: str, **kwargs) -> Dict[str, Any]:
        """Generate content using OpenAI API"""
        try:
            # For now, simulate OpenAI API response
            # In real implementation, this would call the actual API
            
            processed_content = self._enhance_content(prompt, content_type)
            
            return {
                'success': True,
                'content': processed_content,
                'provider': 'openai',
                'content_type': content_type,
                'timestamp': datetime.now().isoformat(),
                'processing_time': 0.3
            }
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            return self._generate_fallback(prompt, content_type)
    
    def _generate_fallback(self, prompt: str, content_type: str, **kwargs) -> Dict[str, Any]:
        """Fallback content generation when APIs are unavailable"""
        try:
            # Simple content enhancement
            processed_content = self._enhance_content(prompt, content_type)
            
            return {
                'success': True,
                'content': processed_content,
                'provider': 'fallback',
                'content_type': content_type,
                'timestamp': datetime.now().isoformat(),
                'processing_time': 0.1,
                'note': 'Generated using fallback method'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'content': prompt
            }
    
    def _enhance_content(self, content: str, content_type: str) -> str:
        """Enhance content with basic processing"""
        try:
            # Clean up the content
            enhanced = content.strip()
            
            # Add content type specific enhancements
            if content_type == "script":
                enhanced = self._enhance_script(enhanced)
            elif content_type == "description":
                enhanced = self._enhance_description(enhanced)
            elif content_type == "prompt":
                enhanced = self._enhance_prompt(enhanced)
            
            return enhanced
            
        except Exception as e:
            self.logger.error(f"Content enhancement error: {e}")
            return content
    
    def _enhance_script(self, script: str) -> str:
        """Enhance video script content"""
        # Basic script formatting
        lines = script.split('\n')
        enhanced_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Ensure proper sentence structure
                if not line.endswith(('.', '!', '?')):
                    line += '.'
                enhanced_lines.append(line)
        
        return '\n'.join(enhanced_lines)
    
    def _enhance_description(self, description: str) -> str:
        """Enhance description content"""
        # Basic description formatting
        description = description.strip()
        
        # Ensure it starts with capital letter
        if description and not description[0].isupper():
            description = description[0].upper() + description[1:]
        
        # Ensure it ends with proper punctuation
        if description and not description.endswith(('.', '!', '?')):
            description += '.'
        
        return description
    
    def _enhance_prompt(self, prompt: str) -> str:
        """Enhance prompt content"""
        # Basic prompt optimization
        prompt = prompt.strip()
        
        # Remove excessive whitespace
        prompt = re.sub(r'\s+', ' ', prompt)
        
        return prompt
    
    def _select_best_provider(self) -> str:
        """Select the best available API provider"""
        # Check if Gemini is available
        if self.api_config.get('gemini', {}).get('api_key'):
            return 'gemini'
        
        # Check if OpenAI is available
        if self.api_config.get('openai', {}).get('api_key'):
            return 'openai'
        
        # Fallback to local processing
        return 'fallback'
    
    def _generate_cache_key(self, prompt: str, content_type: str, provider: str) -> str:
        """Generate cache key for content"""
        content_hash = hashlib.md5(
            f"{prompt}_{content_type}_{provider}".encode('utf-8')
        ).hexdigest()
        return content_hash[:16]
    
    def process_script(self, script: str, enhancement_level: str = "medium") -> Dict[str, Any]:
        """
        Process and enhance video script
        
        Args:
            script: Raw script content
            enhancement_level: Level of enhancement (basic, medium, advanced)
            
        Returns:
            Dict with processed script and analysis
        """
        try:
            # Basic script analysis
            word_count = len(script.split())
            char_count = len(script)
            estimated_duration = word_count / 150  # Assume 150 WPM speaking rate
            
            # Process based on enhancement level
            if enhancement_level == "basic":
                processed_script = self._enhance_script(script)
            elif enhancement_level == "medium":
                processed_script = self.generate_content(
                    script, "script", "auto"
                )['content']
            else:  # advanced
                processed_script = self.generate_content(
                    f"Enhance this video script for maximum engagement: {script}",
                    "script", "auto"
                )['content']
            
            return {
                'success': True,
                'original_script': script,
                'processed_script': processed_script,
                'analysis': {
                    'word_count': word_count,
                    'character_count': char_count,
                    'estimated_duration_minutes': round(estimated_duration, 1),
                    'enhancement_level': enhancement_level
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Script processing error: {e}")
            return {
                'success': False,
                'error': str(e),
                'original_script': script,
                'processed_script': script
            }
    
    def clear_cache(self):
        """Clear the content cache"""
        self.content_cache.clear()
        self.logger.info("Content cache cleared")
    
    def set_api_key(self, provider: str, api_key: str):
        """Set API key for specific provider"""
        try:
            if provider not in ['gemini', 'openai', 'chatgpt']:
                raise ValueError(f"Unsupported provider: {provider}")
            
            # Map chatgpt to openai for consistency
            if provider == 'chatgpt':
                provider = 'openai'
            
            # Initialize provider config if not exists
            if provider not in self.api_config:
                self.api_config[provider] = {}
            
            self.api_config[provider]['api_key'] = api_key
            self.logger.info(f"API key updated for {provider}")
            
            # Re-initialize APIs with new key
            self.initialize_apis()
            
        except Exception as e:
            self.logger.error(f"Error setting API key for {provider}: {e}")
            raise

    def is_provider_available(self, provider: str) -> bool:
        """Check if provider is available and properly configured"""
        try:
            # Map chatgpt to openai for consistency
            if provider == 'chatgpt':
                provider = 'openai'
            
            if provider not in ['gemini', 'openai']:
                return False
            
            # Check if API key is configured
            api_key = self.api_config.get(provider, {}).get('api_key', '').strip()
            if not api_key:
                return False
            
            # Provider is available if API key exists
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking provider availability: {e}")
            return False

    def generate_video_prompts(self, script: str, provider: str = "auto", 
                             style: str = "cinematic", **kwargs) -> Dict[str, Any]:
        """Generate video prompts from script with proper duration-based prompt count"""
        try:
            if not script or not script.strip():
                return {
                    'status': 'error',
                    'error_message': 'Empty script provided'
                }
            
            # Extract video duration from kwargs
            video_duration = kwargs.get('video_duration', 48)  # Default 48s (6 prompts)
            
            self.logger.info(f"Generating prompts for {video_duration}s video")
            
            # Map chatgpt to openai for consistency
            if provider == 'chatgpt':
                provider = 'openai'
            
            # Auto-select provider if needed
            if provider == "auto":
                provider = self._select_best_provider()
            
            # Check provider availability
            if not self.is_provider_available(provider):
                return {
                    'status': 'error',
                    'error_message': f'Provider {provider} not available or not configured'
                }
            
            # 🎯 USE REAL GEMINI API IF AVAILABLE FOR BETTER PROMPTS
            if provider == 'gemini' and self.is_provider_available('gemini'):
                video_prompt = self._generate_with_gemini_api(script, style, video_duration)
            else:
                # Generate enhanced prompt for video creation with duration
                video_prompt = self._create_video_prompt(script, style, provider, video_duration)
            
            return {
                'status': 'success',
                'video_prompts': video_prompt,
                'provider': provider,
                'style': style,
                'video_duration': video_duration,
                'prompts_count': video_duration // 8,  # Each prompt = 8s
                'original_script': script
            }
            
        except Exception as e:
            self.logger.error(f"Error generating video prompts: {e}")
            return {
                'status': 'error',
                'error_message': str(e)
            }

    def enhance_script(self, script: str, enhancement_level: str = "medium", 
                      provider: str = "auto", **kwargs) -> Dict[str, Any]:
        """Enhanced script processing with AI"""
        try:
            if not script or not script.strip():
                return {
                    'status': 'error',
                    'error_message': 'Empty script provided',
                    'enhanced_script': script
                }
            
            # Use existing process_script method as base
            result = self.process_script(script, enhancement_level)
            
            # Check if processing was successful
            if not result.get('success', False):
                return {
                    'status': 'error',
                    'error_message': result.get('error', 'Script processing failed'),
                    'enhanced_script': script,
                    'original_script': script
                }
            
            # Return in expected format for main_window.py
            return {
                'status': 'success',
                'enhanced_script': result.get('processed_script', script),
                'original_script': script,
                'provider': provider if provider != "auto" else self._select_best_provider(),
                'enhancement_level': enhancement_level
            }
            
        except Exception as e:
            self.logger.error(f"Error enhancing script: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'enhanced_script': script
            }

    def _create_video_prompt(self, script: str, style: str, provider: str, video_duration: int = 48) -> str:
        """Create video prompt from script with proper prompt count based on duration"""
        try:
            # 🎯 CALCULATE PROMPTS NEEDED BASED ON VIDEO DURATION
            # Each prompt = 8 seconds, max 60 prompts (8 minutes)
            prompts_needed = max(1, min(60, video_duration // 8))
            actual_duration = prompts_needed * 8
            
            self.logger.info(f"🎬 Creating {prompts_needed} prompts for {video_duration}s video (actual: {actual_duration}s)")
            
            # Split script into meaningful segments
            sentences = []
            
            # Split by sentences (periods, exclamation marks, question marks)
            import re
            raw_sentences = re.split(r'[.!?]+', script.strip())
            
            for sentence in raw_sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > 15:  # Only substantial content
                    # Clean up sentence
                    sentence = sentence.replace('\n', ' ')
                    sentence = re.sub(r'\s+', ' ', sentence)
                    if not sentence.endswith(('.', '!', '?')):
                        sentence += '.'
                    sentences.append(sentence)
            
            # If we need more prompts than sentences, split longer sentences
            while len(sentences) < prompts_needed and sentences:
                new_sentences = []
                for sentence in sentences:
                    words = sentence.split()
                    if len(words) > 15:  # Split long sentences
                        mid_point = len(words) // 2
                        chunk1 = ' '.join(words[:mid_point])
                        chunk2 = ' '.join(words[mid_point:])
                        
                        if not chunk1.endswith(('.', '!', '?')):
                            chunk1 += '.'
                        if not chunk2.endswith(('.', '!', '?')):
                            chunk2 += '.'
                            
                        new_sentences.extend([chunk1, chunk2])
                    else:
                        new_sentences.append(sentence)
                
                if len(new_sentences) <= len(sentences):  # No more splitting possible
                    break
                sentences = new_sentences
            
            # Create prompts in proper format
            prompt_parts = []
            
            # Add header with duration info
            prompt_parts.append(f"# Generated Video Prompts - {video_duration}s ({prompts_needed} prompts)")
            prompt_parts.append("")
            
            # Generate exactly the number of prompts needed
            for i in range(1, prompts_needed + 1):
                if i <= len(sentences):
                    sentence = sentences[i-1]
                else:
                    # If we run out of sentences, cycle through existing ones with variations
                    base_sentence = sentences[(i-1) % len(sentences)]
                    sentence = f"Continue with: {base_sentence}"
                
                # Add cinematic elements based on position
                if style.lower() == "cinematic":
                    if i == 1:
                        enhanced_prompt = f"Cinematic opening shot: {sentence}"
                    elif i == prompts_needed:
                        enhanced_prompt = f"Dramatic conclusion: {sentence}"
                    elif i <= prompts_needed // 3:
                        enhanced_prompt = f"Establishing scene: {sentence}"
                    elif i >= prompts_needed * 2 // 3:
                        enhanced_prompt = f"Climactic scene: {sentence}"
                    else:
                        enhanced_prompt = f"Cinematic scene: {sentence}"
                else:
                    enhanced_prompt = sentence
                
                prompt_parts.append(f"PROMPT {i}: {enhanced_prompt}")
            
            return '\n'.join(prompt_parts)
            
        except Exception as e:
            self.logger.error(f"Error creating video prompt: {e}")
            return f"PROMPT 1: Create a video based on: {script}"

    def _generate_with_gemini_api(self, script: str, style: str, video_duration: int) -> str:
        """Generate prompts using real Gemini API if available"""
        try:
            # Try to import and use real Gemini handler
            from api.gemini_handler import GeminiClient
            
            gemini_config = self.api_config.get('gemini', {})
            if not gemini_config.get('api_key'):
                self.logger.warning("Gemini API key not configured, falling back to basic generation")
                return self._create_video_prompt(script, style, 'gemini', video_duration)
            
            # Initialize Gemini client
            client = GeminiClient(gemini_config)
            
            # Use the sophisticated prompt generation method
            result = client.generate_prompts_for_video_ai(script, video_duration)
            
            if result.get('status') == 'success':
                prompts_text = result.get('response', '')
                
                if prompts_text and 'PROMPT' in prompts_text:
                    self.logger.info(f"✅ Generated prompts using real Gemini API for {video_duration}s video")
                    return prompts_text
                else:
                    self.logger.warning("Gemini API returned empty/invalid prompts, falling back")
            
            # Fallback to basic generation if API fails
            return self._create_video_prompt(script, style, 'gemini', video_duration)
            
        except ImportError:
            self.logger.info("Gemini handler not available, using basic generation")
            return self._create_video_prompt(script, style, 'gemini', video_duration)
        except Exception as e:
            self.logger.error(f"Error with Gemini API: {e}, falling back to basic generation")
            return self._create_video_prompt(script, style, 'gemini', video_duration)

    def get_stats(self) -> Dict[str, Any]:
        """Get content generator statistics"""
        return {
            'cache_size': len(self.content_cache),
            'cache_max_size': self.cache_max_size,
            'apis_configured': {
                'gemini': bool(self.api_config.get('gemini', {}).get('api_key')),
                'openai': bool(self.api_config.get('openai', {}).get('api_key'))
            },
            'best_provider': self._select_best_provider()
        }


# Convenience function for backward compatibility
def create_content_generator(api_config: Dict[str, Any] = None) -> ContentGenerator:
    """Create a new ContentGenerator instance"""
    return ContentGenerator(api_config) 