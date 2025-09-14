#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Performance Monitor
Giám sát CPU, RAM, GPU, thời gian xử lý cảnh real-time
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import psutil
from collections import deque
import sqlite3

class PerformanceMonitor:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path

        # Monitoring settings
        self.monitoring_active = False
        self.collection_interval = 5  # seconds
        self.max_data_points = 1000
        self.database_path = "logs/performance.db"

        # Data storage
        self.metrics_data = {
            'cpu_usage': deque(maxlen=self.max_data_points),
            'memory_usage': deque(maxlen=self.max_data_points),
            'gpu_usage': deque(maxlen=self.max_data_points),
            'gpu_memory': deque(maxlen=self.max_data_points),
            'disk_io': deque(maxlen=self.max_data_points),
            'network_io': deque(maxlen=self.max_data_points),
            'api_response_times': deque(maxlen=self.max_data_points),
            'scene_generation_times': deque(maxlen=self.max_data_points)
        }

        # Performance thresholds
        self.thresholds = {
            'cpu_warning': 80,
            'cpu_critical': 95,
            'memory_warning': 85,
            'memory_critical': 95,
            'gpu_warning': 85,
            'gpu_critical': 95,
            'response_time_warning': 5000,  # ms
            'response_time_critical': 10000  # ms
        }

        self.setup_logging()
        self.setup_database()

        # GPU monitoring
        self.gpu_available = self.check_gpu_availability()

    def setup_logging(self):
        """Thiết lập logging"""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/performance_monitor.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('PerformanceMonitor')

    def setup_database(self):
        """Thiết lập database SQLite để lưu dữ liệu performance"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    metric_type TEXT,
                    metric_value REAL,
                    additional_data TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    api_name TEXT,
                    response_time REAL,
                    status TEXT,
                    error_message TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scene_processing (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    scene_id TEXT,
                    processing_time REAL,
                    resolution TEXT,
                    api_used TEXT,
                    success BOOLEAN
                )
            ''')

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to setup database: {e}")

    def check_gpu_availability(self) -> bool:
        """Kiểm tra GPU có sẵn không"""
        try:
            import pynvml
            pynvml.nvmlInit()
            return pynvml.nvmlDeviceGetCount() > 0
        except:
            return False

    def collect_cpu_metrics(self) -> Dict[str, Any]:
        """Thu thập metrics CPU"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_freq = psutil.cpu_freq()
            cpu_count = psutil.cpu_count()

            # Per-core usage
            cpu_per_core = psutil.cpu_percent(percpu=True)

            return {
                'timestamp': datetime.now().isoformat(),
                'overall_usage': cpu_percent,
                'frequency_mhz': cpu_freq.current if cpu_freq else 0,
                'core_count': cpu_count,
                'per_core_usage': cpu_per_core,
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
        except Exception as e:
            self.logger.error(f"Failed to collect CPU metrics: {e}")
            return {}

    def collect_memory_metrics(self) -> Dict[str, Any]:
        """Thu thập metrics memory"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return {
                'timestamp': datetime.now().isoformat(),
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'usage_percent': memory.percent,
                'swap_total_gb': round(swap.total / (1024**3), 2) if swap.total > 0 else 0,
                'swap_used_gb': round(swap.used / (1024**3), 2) if swap.total > 0 else 0,
                'swap_percent': swap.percent if swap.total > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Failed to collect memory metrics: {e}")
            return {}

    def collect_gpu_metrics(self) -> Dict[str, Any]:
        """Thu thập metrics GPU"""
        if not self.gpu_available:
            return {}

        try:
            import pynvml

            gpu_count = pynvml.nvmlDeviceGetCount()
            gpus = []

            for i in range(gpu_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)

                # Basic info
                name = pynvml.nvmlDeviceGetName(handle).decode()

                # Memory info
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)

                # Utilization
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)

                # Temperature
                try:
                    temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                except:
                    temperature = 0

                # Power
                try:
                    power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000  # Convert to watts
                except:
                    power_usage = 0

                gpu_data = {
                    'gpu_id': i,
                    'name': name,
                    'memory_total_gb': round(memory_info.total / (1024**3), 2),
                    'memory_used_gb': round(memory_info.used / (1024**3), 2),
                    'memory_free_gb': round(memory_info.free / (1024**3), 2),
                    'memory_usage_percent': round((memory_info.used / memory_info.total) * 100, 1),
                    'gpu_utilization_percent': utilization.gpu,
                    'memory_utilization_percent': utilization.memory,
                    'temperature_c': temperature,
                    'power_usage_w': power_usage
                }

                gpus.append(gpu_data)

            return {
                'timestamp': datetime.now().isoformat(),
                'gpu_count': gpu_count,
                'gpus': gpus
            }

        except Exception as e:
            self.logger.error(f"Failed to collect GPU metrics: {e}")
            return {}

    def collect_disk_metrics(self) -> Dict[str, Any]:
        """Thu thập metrics disk I/O"""
        try:
            disk_io = psutil.disk_io_counters()
            disk_usage = psutil.disk_usage('.')

            return {
                'timestamp': datetime.now().isoformat(),
                'read_bytes': disk_io.read_bytes if disk_io else 0,
                'write_bytes': disk_io.write_bytes if disk_io else 0,
                'read_count': disk_io.read_count if disk_io else 0,
                'write_count': disk_io.write_count if disk_io else 0,
                'disk_total_gb': round(disk_usage.total / (1024**3), 2),
                'disk_used_gb': round(disk_usage.used / (1024**3), 2),
                'disk_free_gb': round(disk_usage.free / (1024**3), 2),
                'disk_usage_percent': round((disk_usage.used / disk_usage.total) * 100, 1)
            }
        except Exception as e:
            self.logger.error(f"Failed to collect disk metrics: {e}")
            return {}

    def collect_network_metrics(self) -> Dict[str, Any]:
        """Thu thập metrics network I/O"""
        try:
            network_io = psutil.net_io_counters()

            return {
                'timestamp': datetime.now().isoformat(),
                'bytes_sent': network_io.bytes_sent if network_io else 0,
                'bytes_recv': network_io.bytes_recv if network_io else 0,
                'packets_sent': network_io.packets_sent if network_io else 0,
                'packets_recv': network_io.packets_recv if network_io else 0,
                'errors_in': network_io.errin if network_io else 0,
                'errors_out': network_io.errout if network_io else 0
            }
        except Exception as e:
            self.logger.error(f"Failed to collect network metrics: {e}")
            return {}

    def collect_all_metrics(self) -> Dict[str, Any]:
        """Thu thập tất cả metrics"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': self.collect_cpu_metrics(),
            'memory': self.collect_memory_metrics(),
            'gpu': self.collect_gpu_metrics(),
            'disk': self.collect_disk_metrics(),
            'network': self.collect_network_metrics()
        }

    def store_metrics_to_db(self, metrics: Dict[str, Any]):
        """Lưu metrics vào database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            timestamp = metrics['timestamp']

            # Store CPU metrics
            if 'cpu' in metrics and metrics['cpu']:
                cursor.execute(
                    "INSERT INTO performance_metrics (timestamp, metric_type, metric_value, additional_data) VALUES (?, ?, ?, ?)",
                    (timestamp, 'cpu_usage', metrics['cpu'].get('overall_usage', 0), json.dumps(metrics['cpu']))
                )

            # Store Memory metrics
            if 'memory' in metrics and metrics['memory']:
                cursor.execute(
                    "INSERT INTO performance_metrics (timestamp, metric_type, metric_value, additional_data) VALUES (?, ?, ?, ?)",
                    (timestamp, 'memory_usage', metrics['memory'].get('usage_percent', 0), json.dumps(metrics['memory']))
                )

            # Store GPU metrics
            if 'gpu' in metrics and metrics['gpu'] and metrics['gpu'].get('gpus'):
                for gpu in metrics['gpu']['gpus']:
                    cursor.execute(
                        "INSERT INTO performance_metrics (timestamp, metric_type, metric_value, additional_data) VALUES (?, ?, ?, ?)",
                        (timestamp, f'gpu_{gpu["gpu_id"]}_usage', gpu.get('gpu_utilization_percent', 0), json.dumps(gpu))
                    )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to store metrics to database: {e}")

    def start_monitoring(self):
        """Bắt đầu monitoring"""
        if self.monitoring_active:
            self.logger.warning("Monitoring already active")
            return

        self.monitoring_active = True
        self.logger.info("Starting performance monitoring...")

        def monitoring_loop():
            while self.monitoring_active:
                try:
                    # Collect metrics
                    metrics = self.collect_all_metrics()

                    # Store in memory
                    self.metrics_data['cpu_usage'].append({
                        'timestamp': metrics['timestamp'],
                        'value': metrics['cpu'].get('overall_usage', 0) if metrics['cpu'] else 0
                    })

                    self.metrics_data['memory_usage'].append({
                        'timestamp': metrics['timestamp'],
                        'value': metrics['memory'].get('usage_percent', 0) if metrics['memory'] else 0
                    })

                    if metrics['gpu'] and metrics['gpu'].get('gpus'):
                        primary_gpu = metrics['gpu']['gpus'][0]
                        self.metrics_data['gpu_usage'].append({
                            'timestamp': metrics['timestamp'],
                            'value': primary_gpu.get('gpu_utilization_percent', 0)
                        })
                        self.metrics_data['gpu_memory'].append({
                            'timestamp': metrics['timestamp'],
                            'value': primary_gpu.get('memory_usage_percent', 0)
                        })

                    # Store to database
                    self.store_metrics_to_db(metrics)

                    # Check thresholds and alert if necessary
                    self.check_performance_thresholds(metrics)

                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")

                time.sleep(self.collection_interval)

        # Start monitoring in background thread
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()

    def stop_monitoring(self):
        """Dừng monitoring"""
        if not self.monitoring_active:
            return

        self.monitoring_active = False
        self.logger.info("Stopping performance monitoring...")

        if hasattr(self, 'monitoring_thread'):
            self.monitoring_thread.join(timeout=10)

    def check_performance_thresholds(self, metrics: Dict[str, Any]):
        """Kiểm tra ngưỡng performance và cảnh báo"""
        alerts = []

        # CPU threshold check
        if metrics['cpu']:
            cpu_usage = metrics['cpu'].get('overall_usage', 0)
            if cpu_usage >= self.thresholds['cpu_critical']:
                alerts.append(f"CRITICAL: CPU usage {cpu_usage}% >= {self.thresholds['cpu_critical']}%")
            elif cpu_usage >= self.thresholds['cpu_warning']:
                alerts.append(f"WARNING: CPU usage {cpu_usage}% >= {self.thresholds['cpu_warning']}%")

        # Memory threshold check
        if metrics['memory']:
            memory_usage = metrics['memory'].get('usage_percent', 0)
            if memory_usage >= self.thresholds['memory_critical']:
                alerts.append(f"CRITICAL: Memory usage {memory_usage}% >= {self.thresholds['memory_critical']}%")
            elif memory_usage >= self.thresholds['memory_warning']:
                alerts.append(f"WARNING: Memory usage {memory_usage}% >= {self.thresholds['memory_warning']}%")

        # GPU threshold check
        if metrics['gpu'] and metrics['gpu'].get('gpus'):
            for gpu in metrics['gpu']['gpus']:
                gpu_usage = gpu.get('gpu_utilization_percent', 0)
                if gpu_usage >= self.thresholds['gpu_critical']:
                    alerts.append(f"CRITICAL: GPU {gpu['gpu_id']} usage {gpu_usage}% >= {self.thresholds['gpu_critical']}%")
                elif gpu_usage >= self.thresholds['gpu_warning']:
                    alerts.append(f"WARNING: GPU {gpu['gpu_id']} usage {gpu_usage}% >= {self.thresholds['gpu_warning']}%")

        # Log alerts
        for alert in alerts:
            if "CRITICAL" in alert:
                self.logger.critical(alert)
            else:
                self.logger.warning(alert)

    def log_api_call(self, api_name: str, response_time: float, status: str, error_message: str = None):
        """Ghi log API call"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO api_calls (timestamp, api_name, response_time, status, error_message) VALUES (?, ?, ?, ?, ?)",
                (datetime.now().isoformat(), api_name, response_time, status, error_message)
            )

            conn.commit()
            conn.close()

            # Store in memory
            self.metrics_data['api_response_times'].append({
                'timestamp': datetime.now().isoformat(),
                'api_name': api_name,
                'response_time': response_time,
                'status': status
            })

            # Check response time threshold
            if response_time >= self.thresholds['response_time_critical']:
                self.logger.critical(f"CRITICAL: {api_name} response time {response_time}ms >= {self.thresholds['response_time_critical']}ms")
            elif response_time >= self.thresholds['response_time_warning']:
                self.logger.warning(f"WARNING: {api_name} response time {response_time}ms >= {self.thresholds['response_time_warning']}ms")

        except Exception as e:
            self.logger.error(f"Failed to log API call: {e}")

    def log_scene_processing(self, scene_id: str, processing_time: float, resolution: str, api_used: str, success: bool):
        """Ghi log scene processing"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO scene_processing (timestamp, scene_id, processing_time, resolution, api_used, success) VALUES (?, ?, ?, ?, ?, ?)",
                (datetime.now().isoformat(), scene_id, processing_time, resolution, api_used, success)
            )

            conn.commit()
            conn.close()

            # Store in memory
            self.metrics_data['scene_generation_times'].append({
                'timestamp': datetime.now().isoformat(),
                'scene_id': scene_id,
                'processing_time': processing_time,
                'resolution': resolution,
                'api_used': api_used,
                'success': success
            })

        except Exception as e:
            self.logger.error(f"Failed to log scene processing: {e}")

    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Lấy tóm tắt performance trong X giờ qua"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            since_time = (datetime.now() - timedelta(hours=hours)).isoformat()

            # CPU statistics
            cursor.execute(
                "SELECT AVG(metric_value), MAX(metric_value), MIN(metric_value) FROM performance_metrics WHERE metric_type = 'cpu_usage' AND timestamp >= ?",
                (since_time,)
            )
            cpu_stats = cursor.fetchone()

            # Memory statistics
            cursor.execute(
                "SELECT AVG(metric_value), MAX(metric_value), MIN(metric_value) FROM performance_metrics WHERE metric_type = 'memory_usage' AND timestamp >= ?",
                (since_time,)
            )
            memory_stats = cursor.fetchone()

            # API call statistics
            cursor.execute(
                "SELECT api_name, COUNT(*), AVG(response_time), MAX(response_time) FROM api_calls WHERE timestamp >= ? GROUP BY api_name",
                (since_time,)
            )
            api_stats = cursor.fetchall()

            # Scene processing statistics
            cursor.execute(
                "SELECT COUNT(*), AVG(processing_time), SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) FROM scene_processing WHERE timestamp >= ?",
                (since_time,)
            )
            scene_stats = cursor.fetchone()

            conn.close()

            return {
                'period_hours': hours,
                'cpu': {
                    'average': round(cpu_stats[0], 1) if cpu_stats[0] else 0,
                    'maximum': round(cpu_stats[1], 1) if cpu_stats[1] else 0,
                    'minimum': round(cpu_stats[2], 1) if cpu_stats[2] else 0
                },
                'memory': {
                    'average': round(memory_stats[0], 1) if memory_stats[0] else 0,
                    'maximum': round(memory_stats[1], 1) if memory_stats[1] else 0,
                    'minimum': round(memory_stats[2], 1) if memory_stats[2] else 0
                },
                'api_calls': [
                    {
                        'api_name': stat[0],
                        'call_count': stat[1],
                        'avg_response_time': round(stat[2], 2) if stat[2] else 0,
                        'max_response_time': round(stat[3], 2) if stat[3] else 0
                    }
                    for stat in api_stats
                ],
                'scene_processing': {
                    'total_scenes': scene_stats[0] if scene_stats[0] else 0,
                    'avg_processing_time': round(scene_stats[1], 2) if scene_stats[1] else 0,
                    'successful_scenes': scene_stats[2] if scene_stats[2] else 0,
                    'success_rate': round((scene_stats[2] / scene_stats[0]) * 100, 1) if scene_stats[0] and scene_stats[2] else 0
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to get performance summary: {e}")
            return {}

    def get_realtime_status(self) -> Dict[str, Any]:
        """Lấy trạng thái real-time"""
        current_metrics = self.collect_all_metrics()

        return {
            'timestamp': current_metrics['timestamp'],
            'monitoring_active': self.monitoring_active,
            'current_cpu_usage': current_metrics['cpu'].get('overall_usage', 0) if current_metrics['cpu'] else 0,
            'current_memory_usage': current_metrics['memory'].get('usage_percent', 0) if current_metrics['memory'] else 0,
            'current_gpu_usage': current_metrics['gpu']['gpus'][0].get('gpu_utilization_percent', 0) if current_metrics['gpu'] and current_metrics['gpu'].get('gpus') else 0,
            'gpu_available': self.gpu_available,
            'recent_api_calls': list(self.metrics_data['api_response_times'])[-10:],
            'recent_scene_times': list(self.metrics_data['scene_generation_times'])[-10:]
        }

    def generate_performance_report(self, hours: int = 24, format: str = 'text') -> str:
        """Tạo báo cáo performance"""
        summary = self.get_performance_summary(hours)

        if format == 'json':
            return json.dumps(summary, indent=2, ensure_ascii=False)

        # Text format report
        report = []
        report.append("=" * 60)
        report.append("ClausoNet 4.0 Pro - Performance Report")
        report.append("=" * 60)
        report.append(f"Period: Last {hours} hours")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # System Performance
        report.append("SYSTEM PERFORMANCE:")
        report.append("-" * 30)

        cpu = summary.get('cpu', {})
        report.append(f"CPU Usage:")
        report.append(f"  Average: {cpu.get('average', 0)}%")
        report.append(f"  Maximum: {cpu.get('maximum', 0)}%")
        report.append(f"  Minimum: {cpu.get('minimum', 0)}%")
        report.append("")

        memory = summary.get('memory', {})
        report.append(f"Memory Usage:")
        report.append(f"  Average: {memory.get('average', 0)}%")
        report.append(f"  Maximum: {memory.get('maximum', 0)}%")
        report.append(f"  Minimum: {memory.get('minimum', 0)}%")
        report.append("")

        # API Performance
        api_calls = summary.get('api_calls', [])
        if api_calls:
            report.append("API PERFORMANCE:")
            report.append("-" * 30)
            for api in api_calls:
                report.append(f"{api['api_name']}:")
                report.append(f"  Total Calls: {api['call_count']}")
                report.append(f"  Avg Response: {api['avg_response_time']}ms")
                report.append(f"  Max Response: {api['max_response_time']}ms")
                report.append("")

        # Scene Processing
        scenes = summary.get('scene_processing', {})
        if scenes.get('total_scenes', 0) > 0:
            report.append("SCENE PROCESSING:")
            report.append("-" * 30)
            report.append(f"Total Scenes: {scenes['total_scenes']}")
            report.append(f"Successful: {scenes['successful_scenes']}")
            report.append(f"Success Rate: {scenes['success_rate']}%")
            report.append(f"Avg Processing Time: {scenes['avg_processing_time']}s")
            report.append("")

        report.append("=" * 60)
        return "\n".join(report)

def main():
    """Hàm main để chạy từ command line"""
    import argparse

    parser = argparse.ArgumentParser(description='ClausoNet 4.0 Pro Performance Monitor')
    parser.add_argument('--start', action='store_true',
                       help='Start monitoring')
    parser.add_argument('--stop', action='store_true',
                       help='Stop monitoring')
    parser.add_argument('--status', action='store_true',
                       help='Show current status')
    parser.add_argument('--report', type=int, metavar='HOURS', default=24,
                       help='Generate performance report for last X hours')
    parser.add_argument('--realtime', action='store_true',
                       help='Show real-time performance data')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='Output format')
    parser.add_argument('--interval', type=int, default=5,
                       help='Collection interval in seconds (default: 5)')

    args = parser.parse_args()

    monitor = PerformanceMonitor()
    monitor.collection_interval = args.interval

    try:
        if args.start:
            print("Starting performance monitoring...")
            monitor.start_monitoring()
            print("Monitoring started. Press Ctrl+C to stop.")

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping monitoring...")
                monitor.stop_monitoring()
                print("Monitoring stopped.")

        elif args.stop:
            print("Stopping performance monitoring...")
            monitor.stop_monitoring()
            print("Monitoring stopped.")

        elif args.status:
            status = monitor.get_realtime_status()
            if args.format == 'json':
                print(json.dumps(status, indent=2))
            else:
                print(f"Monitoring Active: {status['monitoring_active']}")
                print(f"CPU Usage: {status['current_cpu_usage']}%")
                print(f"Memory Usage: {status['current_memory_usage']}%")
                if status['gpu_available']:
                    print(f"GPU Usage: {status['current_gpu_usage']}%")
                else:
                    print("GPU: Not available")

        elif args.realtime:
            print("Real-time Performance Monitor")
            print("Press Ctrl+C to stop")
            print("-" * 40)

            try:
                while True:
                    status = monitor.get_realtime_status()
                    print(f"\r{datetime.now().strftime('%H:%M:%S')} | "
                          f"CPU: {status['current_cpu_usage']:5.1f}% | "
                          f"RAM: {status['current_memory_usage']:5.1f}% | "
                          f"GPU: {status['current_gpu_usage']:5.1f}%", end="")
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n")

        else:
            # Generate report
            print(f"Generating performance report for last {args.report} hours...")
            report = monitor.generate_performance_report(args.report, args.format)
            print(report)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
