#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Template Lister
Liệt kê và quản lý các template video có sẵn
"""

import os
import sys
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

class TemplateLister:
    def __init__(self, templates_dir: str = "data/templates/"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Template categories
        self.template_categories = {
            'cinematic': {
                'description': 'Hollywood-style cinematography with dramatic lighting and camera movements',
                'characteristics': ['Dynamic camera angles', 'Cinematic lighting', 'Epic composition']
            },
            'animated': {
                'description': 'Cartoon and anime-style animations with vibrant colors',
                'characteristics': ['Bright colors', 'Stylized characters', 'Smooth animations']
            },
            'documentary': {
                'description': 'Realistic documentary-style footage with natural lighting',
                'characteristics': ['Natural lighting', 'Realistic scenes', 'Informative style']
            },
            'fantasy': {
                'description': 'Magical and mystical atmosphere with fantasy elements',
                'characteristics': ['Magical effects', 'Fantasy creatures', 'Mystical environments']
            },
            'scifi': {
                'description': 'Futuristic and technological style with sci-fi elements',
                'characteristics': ['Futuristic designs', 'High-tech elements', 'Space/cyber themes']
            },
            'horror': {
                'description': 'Dark and suspenseful atmosphere with horror elements',
                'characteristics': ['Dark atmosphere', 'Suspenseful mood', 'Horror elements']
            },
            'comedy': {
                'description': 'Light-hearted and humorous tone with comedic elements',
                'characteristics': ['Bright colors', 'Funny situations', 'Light mood']
            },
            'nature': {
                'description': 'Natural landscapes and wildlife with realistic environments',
                'characteristics': ['Natural environments', 'Wildlife', 'Realistic nature']
            }
        }

        self.setup_logging()
        self.create_default_templates()

    def setup_logging(self):
        """Thiết lập logging"""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/template_lister.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('TemplateLister')

    def create_default_templates(self):
        """Tạo các template mặc định nếu chưa có"""
        for category, info in self.template_categories.items():
            template_file = self.templates_dir / f"{category}.yaml"

            if not template_file.exists():
                template_data = self.generate_template_data(category, info)
                self.save_template(category, template_data)

    def generate_template_data(self, category: str, info: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo dữ liệu template cho category"""
        base_template = {
            'name': category.title(),
            'category': category,
            'description': info['description'],
            'characteristics': info['characteristics'],
            'version': '1.0',
            'created_date': datetime.now().isoformat(),
            'author': 'ClausoNet 4.0 Pro',
            'settings': {
                'video': {
                    'resolution': '1080p',
                    'frame_rate': 30,
                    'aspect_ratio': '16:9',
                    'codec': 'h264'
                },
                'style': {
                    'primary_style': category,
                    'color_palette': self.get_color_palette(category),
                    'lighting_style': self.get_lighting_style(category),
                    'camera_style': self.get_camera_style(category)
                },
                'api': {
                    'preferred_apis': ['gemini', 'veo3'],
                    'model_settings': self.get_model_settings(category)
                }
            },
            'prompts': {
                'style_modifiers': self.get_style_modifiers(category),
                'scene_templates': self.get_scene_templates(category),
                'transition_styles': self.get_transition_styles(category)
            }
        }

        return base_template

    def get_color_palette(self, category: str) -> List[str]:
        """Lấy color palette cho category"""
        palettes = {
            'cinematic': ['Dark blues', 'Golden highlights', 'Deep shadows', 'Warm oranges'],
            'animated': ['Bright primary colors', 'Vibrant pastels', 'Bold contrasts'],
            'documentary': ['Natural earth tones', 'Realistic colors', 'Balanced saturation'],
            'fantasy': ['Magical purples', 'Mystical blues', 'Golden glows', 'Ethereal whites'],
            'scifi': ['Cool blues', 'Neon greens', 'Metallic grays', 'Electric accents'],
            'horror': ['Deep blacks', 'Blood reds', 'Sickly greens', 'Ominous shadows'],
            'comedy': ['Bright yellows', 'Cheerful pinks', 'Sunny oranges', 'Happy blues'],
            'nature': ['Forest greens', 'Sky blues', 'Earth browns', 'Sunset oranges']
        }
        return palettes.get(category, ['Neutral colors'])

    def get_lighting_style(self, category: str) -> str:
        """Lấy lighting style cho category"""
        lighting = {
            'cinematic': 'Dramatic chiaroscuro lighting with strong contrasts',
            'animated': 'Bright, even lighting with vibrant highlights',
            'documentary': 'Natural lighting with realistic shadows',
            'fantasy': 'Magical glowing effects with soft ambient light',
            'scifi': 'Cool LED lighting with neon accents',
            'horror': 'Dark, moody lighting with harsh shadows',
            'comedy': 'Bright, cheerful lighting with soft shadows',
            'nature': 'Natural sunlight with organic shadows'
        }
        return lighting.get(category, 'Standard lighting')

    def get_camera_style(self, category: str) -> str:
        """Lấy camera style cho category"""
        camera_styles = {
            'cinematic': 'Dynamic camera movements, dramatic angles, smooth tracking shots',
            'animated': 'Smooth camera pans, character-focused framing, energetic movements',
            'documentary': 'Steady handheld style, natural camera movements, observational angles',
            'fantasy': 'Sweeping establishing shots, magical reveals, graceful movements',
            'scifi': 'Futuristic camera angles, high-tech movements, sleek transitions',
            'horror': 'Unsettling angles, sudden movements, claustrophobic framing',
            'comedy': 'Upbeat camera work, reaction shots, bouncy movements',
            'nature': 'Patient observation shots, natural movements, wildlife-friendly angles'
        }
        return camera_styles.get(category, 'Standard camera work')

    def get_model_settings(self, category: str) -> Dict[str, Any]:
        """Lấy model settings cho category"""
        settings = {
            'cinematic': {
                'temperature': 0.7,
                'style_strength': 0.8,
                'creativity': 0.7
            },
            'animated': {
                'temperature': 0.8,
                'style_strength': 0.9,
                'creativity': 0.8
            },
            'documentary': {
                'temperature': 0.5,
                'style_strength': 0.6,
                'creativity': 0.5
            },
            'fantasy': {
                'temperature': 0.8,
                'style_strength': 0.9,
                'creativity': 0.9
            },
            'scifi': {
                'temperature': 0.7,
                'style_strength': 0.8,
                'creativity': 0.8
            },
            'horror': {
                'temperature': 0.6,
                'style_strength': 0.8,
                'creativity': 0.7
            },
            'comedy': {
                'temperature': 0.8,
                'style_strength': 0.7,
                'creativity': 0.8
            },
            'nature': {
                'temperature': 0.6,
                'style_strength': 0.7,
                'creativity': 0.6
            }
        }
        return settings.get(category, {'temperature': 0.7, 'style_strength': 0.7, 'creativity': 0.7})

    def get_style_modifiers(self, category: str) -> List[str]:
        """Lấy style modifiers cho category"""
        modifiers = {
            'cinematic': [
                'in the style of a Hollywood blockbuster',
                'with dramatic lighting and composition',
                'shot with professional cinematography',
                'with epic scale and grandeur'
            ],
            'animated': [
                'in animated cartoon style',
                'with vibrant cartoon colors',
                'like a Disney/Pixar animation',
                'with stylized character design'
            ],
            'documentary': [
                'in realistic documentary style',
                'with natural lighting',
                'shot with observational camera work',
                'with authentic, unposed scenes'
            ],
            'fantasy': [
                'in magical fantasy style',
                'with mystical atmosphere',
                'like a fantasy epic film',
                'with enchanted environments'
            ],
            'scifi': [
                'in futuristic sci-fi style',
                'with high-tech elements',
                'like a science fiction movie',
                'with cyberpunk aesthetics'
            ],
            'horror': [
                'in dark horror style',
                'with suspenseful atmosphere',
                'like a thriller movie',
                'with ominous mood'
            ],
            'comedy': [
                'in light comedy style',
                'with humorous elements',
                'like a feel-good movie',
                'with cheerful atmosphere'
            ],
            'nature': [
                'in natural documentary style',
                'with wildlife photography aesthetics',
                'like National Geographic',
                'with pristine natural environments'
            ]
        }
        return modifiers.get(category, ['in professional video style'])

    def get_scene_templates(self, category: str) -> List[Dict[str, str]]:
        """Lấy scene templates cho category"""
        templates = {
            'cinematic': [
                {
                    'type': 'establishing_shot',
                    'template': 'Wide establishing shot of {location}, dramatic lighting, cinematic composition'
                },
                {
                    'type': 'character_close_up',
                    'template': 'Close-up of {character}, dramatic lighting, shallow depth of field'
                },
                {
                    'type': 'action_sequence',
                    'template': 'Dynamic action scene with {action}, fast-paced cinematography'
                }
            ],
            'animated': [
                {
                    'type': 'character_intro',
                    'template': 'Animated introduction of {character}, bright cartoon style'
                },
                {
                    'type': 'background_scene',
                    'template': 'Colorful animated background of {location}, cartoon art style'
                },
                {
                    'type': 'action_scene',
                    'template': 'Animated action sequence with {action}, vibrant animation'
                }
            ],
            'documentary': [
                {
                    'type': 'interview_setup',
                    'template': 'Documentary interview setup with {person}, natural lighting'
                },
                {
                    'type': 'location_footage',
                    'template': 'Documentary footage of {location}, observational style'
                },
                {
                    'type': 'process_documentation',
                    'template': 'Documentary coverage of {process}, educational style'
                }
            ]
        }

        return templates.get(category, [
            {
                'type': 'general_scene',
                'template': 'Scene showing {description} in {category} style'
            }
        ])

    def get_transition_styles(self, category: str) -> List[str]:
        """Lấy transition styles cho category"""
        transitions = {
            'cinematic': ['Fade to black', 'Cross dissolve', 'Wipe transition', 'Match cut'],
            'animated': ['Bounce transition', 'Cartoon swipe', 'Pop effect', 'Slide transition'],
            'documentary': ['Straight cut', 'Simple fade', 'Crossfade', 'Jump cut'],
            'fantasy': ['Magical sparkle transition', 'Mystical fade', 'Enchanted dissolve'],
            'scifi': ['Digital glitch', 'Hologram transition', 'Cyber wipe', 'Tech dissolve'],
            'horror': ['Dark fade', 'Creepy dissolve', 'Sudden cut', 'Ominous transition'],
            'comedy': ['Bouncy transition', 'Fun wipe', 'Cheerful fade', 'Upbeat cut'],
            'nature': ['Organic fade', 'Natural dissolve', 'Gentle transition', 'Peaceful cut']
        }
        return transitions.get(category, ['Standard fade', 'Simple cut'])

    def save_template(self, name: str, template_data: Dict[str, Any]):
        """Lưu template vào file"""
        template_file = self.templates_dir / f"{name}.yaml"

        try:
            with open(template_file, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, default_flow_style=False, allow_unicode=True, indent=2)

            self.logger.info(f"Template saved: {template_file}")

        except Exception as e:
            self.logger.error(f"Failed to save template {name}: {e}")
            raise

    def load_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Đọc template từ file"""
        template_file = self.templates_dir / f"{name}.yaml"

        if not template_file.exists():
            return None

        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)

            return template_data

        except Exception as e:
            self.logger.error(f"Failed to load template {name}: {e}")
            return None

    def list_templates(self) -> List[Dict[str, Any]]:
        """Liệt kê tất cả templates"""
        templates = []

        for template_file in self.templates_dir.glob("*.yaml"):
            template_name = template_file.stem
            template_data = self.load_template(template_name)

            if template_data:
                template_info = {
                    'name': template_name,
                    'display_name': template_data.get('name', template_name.title()),
                    'category': template_data.get('category', 'unknown'),
                    'description': template_data.get('description', 'No description available'),
                    'version': template_data.get('version', '1.0'),
                    'created_date': template_data.get('created_date', 'Unknown'),
                    'author': template_data.get('author', 'Unknown'),
                    'file_path': str(template_file),
                    'file_size': template_file.stat().st_size,
                    'last_modified': datetime.fromtimestamp(template_file.stat().st_mtime).isoformat()
                }
                templates.append(template_info)

        # Sort by category, then by name
        templates.sort(key=lambda x: (x['category'], x['name']))
        return templates

    def get_template_details(self, name: str) -> Optional[Dict[str, Any]]:
        """Lấy chi tiết đầy đủ của template"""
        template_data = self.load_template(name)

        if not template_data:
            return None

        template_file = self.templates_dir / f"{name}.yaml"

        # Add file information
        template_data['file_info'] = {
            'file_path': str(template_file),
            'file_size': template_file.stat().st_size,
            'last_modified': datetime.fromtimestamp(template_file.stat().st_mtime).isoformat()
        }

        return template_data

    def create_custom_template(self, name: str, base_template: str = None, customizations: Dict[str, Any] = None) -> bool:
        """Tạo template tùy chỉnh"""
        try:
            if base_template:
                # Start with existing template
                template_data = self.load_template(base_template)
                if not template_data:
                    self.logger.error(f"Base template not found: {base_template}")
                    return False
            else:
                # Start with basic template
                template_data = {
                    'name': name.title(),
                    'category': 'custom',
                    'description': 'Custom user template',
                    'version': '1.0',
                    'created_date': datetime.now().isoformat(),
                    'author': 'User',
                    'settings': {
                        'video': {
                            'resolution': '1080p',
                            'frame_rate': 30,
                            'aspect_ratio': '16:9',
                            'codec': 'h264'
                        },
                        'style': {
                            'primary_style': 'custom',
                            'color_palette': ['Default colors'],
                            'lighting_style': 'Standard lighting',
                            'camera_style': 'Standard camera work'
                        },
                        'api': {
                            'preferred_apis': ['gemini'],
                            'model_settings': {
                                'temperature': 0.7,
                                'style_strength': 0.7,
                                'creativity': 0.7
                            }
                        }
                    },
                    'prompts': {
                        'style_modifiers': ['in professional video style'],
                        'scene_templates': [],
                        'transition_styles': ['Standard fade']
                    }
                }

            # Apply customizations
            if customizations:
                self.apply_customizations(template_data, customizations)

            # Save template
            self.save_template(name, template_data)
            self.logger.info(f"Custom template created: {name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create custom template {name}: {e}")
            return False

    def apply_customizations(self, template_data: Dict[str, Any], customizations: Dict[str, Any]):
        """Áp dụng customizations vào template"""
        def update_nested_dict(target: Dict[str, Any], source: Dict[str, Any]):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    update_nested_dict(target[key], value)
                else:
                    target[key] = value

        update_nested_dict(template_data, customizations)

    def delete_template(self, name: str) -> bool:
        """Xóa template"""
        template_file = self.templates_dir / f"{name}.yaml"

        if not template_file.exists():
            self.logger.warning(f"Template not found: {name}")
            return False

        # Prevent deletion of default templates
        if name in self.template_categories:
            self.logger.error(f"Cannot delete default template: {name}")
            return False

        try:
            template_file.unlink()
            self.logger.info(f"Template deleted: {name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete template {name}: {e}")
            return False

    def export_template(self, name: str, export_path: str) -> bool:
        """Export template ra file"""
        template_data = self.load_template(name)

        if not template_data:
            return False

        try:
            export_file = Path(export_path)

            if export_file.suffix.lower() == '.json':
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=2, ensure_ascii=False)
            else:
                with open(export_file, 'w', encoding='utf-8') as f:
                    yaml.dump(template_data, f, default_flow_style=False, allow_unicode=True, indent=2)

            self.logger.info(f"Template exported: {name} -> {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export template {name}: {e}")
            return False

    def import_template(self, import_path: str, name: str = None) -> bool:
        """Import template từ file"""
        try:
            import_file = Path(import_path)

            if not import_file.exists():
                self.logger.error(f"Import file not found: {import_path}")
                return False

            # Load template data
            with open(import_file, 'r', encoding='utf-8') as f:
                if import_file.suffix.lower() == '.json':
                    template_data = json.load(f)
                else:
                    template_data = yaml.safe_load(f)

            # Use provided name or extract from file
            template_name = name or import_file.stem

            # Add import metadata
            template_data['imported_from'] = str(import_file)
            template_data['imported_date'] = datetime.now().isoformat()

            # Save template
            self.save_template(template_name, template_data)
            self.logger.info(f"Template imported: {import_path} -> {template_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to import template from {import_path}: {e}")
            return False

    def generate_template_report(self, format: str = 'text') -> str:
        """Tạo báo cáo templates"""
        templates = self.list_templates()

        if format == 'json':
            return json.dumps(templates, indent=2, ensure_ascii=False)

        # Text format report
        report = []
        report.append("=" * 60)
        report.append("ClausoNet 4.0 Pro - Template Report")
        report.append("=" * 60)
        report.append(f"Total Templates: {len(templates)}")
        report.append("")

        # Group by category
        categories = {}
        for template in templates:
            category = template['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(template)

        for category, category_templates in sorted(categories.items()):
            report.append(f"{category.upper()} TEMPLATES ({len(category_templates)}):")
            report.append("-" * 40)

            for template in category_templates:
                report.append(f"• {template['display_name']}")
                report.append(f"  Name: {template['name']}")
                report.append(f"  Description: {template['description']}")
                report.append(f"  Version: {template['version']}")
                report.append(f"  Author: {template['author']}")
                report.append(f"  Size: {template['file_size']} bytes")
                report.append("")

        report.append("=" * 60)
        return "\n".join(report)

def main():
    """Hàm main để chạy từ command line"""
    import argparse

    parser = argparse.ArgumentParser(description='ClausoNet 4.0 Pro Template Lister')
    parser.add_argument('--list', action='store_true',
                       help='List all available templates')
    parser.add_argument('--details', metavar='TEMPLATE_NAME',
                       help='Show detailed information about a template')
    parser.add_argument('--create', metavar='TEMPLATE_NAME',
                       help='Create a new custom template')
    parser.add_argument('--base', metavar='BASE_TEMPLATE',
                       help='Base template for custom template creation')
    parser.add_argument('--delete', metavar='TEMPLATE_NAME',
                       help='Delete a template')
    parser.add_argument('--export', nargs=2, metavar=('TEMPLATE_NAME', 'EXPORT_PATH'),
                       help='Export template to file')
    parser.add_argument('--import', nargs=2, metavar=('IMPORT_PATH', 'TEMPLATE_NAME'),
                       help='Import template from file')
    parser.add_argument('--report', action='store_true',
                       help='Generate template report')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='Output format')
    parser.add_argument('--templates-dir', default='data/templates/',
                       help='Templates directory path')

    args = parser.parse_args()

    lister = TemplateLister(args.templates_dir)

    try:
        if args.list:
            templates = lister.list_templates()

            if args.format == 'json':
                print(json.dumps(templates, indent=2, ensure_ascii=False))
            else:
                print("Available Templates:")
                print("=" * 40)

                current_category = None
                for template in templates:
                    if template['category'] != current_category:
                        current_category = template['category']
                        print(f"\n{current_category.upper()}:")
                        print("-" * 20)

                    print(f"  {template['name']}: {template['description']}")

        elif args.details:
            details = lister.get_template_details(args.details)

            if details:
                if args.format == 'json':
                    print(json.dumps(details, indent=2, ensure_ascii=False))
                else:
                    print(f"Template: {details['name']}")
                    print("=" * 40)
                    print(f"Category: {details['category']}")
                    print(f"Description: {details['description']}")
                    print(f"Version: {details['version']}")
                    print(f"Author: {details['author']}")
                    print(f"Created: {details['created_date']}")
                    print()
                    print("Settings:")
                    print(yaml.dump(details['settings'], default_flow_style=False, indent=2))
            else:
                print(f"Template not found: {args.details}")
                sys.exit(1)

        elif args.create:
            success = lister.create_custom_template(args.create, args.base)
            if success:
                print(f"✓ Custom template created: {args.create}")
            else:
                print(f"✗ Failed to create template: {args.create}")
                sys.exit(1)

        elif args.delete:
            success = lister.delete_template(args.delete)
            if success:
                print(f"✓ Template deleted: {args.delete}")
            else:
                print(f"✗ Failed to delete template: {args.delete}")
                sys.exit(1)

        elif args.export:
            template_name, export_path = args.export
            success = lister.export_template(template_name, export_path)
            if success:
                print(f"✓ Template exported: {template_name} -> {export_path}")
            else:
                print(f"✗ Failed to export template: {template_name}")
                sys.exit(1)

        elif hasattr(args, 'import') and getattr(args, 'import'):
            import_path, template_name = getattr(args, 'import')
            success = lister.import_template(import_path, template_name)
            if success:
                print(f"✓ Template imported: {import_path} -> {template_name}")
            else:
                print(f"✗ Failed to import template: {import_path}")
                sys.exit(1)

        elif args.report:
            report = lister.generate_template_report(args.format)
            print(report)

        else:
            # Default: show template categories
            print("ClausoNet 4.0 Pro - Template Manager")
            print("=" * 40)
            print("\nAvailable Template Categories:")

            for category, info in lister.template_categories.items():
                print(f"\n{category.upper()}:")
                print(f"  Description: {info['description']}")
                print(f"  Characteristics: {', '.join(info['characteristics'])}")

            print(f"\nTemplates directory: {lister.templates_dir}")
            print("Use --list to see all available templates")
            print("Use --help for more options")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
