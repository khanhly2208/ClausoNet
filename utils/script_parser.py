#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Script Parser
Parse kịch bản câu chuyện tiếng Anh thành cấu trúc dữ liệu
"""

import re
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class Scene:
    """Cấu trúc dữ liệu cho một scene"""
    timestamp: str
    location: str
    description: str
    camera: Optional[str] = None
    audio: Optional[str] = None
    emotion: Optional[str] = None
    characters: List[str] = None
    props: List[str] = None
    effects: List[str] = None

@dataclass
class ParsedScript:
    """Cấu trúc dữ liệu cho script đã parse"""
    title: str
    genre: Optional[str] = None
    duration: int = 60
    style: Optional[str] = None
    mood: Optional[str] = None
    scenes: List[Scene] = None

class ScriptParser:
    """Parser cho kịch bản ClausoNet 4.0"""
    
    def __init__(self):
        self.logger = logging.getLogger('ScriptParser')
    
    async def parse_script(self, script_content: str) -> Optional[ParsedScript]:
        """Parse script content thành cấu trúc dữ liệu"""
        try:
            lines = script_content.strip().split('\n')
            
            # Parse metadata
            title = self._extract_field(lines, 'TITLE:', 'Untitled Story')
            genre = self._extract_field(lines, 'GENRE:', None)
            duration_str = self._extract_field(lines, 'DURATION:', '60s')
            duration = int(re.findall(r'\d+', duration_str)[0]) if duration_str else 60
            style = self._extract_field(lines, 'STYLE:', None)
            mood = self._extract_field(lines, 'MOOD:', None)
            
            # Parse scenes
            scenes = self._parse_scenes(script_content)
            
            return ParsedScript(
                title=title,
                genre=genre,
                duration=duration,
                style=style,
                mood=mood,
                scenes=scenes
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse script: {e}")
            return None
    
    def _extract_field(self, lines: List[str], field_name: str, default: Any = None) -> Any:
        """Trích xuất field từ script"""
        for line in lines:
            if line.strip().startswith(field_name):
                return line.split(':', 1)[1].strip()
        return default
    
    def _parse_scenes(self, script_content: str) -> List[Scene]:
        """Parse các scenes từ script"""
        scenes = []
        
        # Tìm các scene blocks
        scene_pattern = r'SCENE \d+:(.*?)(?=SCENE \d+:|CREDITS:|$)'
        scene_matches = re.findall(scene_pattern, script_content, re.DOTALL)
        
        for scene_content in scene_matches:
            scene = self._parse_single_scene(scene_content)
            if scene:
                scenes.append(scene)
        
        return scenes
    
    def _parse_single_scene(self, scene_content: str) -> Optional[Scene]:
        """Parse một scene đơn lẻ"""
        try:
            lines = scene_content.strip().split('\n')
            
            timestamp = self._extract_scene_field(lines, 'TIMESTAMP:', '00:00-00:10')
            location = self._extract_scene_field(lines, 'LOCATION:', 'Unknown Location')
            description = self._extract_scene_field(lines, 'DESCRIPTION:', '')
            camera = self._extract_scene_field(lines, 'CAMERA:', None)
            audio = self._extract_scene_field(lines, 'AUDIO:', None)
            emotion = self._extract_scene_field(lines, 'EMOTION:', None)
            
            # Parse lists
            characters = self._parse_list_field(lines, 'CHARACTERS:')
            props = self._parse_list_field(lines, 'PROPS:')
            effects = self._parse_list_field(lines, 'EFFECTS:')
            
            return Scene(
                timestamp=timestamp,
                location=location,
                description=description,
                camera=camera,
                audio=audio,
                emotion=emotion,
                characters=characters,
                props=props,
                effects=effects
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse scene: {e}")
            return None
    
    def _extract_scene_field(self, lines: List[str], field_name: str, default: Any = None) -> Any:
        """Trích xuất field từ scene"""
        for line in lines:
            if line.strip().startswith(field_name):
                return line.split(':', 1)[1].strip()
        return default
    
    def _parse_list_field(self, lines: List[str], field_name: str) -> List[str]:
        """Parse field dạng list"""
        for line in lines:
            if line.strip().startswith(field_name):
                content = line.split(':', 1)[1].strip()
                if content:
                    # Split by comma and clean up
                    items = [item.strip() for item in content.split(',')]
                    return [item for item in items if item]
        return [] 