#!/usr/bin/env python3
"""
🗺️ VEO SELECTOR MAPPER - Selector Management Tool
Công cụ quản lý và lưu trữ các selectors đã tìm được cho Veo interface
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class VeoSelectorMapper:
    def __init__(self, mapping_file="veo_selectors.json"):
        self.mapping_file = mapping_file
        self.selectors = self.load_selectors()
        
    def load_selectors(self) -> Dict:
        """Load existing selector mappings"""
        if os.path.exists(self.mapping_file):
            try:
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading selectors: {e}")
                return self.get_default_mapping()
        else:
            return self.get_default_mapping()
            
    def get_default_mapping(self) -> Dict:
        """Get default selector mapping structure"""
        return {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "url": "https://labs.google.com/veo",
            "selectors": {
                "model_dropdown": {
                    "primary": [],
                    "fallback": [],
                    "description": "Dropdown để chọn model (Veo 3 Fast, etc.)",
                    "expected_options": ["Veo 3 Fast", "Veo 3 Standard"]
                },
                "type_dropdown": {
                    "primary": [],
                    "fallback": [],
                    "description": "Dropdown để chọn type (Text to Video, Image to Video)",
                    "expected_options": ["Text to Video", "Image to Video"]
                },
                "create_project_button": {
                    "primary": [],
                    "fallback": [],
                    "description": "Button để tạo project mới",
                    "expected_text": ["Create", "New Project", "Start", "Generate"]
                },
                "prompt_input": {
                    "primary": [],
                    "fallback": [],
                    "description": "Input field để nhập prompt",
                    "expected_placeholder": ["Enter prompt", "Describe your video"]
                },
                "upload_button": {
                    "primary": [],
                    "fallback": [],
                    "description": "Button để upload image (for Image to Video)",
                    "expected_text": ["Upload", "Choose Image", "Select Image"]
                }
            }
        }
        
    def add_selector(self, category: str, selector_type: str, selector_data: Dict):
        """Add new selector to mapping"""
        if category not in self.selectors["selectors"]:
            self.selectors["selectors"][category] = {
                "primary": [],
                "fallback": [],
                "description": f"Custom category: {category}"
            }
            
        # Add selector data
        selector_entry = {
            "selector": selector_data.get("selector", ""),
            "method": selector_data.get("method", "xpath"),  # xpath, css, id, class
            "confidence": selector_data.get("confidence", 0.5),
            "tested_date": datetime.now().isoformat(),
            "element_info": {
                "tag": selector_data.get("tag", ""),
                "class": selector_data.get("class", ""),
                "id": selector_data.get("id", ""),
                "text": selector_data.get("text", ""),
                "aria_label": selector_data.get("aria_label", "")
            }
        }
        
        if selector_type == "primary":
            self.selectors["selectors"][category]["primary"].append(selector_entry)
        else:
            self.selectors["selectors"][category]["fallback"].append(selector_entry)
            
        self.selectors["last_updated"] = datetime.now().isoformat()
        
    def remove_selector(self, category: str, selector_type: str, index: int):
        """Remove selector by index"""
        try:
            if selector_type == "primary":
                del self.selectors["selectors"][category]["primary"][index]
            else:
                del self.selectors["selectors"][category]["fallback"][index]
            self.selectors["last_updated"] = datetime.now().isoformat()
            return True
        except (KeyError, IndexError):
            return False
            
    def get_selectors_for_category(self, category: str) -> Dict:
        """Get all selectors for a category"""
        return self.selectors["selectors"].get(category, {})
        
    def get_best_selector(self, category: str) -> Optional[Dict]:
        """Get best selector for a category (highest confidence primary)"""
        category_data = self.get_selectors_for_category(category)
        if not category_data:
            return None
            
        primary_selectors = category_data.get("primary", [])
        if primary_selectors:
            # Sort by confidence and return best
            best = max(primary_selectors, key=lambda x: x.get("confidence", 0))
            return best
            
        # Fallback to fallback selectors
        fallback_selectors = category_data.get("fallback", [])
        if fallback_selectors:
            best = max(fallback_selectors, key=lambda x: x.get("confidence", 0))
            return best
            
        return None
        
    def save_selectors(self):
        """Save selectors to file"""
        try:
            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                json.dump(self.selectors, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error saving selectors: {e}")
            return False
            
    def display_mapping(self):
        """Display current selector mapping"""
        print("\n🗺️ VEO SELECTOR MAPPING")
        print("=" * 60)
        print(f"Version: {self.selectors.get('version', 'Unknown')}")
        print(f"Last Updated: {self.selectors.get('last_updated', 'Unknown')}")
        print(f"URL: {self.selectors.get('url', 'Unknown')}")
        
        for category, data in self.selectors["selectors"].items():
            print(f"\n📋 {category.upper()}")
            print("-" * 40)
            print(f"Description: {data.get('description', 'No description')}")
            
            # Primary selectors
            primary = data.get("primary", [])
            print(f"\n🎯 Primary Selectors ({len(primary)}):")
            for i, sel in enumerate(primary):
                print(f"  [{i}] {sel['selector']}")
                print(f"      Confidence: {sel.get('confidence', 0)}")
                print(f"      Method: {sel.get('method', 'unknown')}")
                if sel.get('element_info', {}).get('text'):
                    print(f"      Text: {sel['element_info']['text'][:50]}")
                    
            # Fallback selectors
            fallback = data.get("fallback", [])
            print(f"\n🔄 Fallback Selectors ({len(fallback)}):")
            for i, sel in enumerate(fallback):
                print(f"  [{i}] {sel['selector']}")
                print(f"      Confidence: {sel.get('confidence', 0)}")
                print(f"      Method: {sel.get('method', 'unknown')}")
                
    def interactive_mapper(self):
        """Interactive mapping management"""
        print("\n🗺️ VEO SELECTOR MAPPER - INTERACTIVE MODE")
        print("=" * 50)
        
        while True:
            print("\n📋 COMMANDS:")
            print("1. 'show' - Show current mapping")
            print("2. 'add <category> <type>' - Add selector (type: primary/fallback)")
            print("3. 'remove <category> <type> <index>' - Remove selector")
            print("4. 'best <category>' - Show best selector for category")
            print("5. 'save' - Save mapping to file")
            print("6. 'load <file>' - Load mapping from file")
            print("7. 'export <file>' - Export mapping to file")
            print("8. 'quit' - Thoát")
            
            command = input("\n🎮 Enter command: ").strip()
            
            if command == 'quit':
                break
            elif command == 'show':
                self.display_mapping()
            elif command.startswith('add '):
                self.handle_add_command(command)
            elif command.startswith('remove '):
                self.handle_remove_command(command)
            elif command.startswith('best '):
                category = command.replace('best ', '')
                best = self.get_best_selector(category)
                if best:
                    print(f"\n🎯 Best selector for {category}:")
                    print(f"Selector: {best['selector']}")
                    print(f"Confidence: {best.get('confidence', 0)}")
                    print(f"Method: {best.get('method', 'unknown')}")
                else:
                    print(f"❌ No selector found for {category}")
            elif command == 'save':
                if self.save_selectors():
                    print("✅ Mapping saved successfully!")
                else:
                    print("❌ Failed to save mapping!")
            elif command.startswith('load '):
                filename = command.replace('load ', '')
                self.mapping_file = filename
                self.selectors = self.load_selectors()
                print(f"✅ Loaded mapping from {filename}")
            elif command.startswith('export '):
                filename = command.replace('export ', '')
                self.export_mapping(filename)
            else:
                print("❌ Unknown command!")
                
    def handle_add_command(self, command):
        """Handle add selector command"""
        parts = command.split()
        if len(parts) < 3:
            print("❌ Usage: add <category> <type>")
            return
            
        category = parts[1]
        selector_type = parts[2]
        
        if selector_type not in ['primary', 'fallback']:
            print("❌ Type must be 'primary' or 'fallback'")
            return
            
        print(f"\n➕ Adding {selector_type} selector for {category}")
        
        # Get selector data
        selector = input("Selector (XPath/CSS): ").strip()
        if not selector:
            print("❌ Selector cannot be empty!")
            return
            
        method = input("Method (xpath/css/id/class) [xpath]: ").strip() or "xpath"
        confidence = input("Confidence (0.0-1.0) [0.5]: ").strip()
        
        try:
            confidence = float(confidence) if confidence else 0.5
        except ValueError:
            confidence = 0.5
            
        # Optional element info
        tag = input("Tag name [optional]: ").strip()
        class_name = input("Class [optional]: ").strip()
        element_id = input("ID [optional]: ").strip()
        text = input("Text content [optional]: ").strip()
        aria_label = input("Aria label [optional]: ").strip()
        
        selector_data = {
            "selector": selector,
            "method": method,
            "confidence": confidence,
            "tag": tag,
            "class": class_name,
            "id": element_id,
            "text": text,
            "aria_label": aria_label
        }
        
        self.add_selector(category, selector_type, selector_data)
        print("✅ Selector added successfully!")
        
    def handle_remove_command(self, command):
        """Handle remove selector command"""
        parts = command.split()
        if len(parts) < 4:
            print("❌ Usage: remove <category> <type> <index>")
            return
            
        category = parts[1]
        selector_type = parts[2]
        
        try:
            index = int(parts[3])
        except ValueError:
            print("❌ Index must be a number!")
            return
            
        if self.remove_selector(category, selector_type, index):
            print("✅ Selector removed successfully!")
        else:
            print("❌ Failed to remove selector!")
            
    def export_mapping(self, filename):
        """Export mapping to file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.selectors, f, indent=2, ensure_ascii=False)
            print(f"✅ Mapping exported to {filename}")
        except Exception as e:
            print(f"❌ Error exporting mapping: {e}")

def main():
    """Main function"""
    print("🗺️ VEO SELECTOR MAPPER")
    print("=" * 40)
    
    # Get mapping file
    mapping_file = input("Mapping file [veo_selectors.json]: ").strip()
    if not mapping_file:
        mapping_file = "veo_selectors.json"
    
    mapper = VeoSelectorMapper(mapping_file)
    
    try:
        mapper.interactive_mapper()
    except KeyboardInterrupt:
        print("\n🛑 Mapping interrupted!")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Save before exit
    if input("\n💾 Save mapping before exit? (y/n): ").lower() == 'y':
        mapper.save_selectors()
        print("✅ Mapping saved!")

if __name__ == "__main__":
    main() 