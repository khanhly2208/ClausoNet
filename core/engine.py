"""
ClausoNet 4.0 Pro - AI Processing Engine
Core module for orchestrating video generation
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json
import time

# Add parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scene_analyzer import SceneAnalyzer
from core.video_generator import VideoGenerator
from core.license_manager import LicenseManager
from api.google_veo3 import GoogleVeo3Client
from api.gemini_handler import GeminiClient
from api.openai_connector import OpenAIClient
from utils.script_parser import ScriptParser
from utils.encryption import SecurityManager

@dataclass
class ProcessingRequest:
    """Request data structure for video processing"""
    script_content: str
    output_path: str
    resolution: str = "1080p"
    style: str = "cinematic"
    api_preference: List[str] = None
    batch_mode: bool = False
    template_name: Optional[str] = None

@dataclass
class ProcessingResult:
    """Result data structure for video processing"""
    success: bool
    video_path: Optional[str] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0
    scenes_processed: int = 0
    metadata: Dict[str, Any] = None

class AIEngine:
    """Main AI Processing Engine for ClausoNet 4.0 Pro"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        # Initialize core components
        self.license_manager = LicenseManager(self.config)
        self.scene_analyzer = SceneAnalyzer(self.config)
        self.video_generator = VideoGenerator(self.config)
        self.script_parser = ScriptParser()
        self.security_manager = SecurityManager(self.config)
        
        # Initialize API clients
        self.api_clients = self._initialize_api_clients()
        
        # Performance tracking
        self.processing_stats = {
            'total_videos_generated': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0,
            'api_call_count': {}
        }
        
        self.logger.info("ClausoNet 4.0 Pro AI Engine initialized successfully")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        import yaml
        
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            return config
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {e}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('clausonet.engine')
        
        if not logger.handlers:
            handler = logging.FileHandler('logs/engine.log', encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    def _initialize_api_clients(self) -> Dict[str, Any]:
        """Initialize API clients based on configuration"""
        clients = {}
        
        # Google Veo 3
        if self.config['apis']['google_veo3']['enabled']:
            try:
                clients['veo3'] = GoogleVeo3Client(self.config['apis']['google_veo3'])
                self.logger.info("Google Veo 3 client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Google Veo 3: {e}")
        
        # Gemini
        if self.config['apis']['gemini']['enabled']:
            try:
                clients['gemini'] = GeminiClient(self.config['apis']['gemini'])
                self.logger.info("Gemini client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini: {e}")
        
        # OpenAI
        if self.config['apis']['openai']['enabled']:
            try:
                clients['openai'] = OpenAIClient(self.config['apis']['openai'])
                self.logger.info("OpenAI client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI: {e}")
        
        return clients
    
    async def process_video_request(self, request: ProcessingRequest) -> ProcessingResult:
        """
        Main method to process video generation request
        
        Args:
            request: ProcessingRequest object containing all necessary data
            
        Returns:
            ProcessingResult object with generation results
        """
        start_time = time.time()
        
        try:
            # Validate license
            if not self.license_manager.validate_license():
                return ProcessingResult(
                    success=False,
                    error_message="License validation failed"
                )
            
            # Parse script
            self.logger.info("Parsing script content")
            parsed_script = await self.script_parser.parse_script(request.script_content)
            
            if not parsed_script:
                return ProcessingResult(
                    success=False,
                    error_message="Failed to parse script content"
                )
            
            # Analyze scenes
            self.logger.info(f"Analyzing {len(parsed_script.scenes)} scenes")
            analyzed_scenes = await self.scene_analyzer.analyze_scenes(
                parsed_script.scenes,
                style=request.style
            )
            
            # Generate video
            self.logger.info("Starting video generation")
            video_path = await self.video_generator.generate_video(
                scenes=analyzed_scenes,
                output_path=request.output_path,
                resolution=request.resolution,
                api_clients=self.api_clients,
                api_preference=request.api_preference or ['gemini', 'veo3']
            )
            
            processing_time = time.time() - start_time
            
            # Update statistics
            self._update_stats(processing_time, len(analyzed_scenes))
            
            self.logger.info(f"Video generation completed in {processing_time:.2f} seconds")
            
            return ProcessingResult(
                success=True,
                video_path=video_path,
                processing_time=processing_time,
                scenes_processed=len(analyzed_scenes),
                metadata={
                    'script_title': parsed_script.title,
                    'total_duration': parsed_script.duration,
                    'resolution': request.resolution,
                    'style': request.style
                }
            )
            
        except Exception as e:
            self.logger.error(f"Video processing failed: {e}")
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    async def batch_process(self, requests: List[ProcessingRequest]) -> List[ProcessingResult]:
        """
        Process multiple video requests in batch
        
        Args:
            requests: List of ProcessingRequest objects
            
        Returns:
            List of ProcessingResult objects
        """
        self.logger.info(f"Starting batch processing of {len(requests)} requests")
        
        # Process requests with concurrency limit
        max_concurrent = self.config['processing']['max_concurrent_scenes']
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(request):
            async with semaphore:
                return await self.process_video_request(request)
        
        tasks = [process_with_semaphore(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ProcessingResult(
                    success=False,
                    error_message=f"Batch processing error: {str(result)}"
                ))
            else:
                processed_results.append(result)
        
        self.logger.info(f"Batch processing completed. Success rate: {sum(1 for r in processed_results if r.success)}/{len(processed_results)}")
        
        return processed_results
    
    def _update_stats(self, processing_time: float, scenes_count: int):
        """Update processing statistics"""
        self.processing_stats['total_videos_generated'] += 1
        self.processing_stats['total_processing_time'] += processing_time
        
        # Calculate average
        if self.processing_stats['total_videos_generated'] > 0:
            self.processing_stats['average_processing_time'] = (
                self.processing_stats['total_processing_time'] / 
                self.processing_stats['total_videos_generated']
            )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and statistics"""
        return {
            'version': self.config['version'],
            'license_status': self.license_manager.get_license_status(),
            'api_clients_status': {
                name: 'connected' if client else 'disconnected'
                for name, client in self.api_clients.items()
            },
            'processing_stats': self.processing_stats.copy(),
            'system_resources': self._get_system_resources()
        }
    
    def _get_system_resources(self) -> Dict[str, Any]:
        """Get current system resource usage"""
        import psutil
        
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage_percent': psutil.disk_usage('.').percent,
                'gpu_available': self._check_gpu_availability()
            }
        except Exception as e:
            self.logger.error(f"Failed to get system resources: {e}")
            return {}
    
    def _check_gpu_availability(self) -> bool:
        """Check if GPU is available for processing"""
        # GPU support not needed for API-only version
        return False
    
    def shutdown(self):
        """Gracefully shutdown the engine"""
        self.logger.info("Shutting down ClausoNet AI Engine")
        
        # Save statistics
        stats_file = Path('logs/processing_stats.json')
        try:
            with open(stats_file, 'w') as f:
                json.dump(self.processing_stats, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save statistics: {e}")
        
        # Close API connections
        for name, client in self.api_clients.items():
            try:
                if hasattr(client, 'close'):
                    client.close()
            except Exception as e:
                self.logger.error(f"Error closing {name} client: {e}")
        
        self.logger.info("Engine shutdown completed")

# Global engine instance
_engine_instance = None

def get_engine(config_path: str = "config.yaml") -> AIEngine:
    """Get or create global engine instance"""
    global _engine_instance
    
    if _engine_instance is None:
        _engine_instance = AIEngine(config_path)
    
    return _engine_instance

def shutdown_engine():
    """Shutdown global engine instance"""
    global _engine_instance
    
    if _engine_instance is not None:
        _engine_instance.shutdown()
        _engine_instance = None
