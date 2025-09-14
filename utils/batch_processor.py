#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Batch Video Processor
Xử lý nhiều kịch bản video cùng lúc với cấu hình batch
"""

import os
import sys
import json
import time
import asyncio
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil

class BatchProcessor:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
        self.batch_results = {}
        self.active_jobs = {}

        # Batch settings
        self.max_concurrent_jobs = self.config.get('processing', {}).get('max_concurrent_scenes', 4)
        self.output_dir = Path(self.config.get('processing', {}).get('output_directory', './output/'))
        self.temp_dir = Path(self.config.get('processing', {}).get('temp_directory', './temp/'))

        # Tạo thư mục cần thiết
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        os.makedirs('logs', exist_ok=True)

        self.setup_logging()

    def setup_logging(self):
        """Thiết lập logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/batch_processing.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('BatchProcessor')

    def load_config(self) -> Dict[str, Any]:
        """Đọc cấu hình từ config.yaml"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            self.logger.error(f"Config file not found: {self.config_path}")
            return self.get_default_config()
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Trả về cấu hình mặc định"""
        return {
            'processing': {
                'max_concurrent_scenes': 4,
                'output_directory': './output/',
                'temp_directory': './temp/'
            },
            'video': {
                'default_resolution': '1080p',
                'frame_rate': 30,
                'codec': 'h264'
            }
        }

    def load_batch_config(self, batch_config_path: str) -> Dict[str, Any]:
        """Đọc cấu hình batch"""
        try:
            with open(batch_config_path, 'r', encoding='utf-8') as f:
                if batch_config_path.endswith('.json'):
                    batch_config = json.load(f)
                else:
                    batch_config = yaml.safe_load(f)

            # Validate batch config
            required_fields = ['batch_id', 'scripts']
            for field in required_fields:
                if field not in batch_config:
                    raise ValueError(f"Missing required field: {field}")

            return batch_config

        except Exception as e:
            self.logger.error(f"Failed to load batch config: {e}")
            raise

    def validate_script_files(self, script_paths: List[str]) -> List[str]:
        """Kiểm tra và xác thực các file script"""
        valid_scripts = []

        for script_path in script_paths:
            if not os.path.exists(script_path):
                self.logger.warning(f"Script file not found: {script_path}")
                continue

            # Check file extension
            if not script_path.lower().endswith(('.txt', '.md', '.script')):
                self.logger.warning(f"Unsupported script format: {script_path}")
                continue

            # Check file size (max 10MB)
            file_size = os.path.getsize(script_path)
            if file_size > 10 * 1024 * 1024:
                self.logger.warning(f"Script file too large: {script_path} ({file_size} bytes)")
                continue

            valid_scripts.append(script_path)

        return valid_scripts

    def parse_script_file(self, script_path: str) -> Dict[str, Any]:
        """Phân tích file script"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Basic script parsing
            script_info = {
                'title': 'Untitled',
                'duration': 60,
                'scenes': [],
                'metadata': {}
            }

            lines = content.split('\n')
            current_section = None
            current_scene = {}

            for line in lines:
                line = line.strip()

                if line.startswith('TITLE:'):
                    script_info['title'] = line.replace('TITLE:', '').strip()
                elif line.startswith('DURATION:'):
                    duration_str = line.replace('DURATION:', '').strip()
                    # Parse duration (support formats like "120s", "2:00", "2 minutes")
                    script_info['duration'] = self.parse_duration(duration_str)
                elif line.startswith('SCENE'):
                    if current_scene:
                        script_info['scenes'].append(current_scene)
                    current_scene = {'scene_number': len(script_info['scenes']) + 1}
                elif line.startswith('DESCRIPTION:'):
                    current_scene['description'] = line.replace('DESCRIPTION:', '').strip()
                elif line.startswith('TIMESTAMP:'):
                    current_scene['timestamp'] = line.replace('TIMESTAMP:', '').strip()

            # Add last scene
            if current_scene:
                script_info['scenes'].append(current_scene)

            return script_info

        except Exception as e:
            self.logger.error(f"Failed to parse script {script_path}: {e}")
            raise

    def parse_duration(self, duration_str: str) -> int:
        """Phân tích chuỗi thời lượng thành giây"""
        duration_str = duration_str.lower().strip()

        if 's' in duration_str:
            return int(duration_str.replace('s', ''))
        elif ':' in duration_str:
            parts = duration_str.split(':')
            if len(parts) == 2:
                minutes, seconds = parts
                return int(minutes) * 60 + int(seconds)
        elif 'minute' in duration_str:
            return int(duration_str.replace('minutes', '').replace('minute', '').strip()) * 60

        # Default fallback
        try:
            return int(duration_str)
        except:
            return 60

    def create_job(self, script_path: str, job_settings: Dict[str, Any], batch_id: str) -> Dict[str, Any]:
        """Tạo job xử lý video từ script"""
        script_info = self.parse_script_file(script_path)

        job_id = f"{batch_id}_{os.path.splitext(os.path.basename(script_path))[0]}_{int(time.time())}"

        job = {
            'job_id': job_id,
            'batch_id': batch_id,
            'script_path': script_path,
            'script_info': script_info,
            'settings': job_settings,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'started_at': None,
            'completed_at': None,
            'progress': 0,
            'output_file': None,
            'error_message': None,
            'processing_time': 0
        }

        return job

    def process_single_video(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Xử lý một video đơn lẻ"""
        job_id = job['job_id']
        self.logger.info(f"Starting job: {job_id}")

        try:
            job['status'] = 'processing'
            job['started_at'] = datetime.utcnow().isoformat()
            start_time = time.time()

            # Simulate video generation process
            # Trong thực tế, đây sẽ là nơi gọi ClausoNet engine
            script_info = job['script_info']
            settings = job['settings']

            total_scenes = len(script_info['scenes'])

            for i, scene in enumerate(script_info['scenes']):
                # Simulate scene processing
                self.logger.info(f"Processing scene {i+1}/{total_scenes} for job {job_id}")

                # Update progress
                job['progress'] = int((i + 1) / total_scenes * 100)

                # Simulate processing time (2-5 seconds per scene)
                import random
                processing_time = random.uniform(2, 5)
                time.sleep(processing_time)

                # Check if job was cancelled
                if job.get('cancelled', False):
                    job['status'] = 'cancelled'
                    return job

            # Generate output filename
            output_filename = f"{job['batch_id']}_{script_info['title'].replace(' ', '_')}_{int(time.time())}.mp4"
            output_path = self.output_dir / output_filename

            # Simulate final video creation
            self.logger.info(f"Finalizing video for job {job_id}")
            time.sleep(2)

            # Create dummy output file
            with open(output_path, 'w') as f:
                f.write(f"# Simulated video output for {job_id}\n")
                f.write(f"# Script: {job['script_path']}\n")
                f.write(f"# Title: {script_info['title']}\n")
                f.write(f"# Duration: {script_info['duration']} seconds\n")
                f.write(f"# Scenes: {total_scenes}\n")

            # Complete job
            job['status'] = 'completed'
            job['progress'] = 100
            job['completed_at'] = datetime.utcnow().isoformat()
            job['processing_time'] = time.time() - start_time
            job['output_file'] = str(output_path)

            self.logger.info(f"Job completed: {job_id} -> {output_filename}")

        except Exception as e:
            job['status'] = 'failed'
            job['error_message'] = str(e)
            job['completed_at'] = datetime.utcnow().isoformat()
            job['processing_time'] = time.time() - start_time if 'started_at' in job else 0

            self.logger.error(f"Job failed: {job_id} - {e}")

        return job

    def run_batch_processing(self, batch_config_path: str) -> Dict[str, Any]:
        """Chạy batch processing"""
        self.logger.info(f"Starting batch processing: {batch_config_path}")

        try:
            # Load batch configuration
            batch_config = self.load_batch_config(batch_config_path)
            batch_id = batch_config['batch_id']

            # Validate script files
            script_paths = batch_config['scripts']
            valid_scripts = self.validate_script_files(script_paths)

            if not valid_scripts:
                raise ValueError("No valid script files found")

            self.logger.info(f"Processing {len(valid_scripts)} scripts")

            # Create jobs
            job_settings = batch_config.get('settings', {})
            jobs = []

            for script_path in valid_scripts:
                job = self.create_job(script_path, job_settings, batch_id)
                jobs.append(job)

            # Process jobs concurrently
            batch_start_time = time.time()
            completed_jobs = []

            with ThreadPoolExecutor(max_workers=self.max_concurrent_jobs) as executor:
                # Submit jobs
                future_to_job = {
                    executor.submit(self.process_single_video, job): job
                    for job in jobs
                }

                # Collect results
                for future in as_completed(future_to_job):
                    job = future_to_job[future]
                    try:
                        completed_job = future.result()
                        completed_jobs.append(completed_job)
                    except Exception as e:
                        self.logger.error(f"Job execution failed: {job['job_id']} - {e}")
                        job['status'] = 'failed'
                        job['error_message'] = str(e)
                        completed_jobs.append(job)

            # Generate batch results
            batch_results = {
                'batch_id': batch_id,
                'started_at': datetime.utcnow().isoformat(),
                'completed_at': datetime.utcnow().isoformat(),
                'total_processing_time': time.time() - batch_start_time,
                'total_scripts': len(valid_scripts),
                'jobs': completed_jobs,
                'statistics': self.calculate_batch_statistics(completed_jobs)
            }

            # Save batch results
            results_file = self.output_dir / f"{batch_id}_results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(batch_results, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Batch processing completed: {batch_id}")
            return batch_results

        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            raise

    def calculate_batch_statistics(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tính toán thống kê batch"""
        total_jobs = len(jobs)
        completed_jobs = len([j for j in jobs if j['status'] == 'completed'])
        failed_jobs = len([j for j in jobs if j['status'] == 'failed'])
        cancelled_jobs = len([j for j in jobs if j['status'] == 'cancelled'])

        processing_times = [j['processing_time'] for j in jobs if j['processing_time'] > 0]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0

        total_scenes = sum([len(j['script_info']['scenes']) for j in jobs])
        total_duration = sum([j['script_info']['duration'] for j in jobs])

        return {
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'cancelled_jobs': cancelled_jobs,
            'success_rate': round((completed_jobs / total_jobs) * 100, 1) if total_jobs > 0 else 0,
            'average_processing_time': round(avg_processing_time, 2),
            'total_scenes_processed': total_scenes,
            'total_video_duration': total_duration
        }

    def create_batch_config_template(self, output_path: str) -> None:
        """Tạo template cấu hình batch"""
        template = {
            "batch_id": "example_batch_001",
            "description": "Example batch processing configuration",
            "scripts": [
                "scripts/episode_01.txt",
                "scripts/episode_02.txt",
                "scripts/episode_03.txt"
            ],
            "settings": {
                "resolution": "1080p",
                "style": "cinematic",
                "api_preference": ["gemini", "veo3"],
                "quality": "high",
                "custom_template": None
            },
            "output": {
                "format": "mp4",
                "codec": "h264",
                "naming_pattern": "{batch_id}_{script_title}_{timestamp}",
                "create_thumbnails": True,
                "create_preview": True
            },
            "processing": {
                "max_concurrent": 4,
                "retry_failed": True,
                "continue_on_error": True,
                "cleanup_temp": True
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Batch config template created: {output_path}")

    def monitor_batch_progress(self, batch_id: str) -> Dict[str, Any]:
        """Theo dõi tiến trình batch"""
        # Trong implementation thực tế, sẽ đọc từ database hoặc cache
        return {
            'batch_id': batch_id,
            'status': 'processing',
            'progress': 45,
            'completed_jobs': 2,
            'total_jobs': 5,
            'current_job': 'episode_03_processing',
            'estimated_time_remaining': 300  # seconds
        }

    def cancel_batch(self, batch_id: str) -> bool:
        """Hủy batch processing"""
        try:
            # Mark all pending jobs as cancelled
            # Trong implementation thực tế, sẽ signal các worker threads
            self.logger.info(f"Cancelling batch: {batch_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cancel batch {batch_id}: {e}")
            return False

    def generate_batch_report(self, batch_results: Dict[str, Any], format: str = 'text') -> str:
        """Tạo báo cáo batch processing"""
        if format == 'json':
            return json.dumps(batch_results, indent=2, ensure_ascii=False)

        # Text format report
        report = []
        report.append("=" * 60)
        report.append("ClausoNet 4.0 Pro - Batch Processing Report")
        report.append("=" * 60)
        report.append(f"Batch ID: {batch_results['batch_id']}")
        report.append(f"Completed: {batch_results['completed_at']}")
        report.append(f"Total Processing Time: {batch_results['total_processing_time']:.2f} seconds")
        report.append("")

        # Statistics
        stats = batch_results['statistics']
        report.append("STATISTICS:")
        report.append("-" * 30)
        report.append(f"  Total Scripts: {stats['total_jobs']}")
        report.append(f"  Completed: {stats['completed_jobs']}")
        report.append(f"  Failed: {stats['failed_jobs']}")
        report.append(f"  Success Rate: {stats['success_rate']}%")
        report.append(f"  Average Processing Time: {stats['average_processing_time']:.2f}s")
        report.append(f"  Total Scenes: {stats['total_scenes_processed']}")
        report.append(f"  Total Duration: {stats['total_video_duration']}s")
        report.append("")

        # Job Details
        report.append("JOB DETAILS:")
        report.append("-" * 30)

        for job in batch_results['jobs']:
            status_icon = {
                'completed': '✓',
                'failed': '✗',
                'cancelled': '○'
            }.get(job['status'], '?')

            script_name = os.path.basename(job['script_path'])
            report.append(f"{status_icon} {script_name}")
            report.append(f"    Title: {job['script_info']['title']}")
            report.append(f"    Status: {job['status'].upper()}")
            report.append(f"    Processing Time: {job['processing_time']:.2f}s")

            if job['status'] == 'completed' and job['output_file']:
                report.append(f"    Output: {os.path.basename(job['output_file'])}")
            elif job['status'] == 'failed' and job['error_message']:
                report.append(f"    Error: {job['error_message']}")

            report.append("")

        report.append("=" * 60)
        return "\n".join(report)

def main():
    """Hàm main để chạy từ command line"""
    import argparse

    parser = argparse.ArgumentParser(description='ClausoNet 4.0 Pro Batch Processor')
    parser.add_argument('--batch-config', '-b', required=True,
                       help='Path to batch configuration file (JSON/YAML)')
    parser.add_argument('--config', '-c', default='config.yaml',
                       help='Path to main config file (default: config.yaml)')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='Report output format (default: text)')
    parser.add_argument('--output', '-o', help='Output report file path')
    parser.add_argument('--create-template', metavar='PATH',
                       help='Create batch config template at specified path')
    parser.add_argument('--monitor', metavar='BATCH_ID',
                       help='Monitor progress of existing batch')
    parser.add_argument('--cancel', metavar='BATCH_ID',
                       help='Cancel running batch')

    args = parser.parse_args()

    processor = BatchProcessor(args.config)

    # Create template
    if args.create_template:
        processor.create_batch_config_template(args.create_template)
        print(f"Batch config template created: {args.create_template}")
        return

    # Monitor batch
    if args.monitor:
        progress = processor.monitor_batch_progress(args.monitor)
        print(json.dumps(progress, indent=2))
        return

    # Cancel batch
    if args.cancel:
        success = processor.cancel_batch(args.cancel)
        if success:
            print(f"Batch cancelled: {args.cancel}")
            sys.exit(0)
        else:
            print(f"Failed to cancel batch: {args.cancel}")
            sys.exit(1)

    # Run batch processing
    print("ClausoNet 4.0 Pro - Batch Video Processor")
    print(f"Processing batch configuration: {args.batch_config}")
    print("")

    try:
        results = processor.run_batch_processing(args.batch_config)

        # Generate report
        report = processor.generate_batch_report(results, args.format)

        # Output report
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"Report saved to: {args.output}")
        else:
            print(report)

        # Exit code based on success rate
        success_rate = results['statistics']['success_rate']
        if success_rate == 100:
            sys.exit(0)  # All successful
        elif success_rate >= 50:
            sys.exit(1)  # Partial success
        else:
            sys.exit(2)  # Mostly failed

    except Exception as e:
        print(f"Batch processing failed: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()
