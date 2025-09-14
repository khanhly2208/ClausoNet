#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Scene Analyzer
Phân tích và xử lý scenes từ script
"""

import logging
import sys
import os
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.script_parser import Scene

class SceneAnalyzer:
    """Phân tích scenes cho video generation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('SceneAnalyzer')
    
    async def analyze_scenes(self, scenes: List[Scene], style: str = "cinematic") -> List[Dict[str, Any]]:
        """Phân tích và chuẩn bị scenes cho video generation"""
        analyzed_scenes = []
        
        for i, scene in enumerate(scenes):
            analyzed_scene = {
                'scene_number': i + 1,
                'timestamp': scene.timestamp,
                'location': scene.location,
                'description': scene.description,
                'camera': scene.camera or "Medium shot",
                'audio': scene.audio or "Ambient sound",
                'emotion': scene.emotion or "Neutral",
                'characters': scene.characters or [],
                'props': scene.props or [],
                'effects': scene.effects or [],
                'style': style,
                'prompt': self._generate_prompt(scene, style)
            }
            
            analyzed_scenes.append(analyzed_scene)
            self.logger.info(f"Analyzed scene {i+1}: {scene.location}")
        
        return analyzed_scenes
    
    def _generate_prompt(self, scene: Scene, style: str) -> str:
        """Tạo prompt cho API từ scene data"""
        prompt_parts = []
        
        # Base description
        prompt_parts.append(f"Location: {scene.location}")
        prompt_parts.append(f"Description: {scene.description}")
        
        # Camera and style
        if scene.camera:
            prompt_parts.append(f"Camera: {scene.camera}")
        prompt_parts.append(f"Style: {style}")
        
        # Characters and props
        if scene.characters:
            prompt_parts.append(f"Characters: {', '.join(scene.characters)}")
        if scene.props:
            prompt_parts.append(f"Props: {', '.join(scene.props)}")
        
        # Emotion and effects
        if scene.emotion:
            prompt_parts.append(f"Mood: {scene.emotion}")
        if scene.effects:
            prompt_parts.append(f"Effects: {', '.join(scene.effects)}")
        
        return ". ".join(prompt_parts) 