#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - System Requirements Checker
Kiểm tra cấu hình hệ thống có đáp ứng yêu cầu tối thiểu không
"""

import psutil
import platform
import sys
import json
import subprocess
from typing import Dict, Any, Tuple
import logging

class SystemChecker:
    def __init__(self):
        self.min_requirements = {
            'cpu_cores': 6,
            'ram_gb': 16,
            'gpu_memory_gb': 4,
            'disk_space_gb': 50,
            'python_version': (3, 11),
            'cuda_available': False,  # Optional but recommended
            'windows_version': 10
        }

        self.recommended_requirements = {
            'cpu_cores': 8,
            'ram_gb': 32,
            'gpu_memory_gb': 8,
            'disk_space_gb': 100,
            'python_version': (3, 11),
            'cuda_available': True,
            'windows_version': 11
        }

        self.setup_logging()

    def setup_logging(self):
        """Thiết lập logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/system_check.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('SystemChecker')

    def check_cpu(self) -> Dict[str, Any]:
        """Kiểm tra CPU"""
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_count_physical = psutil.cpu_count(logical=False)
        cpu_freq = psutil.cpu_freq()

        try:
            # Lấy thông tin CPU từ wmic (Windows)
            result = subprocess.run(
                ['wmic', 'cpu', 'get', 'name', '/format:value'],
                capture_output=True, text=True, shell=True
            )
            cpu_name = "Unknown"
            for line in result.stdout.split('\n'):
                if line.startswith('Name='):
                    cpu_name = line.split('=', 1)[1].strip()
                    break
        except:
            cpu_name = "Unknown"

        result = {
            'name': cpu_name,
            'logical_cores': cpu_count_logical,
            'physical_cores': cpu_count_physical,
            'max_frequency_mhz': cpu_freq.max if cpu_freq else 0,
            'meets_minimum': cpu_count_physical >= self.min_requirements['cpu_cores'],
            'meets_recommended': cpu_count_physical >= self.recommended_requirements['cpu_cores']
        }

        self.logger.info(f"CPU Check: {cpu_name} - {cpu_count_physical} cores")
        return result

    def check_memory(self) -> Dict[str, Any]:
        """Kiểm tra RAM"""
        memory = psutil.virtual_memory()
        ram_gb = memory.total / (1024**3)

        result = {
            'total_gb': round(ram_gb, 1),
            'available_gb': round(memory.available / (1024**3), 1),
            'used_percent': memory.percent,
            'meets_minimum': ram_gb >= self.min_requirements['ram_gb'],
            'meets_recommended': ram_gb >= self.recommended_requirements['ram_gb']
        }

        self.logger.info(f"Memory Check: {result['total_gb']}GB total")
        return result

    def check_gpu(self) -> Dict[str, Any]:
        """Kiểm tra GPU"""
        gpu_info = {'available': False, 'cuda_available': False}

        try:
            import pynvml
            pynvml.nvmlInit()
            gpu_count = pynvml.nvmlDeviceGetCount()

            if gpu_count > 0:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                gpu_memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                gpu_name = pynvml.nvmlDeviceGetName(handle).decode()
                gpu_memory_gb = gpu_memory_info.total / (1024**3)

                gpu_info.update({
                    'available': True,
                    'name': gpu_name,
                    'memory_gb': round(gpu_memory_gb, 1),
                    'memory_used_gb': round(gpu_memory_info.used / (1024**3), 1),
                    'memory_free_gb': round(gpu_memory_info.free / (1024**3), 1),
                    'meets_minimum': gpu_memory_gb >= self.min_requirements['gpu_memory_gb'],
                    'meets_recommended': gpu_memory_gb >= self.recommended_requirements['gpu_memory_gb']
                })

                self.logger.info(f"GPU Check: {gpu_name} - {gpu_memory_gb:.1f}GB VRAM")
        except ImportError:
            self.logger.warning("pynvml not available - GPU check skipped")
        except Exception as e:
            self.logger.error(f"GPU check failed: {e}")

        # CUDA check not needed for API-only version
        gpu_info['cuda_available'] = False
        gpu_info['cuda_version'] = "N/A"
        gpu_info['torch_version'] = "N/A"

        return gpu_info

    def check_disk_space(self) -> Dict[str, Any]:
        """Kiểm tra dung lượng đĩa"""
        current_drive = psutil.disk_usage('.')

        total_gb = current_drive.total / (1024**3)
        free_gb = current_drive.free / (1024**3)
        used_gb = current_drive.used / (1024**3)

        result = {
            'total_gb': round(total_gb, 1),
            'free_gb': round(free_gb, 1),
            'used_gb': round(used_gb, 1),
            'used_percent': round((used_gb / total_gb) * 100, 1),
            'meets_minimum': free_gb >= self.min_requirements['disk_space_gb'],
            'meets_recommended': free_gb >= self.recommended_requirements['disk_space_gb']
        }

        self.logger.info(f"Disk Check: {free_gb:.1f}GB free space")
        return result

    def check_python_version(self) -> Dict[str, Any]:
        """Kiểm tra phiên bản Python"""
        current_version = sys.version_info
        min_version = self.min_requirements['python_version']

        result = {
            'current_version': f"{current_version.major}.{current_version.minor}.{current_version.micro}",
            'required_version': f"{min_version[0]}.{min_version[1]}+",
            'meets_requirement': (current_version.major, current_version.minor) >= min_version
        }

        self.logger.info(f"Python Check: {result['current_version']}")
        return result

    def check_windows_version(self) -> Dict[str, Any]:
        """Kiểm tra phiên bản Windows"""
        system = platform.system()
        release = platform.release()
        version = platform.version()

        result = {
            'system': system,
            'release': release,
            'version': version,
            'is_windows': system == 'Windows',
            'meets_requirement': system == 'Windows' and int(release) >= self.min_requirements['windows_version']
        }

        if result['is_windows']:
            try:
                # Lấy thông tin Windows build
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
                build_number = winreg.QueryValueEx(key, "CurrentBuild")[0]
                product_name = winreg.QueryValueEx(key, "ProductName")[0]
                winreg.CloseKey(key)

                result.update({
                    'build_number': build_number,
                    'product_name': product_name
                })
            except Exception as e:
                self.logger.warning(f"Could not get detailed Windows info: {e}")

        self.logger.info(f"OS Check: {system} {release}")
        return result

    def check_required_software(self) -> Dict[str, Any]:
        """Kiểm tra phần mềm cần thiết"""
        software_checks = {}

        # Check FFmpeg
        try:
            result = subprocess.run(['ffmpeg', '-version'],
                                  capture_output=True, text=True, timeout=10)
            software_checks['ffmpeg'] = {
                'available': result.returncode == 0,
                'version': result.stdout.split('\n')[0] if result.returncode == 0 else None
            }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            software_checks['ffmpeg'] = {'available': False, 'version': None}

        # Check Visual C++ Redistributable
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\X64")
            version = winreg.QueryValueEx(key, "Version")[0]
            winreg.CloseKey(key)
            software_checks['vc_redist'] = {'available': True, 'version': version}
        except:
            software_checks['vc_redist'] = {'available': False, 'version': None}

        return software_checks

    def check_network_connectivity(self) -> Dict[str, Any]:
        """Kiểm tra kết nối mạng"""
        import socket
        import time

        endpoints = {
            'google_api': ('googleapis.com', 443),
            'openai_api': ('api.openai.com', 443),
            'clausonet_license': ('license.clausonet.com', 443)
        }

        connectivity_results = {}

        for name, (host, port) in endpoints.items():
            try:
                start_time = time.time()
                sock = socket.create_connection((host, port), timeout=10)
                sock.close()
                response_time = (time.time() - start_time) * 1000

                connectivity_results[name] = {
                    'accessible': True,
                    'response_time_ms': round(response_time, 2)
                }
            except Exception as e:
                connectivity_results[name] = {
                    'accessible': False,
                    'error': str(e)
                }

        return connectivity_results

    def run_full_system_check(self) -> Dict[str, Any]:
        """Chạy kiểm tra toàn bộ hệ thống"""
        self.logger.info("Starting comprehensive system check...")

        results = {
            'timestamp': psutil.boot_time(),
            'cpu': self.check_cpu(),
            'memory': self.check_memory(),
            'gpu': self.check_gpu(),
            'disk': self.check_disk_space(),
            'python': self.check_python_version(),
            'os': self.check_windows_version(),
            'software': self.check_required_software(),
            'network': self.check_network_connectivity()
        }

        # Tính tổng điểm đánh giá
        results['overall_assessment'] = self.calculate_overall_score(results)

        self.logger.info("System check completed")
        return results

    def calculate_overall_score(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Tính điểm tổng thể"""
        checks = {
            'cpu_minimum': results['cpu']['meets_minimum'],
            'memory_minimum': results['memory']['meets_minimum'],
            'disk_minimum': results['disk']['meets_minimum'],
            'python_version': results['python']['meets_requirement'],
            'windows_version': results['os']['meets_requirement'],
            'gpu_available': results['gpu']['available']
        }

        passed_checks = sum(1 for check in checks.values() if check)
        total_checks = len(checks)

        score_percentage = (passed_checks / total_checks) * 100

        if score_percentage >= 90:
            status = "Excellent"
            recommendation = "System fully optimized for ClausoNet 4.0 Pro"
        elif score_percentage >= 75:
            status = "Good"
            recommendation = "System meets requirements with minor optimizations possible"
        elif score_percentage >= 60:
            status = "Acceptable"
            recommendation = "System meets minimum requirements but upgrades recommended"
        else:
            status = "Insufficient"
            recommendation = "System requires upgrades before running ClausoNet 4.0 Pro"

        return {
            'score_percentage': round(score_percentage, 1),
            'status': status,
            'recommendation': recommendation,
            'failed_checks': [check for check, passed in checks.items() if not passed]
        }

    def generate_report(self, results: Dict[str, Any], format: str = 'text') -> str:
        """Tạo báo cáo kiểm tra hệ thống"""
        if format == 'json':
            return json.dumps(results, indent=2, ensure_ascii=False)

        # Text format report
        report = []
        report.append("=" * 60)
        report.append("ClausoNet 4.0 Pro - System Requirements Report")
        report.append("=" * 60)
        report.append("")

        # Overall Assessment
        assessment = results['overall_assessment']
        report.append(f"Overall Score: {assessment['score_percentage']}% - {assessment['status']}")
        report.append(f"Recommendation: {assessment['recommendation']}")
        report.append("")

        # Detailed Results
        report.append("DETAILED RESULTS:")
        report.append("-" * 40)

        # CPU
        cpu = results['cpu']
        status = "✓ PASS" if cpu['meets_minimum'] else "✗ FAIL"
        report.append(f"CPU: {status}")
        report.append(f"  - Model: {cpu['name']}")
        report.append(f"  - Cores: {cpu['physical_cores']} physical, {cpu['logical_cores']} logical")
        report.append(f"  - Required: {self.min_requirements['cpu_cores']}+ cores")
        report.append("")

        # Memory
        memory = results['memory']
        status = "✓ PASS" if memory['meets_minimum'] else "✗ FAIL"
        report.append(f"Memory: {status}")
        report.append(f"  - Total: {memory['total_gb']} GB")
        report.append(f"  - Available: {memory['available_gb']} GB")
        report.append(f"  - Required: {self.min_requirements['ram_gb']}+ GB")
        report.append("")

        # GPU
        gpu = results['gpu']
        if gpu['available']:
            status = "✓ PASS" if gpu.get('meets_minimum', False) else "⚠ LIMITED"
            report.append(f"GPU: {status}")
            report.append(f"  - Model: {gpu['name']}")
            report.append(f"  - VRAM: {gpu['memory_gb']} GB")
            report.append(f"  - CUDA: {'Available' if gpu['cuda_available'] else 'Not Available'}")
        else:
            report.append("GPU: ⚠ NOT DETECTED")
            report.append("  - Note: GPU acceleration recommended for optimal performance")
        report.append("")

        # Disk Space
        disk = results['disk']
        status = "✓ PASS" if disk['meets_minimum'] else "✗ FAIL"
        report.append(f"Disk Space: {status}")
        report.append(f"  - Free: {disk['free_gb']} GB")
        report.append(f"  - Total: {disk['total_gb']} GB")
        report.append(f"  - Required: {self.min_requirements['disk_space_gb']}+ GB")
        report.append("")

        # Python Version
        python = results['python']
        status = "✓ PASS" if python['meets_requirement'] else "✗ FAIL"
        report.append(f"Python Version: {status}")
        report.append(f"  - Current: {python['current_version']}")
        report.append(f"  - Required: {python['required_version']}")
        report.append("")

        # Operating System
        os_info = results['os']
        status = "✓ PASS" if os_info['meets_requirement'] else "✗ FAIL"
        report.append(f"Operating System: {status}")
        report.append(f"  - System: {os_info['system']} {os_info['release']}")
        if 'product_name' in os_info:
            report.append(f"  - Edition: {os_info['product_name']}")
        report.append("")

        # Software Dependencies
        software = results['software']
        report.append("Required Software:")
        for name, info in software.items():
            status = "✓ INSTALLED" if info['available'] else "✗ MISSING"
            report.append(f"  - {name.upper()}: {status}")
            if info['version']:
                report.append(f"    Version: {info['version']}")
        report.append("")

        # Network Connectivity
        network = results['network']
        report.append("Network Connectivity:")
        for endpoint, info in network.items():
            if info['accessible']:
                report.append(f"  - {endpoint}: ✓ OK ({info['response_time_ms']}ms)")
            else:
                report.append(f"  - {endpoint}: ✗ FAILED ({info['error']})")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)

def main():
    """Hàm main để chạy từ command line"""
    import argparse

    parser = argparse.ArgumentParser(description='ClausoNet 4.0 Pro System Checker')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='Output format (default: text)')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Quiet mode - minimal output')

    args = parser.parse_args()

    # Tạo thư mục logs nếu chưa có
    import os
    os.makedirs('logs', exist_ok=True)

    checker = SystemChecker()

    if not args.quiet:
        print("ClausoNet 4.0 Pro - System Requirements Check")
        print("Checking system compatibility...")
        print("")

    # Chạy kiểm tra
    results = checker.run_full_system_check()

    # Tạo báo cáo
    report = checker.generate_report(results, args.format)

    # Xuất kết quả
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report saved to: {args.output}")
    else:
        print(report)

    # Exit code dựa trên kết quả
    assessment = results['overall_assessment']
    if assessment['score_percentage'] >= 75:
        sys.exit(0)  # Success
    elif assessment['score_percentage'] >= 60:
        sys.exit(1)  # Warning
    else:
        sys.exit(2)  # Error

if __name__ == "__main__":
    main()
