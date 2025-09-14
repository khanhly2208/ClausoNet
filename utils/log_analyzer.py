#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Log Analyzer
Phân tích log hệ thống, API, hiệu năng và tạo báo cáo
"""

import os
import sys
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
from collections import defaultdict, Counter
import sqlite3
import time
class LogAnalyzer:
    def __init__(self, logs_dir: str = "logs/"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)

        # Log file patterns
        self.log_patterns = {
            'main': 'clausonet_main.log*',
            'api': 'api_calls.log*',
            'performance': 'performance.log*',
            'license': 'license.log*',
            'batch': 'batch_processing.log*',
            'backup': 'backup.log*',
            'system': 'system_check.log*',
            'template': 'template_lister.log*'
        }

        # Error patterns for analysis
        self.error_patterns = {
            'api_error': r'API.*(?:error|failed|timeout)',
            'license_error': r'(?:license|activation).*(?:error|failed|invalid)',
            'memory_error': r'(?:memory|out of memory|OOM)',
            'disk_error': r'(?:disk|storage|space).*(?:error|full|failed)',
            'network_error': r'(?:network|connection|timeout).*(?:error|failed)',
            'gpu_error': r'(?:GPU|CUDA|graphics).*(?:error|failed)',
            'processing_error': r'(?:processing|generation|scene).*(?:error|failed)'
        }

        # Performance thresholds
        self.performance_thresholds = {
            'response_time_warning': 5.0,
            'response_time_critical': 10.0,
            'cpu_warning': 80.0,
            'memory_warning': 85.0,
            'gpu_warning': 85.0
        }

        self.setup_logging()

    def setup_logging(self):
        """Thiết lập logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.logs_dir / 'log_analyzer.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('LogAnalyzer')

    def find_log_files(self, log_type: str = None) -> List[Path]:
        """Tìm các file log theo type"""
        log_files = []

        if log_type and log_type in self.log_patterns:
            pattern = self.log_patterns[log_type]
            log_files.extend(self.logs_dir.glob(pattern))
        else:
            # Find all log files
            for pattern in self.log_patterns.values():
                log_files.extend(self.logs_dir.glob(pattern))

        # Sort by modification time (newest first)
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return log_files

    def parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Phân tích một dòng log"""
        # Standard log format: timestamp - logger - level - message
        log_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([^-]+) - (\w+) - (.+)'
        match = re.match(log_pattern, line.strip())

        if match:
            timestamp_str, logger_name, level, message = match.groups()

            try:
                # Parse timestamp
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
            except ValueError:
                # Try alternative format
                try:
                    timestamp = datetime.strptime(timestamp_str[:19], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    timestamp = datetime.now()

            return {
                'timestamp': timestamp,
                'logger': logger_name.strip(),
                'level': level.strip(),
                'message': message.strip(),
                'raw_line': line.strip()
            }

        return None

    def analyze_log_file(self, log_file: Path, start_time: datetime = None, end_time: datetime = None) -> Dict[str, Any]:
        """Phân tích một file log"""
        self.logger.info(f"Analyzing log file: {log_file}")

        analysis = {
            'file_path': str(log_file),
            'file_size': log_file.stat().st_size,
            'last_modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat(),
            'total_lines': 0,
            'parsed_lines': 0,
            'log_levels': Counter(),
            'loggers': Counter(),
            'errors': [],
            'warnings': [],
            'time_range': {'start': None, 'end': None},
            'error_patterns': defaultdict(list),
            'api_calls': [],
            'performance_issues': []
        }

        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    analysis['total_lines'] = line_num

                    # Parse log line
                    parsed = self.parse_log_line(line)
                    if not parsed:
                        continue

                    # Check time range filter
                    if start_time and parsed['timestamp'] < start_time:
                        continue
                    if end_time and parsed['timestamp'] > end_time:
                        continue

                    analysis['parsed_lines'] += 1

                    # Update time range
                    if not analysis['time_range']['start'] or parsed['timestamp'] < analysis['time_range']['start']:
                        analysis['time_range']['start'] = parsed['timestamp'].isoformat()
                    if not analysis['time_range']['end'] or parsed['timestamp'] > analysis['time_range']['end']:
                        analysis['time_range']['end'] = parsed['timestamp'].isoformat()

                    # Count levels and loggers
                    analysis['log_levels'][parsed['level']] += 1
                    analysis['loggers'][parsed['logger']] += 1

                    # Collect errors and warnings
                    if parsed['level'] == 'ERROR':
                        analysis['errors'].append({
                            'timestamp': parsed['timestamp'].isoformat(),
                            'logger': parsed['logger'],
                            'message': parsed['message'],
                            'line_number': line_num
                        })
                    elif parsed['level'] == 'WARNING':
                        analysis['warnings'].append({
                            'timestamp': parsed['timestamp'].isoformat(),
                            'logger': parsed['logger'],
                            'message': parsed['message'],
                            'line_number': line_num
                        })

                    # Check error patterns
                    self.check_error_patterns(parsed, analysis['error_patterns'])

                    # Extract API call information
                    self.extract_api_info(parsed, analysis['api_calls'])

                    # Check performance issues
                    self.check_performance_issues(parsed, analysis['performance_issues'])

        except Exception as e:
            self.logger.error(f"Failed to analyze log file {log_file}: {e}")
            analysis['error'] = str(e)

        return analysis

    def check_error_patterns(self, parsed_line: Dict[str, Any], error_patterns: Dict[str, List]):
        """Kiểm tra error patterns"""
        message = parsed_line['message'].lower()

        for pattern_name, pattern in self.error_patterns.items():
            if re.search(pattern, message, re.IGNORECASE):
                error_patterns[pattern_name].append({
                    'timestamp': parsed_line['timestamp'].isoformat(),
                    'logger': parsed_line['logger'],
                    'level': parsed_line['level'],
                    'message': parsed_line['message']
                })

    def extract_api_info(self, parsed_line: Dict[str, Any], api_calls: List[Dict[str, Any]]):
        """Trích xuất thông tin API calls"""
        message = parsed_line['message']

        # Look for API call patterns
        api_patterns = [
            r'API call to (\w+).*?(\d+\.?\d*)\s*ms',
            r'(\w+) API.*?response time[:\s]+(\d+\.?\d*)\s*ms',
            r'Testing (\w+) API.*?(\d+\.?\d*)\s*ms'
        ]

        for pattern in api_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                api_name, response_time = match.groups()
                api_calls.append({
                    'timestamp': parsed_line['timestamp'].isoformat(),
                    'api_name': api_name,
                    'response_time': float(response_time),
                    'logger': parsed_line['logger'],
                    'level': parsed_line['level']
                })
                break

    def check_performance_issues(self, parsed_line: Dict[str, Any], performance_issues: List[Dict[str, Any]]):
        """Kiểm tra performance issues"""
        message = parsed_line['message']

        # Check for performance warnings/errors
        perf_patterns = [
            (r'CPU usage (\d+\.?\d*)%', 'cpu_usage'),
            (r'Memory usage (\d+\.?\d*)%', 'memory_usage'),
            (r'GPU usage (\d+\.?\d*)%', 'gpu_usage'),
            (r'response time (\d+\.?\d*)\s*ms', 'response_time')
        ]

        for pattern, metric_type in perf_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                value = float(match.group(1))

                # Check thresholds
                threshold_key = f"{metric_type.split('_')[0]}_warning"
                if metric_type == 'response_time':
                    threshold_key = 'response_time_warning'

                if threshold_key in self.performance_thresholds:
                    threshold = self.performance_thresholds[threshold_key]
                    if value >= threshold:
                        performance_issues.append({
                            'timestamp': parsed_line['timestamp'].isoformat(),
                            'metric_type': metric_type,
                            'value': value,
                            'threshold': threshold,
                            'severity': 'critical' if value >= threshold * 1.2 else 'warning',
                            'message': parsed_line['message']
                        })
                break

    def analyze_all_logs(self, start_time: datetime = None, end_time: datetime = None, log_types: List[str] = None) -> Dict[str, Any]:
        """Phân tích tất cả log files"""
        self.logger.info("Starting comprehensive log analysis...")

        if not start_time:
            start_time = datetime.now() - timedelta(days=7)  # Default: last 7 days

        if not end_time:
            end_time = datetime.now()

        overall_analysis = {
            'analysis_period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'duration_hours': (end_time - start_time).total_seconds() / 3600
            },
            'log_files_analyzed': [],
            'total_log_files': 0,
            'total_lines_analyzed': 0,
            'summary': {
                'total_errors': 0,
                'total_warnings': 0,
                'unique_error_types': 0,
                'api_calls_analyzed': 0,
                'performance_issues': 0
            },
            'error_distribution': Counter(),
            'logger_activity': Counter(),
            'api_performance': {},
            'error_timeline': [],
            'recommendations': []
        }

        # Find log files to analyze
        if log_types:
            log_files = []
            for log_type in log_types:
                log_files.extend(self.find_log_files(log_type))
        else:
            log_files = self.find_log_files()

        overall_analysis['total_log_files'] = len(log_files)

        # Analyze each log file
        all_errors = []
        all_api_calls = []
        all_performance_issues = []

        for log_file in log_files:
            file_analysis = self.analyze_log_file(log_file, start_time, end_time)
            overall_analysis['log_files_analyzed'].append({
                'file': str(log_file),
                'lines_parsed': file_analysis['parsed_lines'],
                'errors': len(file_analysis['errors']),
                'warnings': len(file_analysis['warnings'])
            })

            overall_analysis['total_lines_analyzed'] += file_analysis['parsed_lines']

            # Aggregate data
            all_errors.extend(file_analysis['errors'])
            all_api_calls.extend(file_analysis['api_calls'])
            all_performance_issues.extend(file_analysis['performance_issues'])

            # Update counters
            for level, count in file_analysis['log_levels'].items():
                overall_analysis['error_distribution'][level] += count

            for logger, count in file_analysis['loggers'].items():
                overall_analysis['logger_activity'][logger] += count

        # Calculate summary statistics
        overall_analysis['summary']['total_errors'] = len(all_errors)
        overall_analysis['summary']['total_warnings'] = len([e for e in all_errors if 'WARNING' in str(e)])
        overall_analysis['summary']['api_calls_analyzed'] = len(all_api_calls)
        overall_analysis['summary']['performance_issues'] = len(all_performance_issues)

        # Analyze API performance
        overall_analysis['api_performance'] = self.analyze_api_performance(all_api_calls)

        # Create error timeline
        overall_analysis['error_timeline'] = self.create_error_timeline(all_errors)

        # Generate recommendations
        overall_analysis['recommendations'] = self.generate_recommendations(overall_analysis, all_errors, all_performance_issues)

        self.logger.info("Log analysis completed")
        return overall_analysis

    def analyze_api_performance(self, api_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Phân tích hiệu năng API"""
        if not api_calls:
            return {}

        api_stats = defaultdict(lambda: {'calls': [], 'total_calls': 0})

        for call in api_calls:
            api_name = call['api_name']
            response_time = call['response_time']

            api_stats[api_name]['calls'].append(response_time)
            api_stats[api_name]['total_calls'] += 1

        # Calculate statistics for each API
        performance_summary = {}
        for api_name, stats in api_stats.items():
            response_times = stats['calls']

            performance_summary[api_name] = {
                'total_calls': stats['total_calls'],
                'avg_response_time': sum(response_times) / len(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'slow_calls': len([t for t in response_times if t > self.performance_thresholds['response_time_warning']]),
                'failed_calls': 0  # Would need to track this separately
            }

        return performance_summary

    def create_error_timeline(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Tạo timeline của errors"""
        if not errors:
            return []

        # Group errors by hour
        hourly_errors = defaultdict(int)

        for error in errors:
            try:
                timestamp = datetime.fromisoformat(error['timestamp'])
                hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                hourly_errors[hour_key] += 1
            except:
                continue

        # Convert to timeline format
        timeline = []
        for hour, count in sorted(hourly_errors.items()):
            timeline.append({
                'hour': hour,
                'error_count': count
            })

        return timeline

    def generate_recommendations(self, analysis: Dict[str, Any], errors: List[Dict[str, Any]], performance_issues: List[Dict[str, Any]]) -> List[str]:
        """Tạo recommendations dựa trên phân tích"""
        recommendations = []

        # Check error rate
        total_lines = analysis['total_lines_analyzed']
        error_count = analysis['summary']['total_errors']

        if total_lines > 0:
            error_rate = (error_count / total_lines) * 100
            if error_rate > 5:
                recommendations.append(f"High error rate detected ({error_rate:.1f}%). Review error logs and fix critical issues.")

        # Check API performance
        api_perf = analysis.get('api_performance', {})
        for api_name, stats in api_perf.items():
            if stats['avg_response_time'] > self.performance_thresholds['response_time_warning']:
                recommendations.append(f"{api_name} API has slow response times (avg: {stats['avg_response_time']:.1f}ms). Consider optimizing or checking network connectivity.")

        # Check performance issues
        if len(performance_issues) > 10:
            recommendations.append(f"Multiple performance issues detected ({len(performance_issues)}). Monitor system resources and consider hardware upgrades.")

        # Check for common error patterns
        error_messages = [e.get('message', '') for e in errors]
        common_errors = Counter(error_messages).most_common(3)

        for error_msg, count in common_errors:
            if count > 5:
                recommendations.append(f"Recurring error detected: '{error_msg[:100]}...' ({count} times). Investigate root cause.")

        # Check logger activity
        logger_activity = analysis.get('logger_activity', {})
        if 'ERROR' in analysis.get('error_distribution', {}) and analysis['error_distribution']['ERROR'] > 50:
            recommendations.append("High number of ERROR level logs. Review application stability and error handling.")

        if not recommendations:
            recommendations.append("No critical issues detected. System appears to be running normally.")

        return recommendations

    def export_analysis_report(self, analysis: Dict[str, Any], output_path: str, format: str = 'json'):
        """Export phân tích ra file"""
        try:
            output_file = Path(output_path)

            if format.lower() == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)

            elif format.lower() == 'html':
                html_content = self.generate_html_report(analysis)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)

            else:  # text format
                text_content = self.generate_text_report(analysis)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text_content)

            self.logger.info(f"Analysis report exported: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export analysis report: {e}")
            return False

    def generate_text_report(self, analysis: Dict[str, Any]) -> str:
        """Tạo báo cáo text"""
        report = []
        report.append("=" * 80)
        report.append("ClausoNet 4.0 Pro - Log Analysis Report")
        report.append("=" * 80)

        # Analysis period
        period = analysis['analysis_period']
        report.append(f"Analysis Period: {period['start']} to {period['end']}")
        report.append(f"Duration: {period['duration_hours']:.1f} hours")
        report.append("")

        # Summary
        summary = analysis['summary']
        report.append("SUMMARY:")
        report.append("-" * 40)
        report.append(f"Log Files Analyzed: {analysis['total_log_files']}")
        report.append(f"Total Lines Processed: {analysis['total_lines_analyzed']:,}")
        report.append(f"Total Errors: {summary['total_errors']}")
        report.append(f"Total Warnings: {summary['total_warnings']}")
        report.append(f"API Calls Analyzed: {summary['api_calls_analyzed']}")
        report.append(f"Performance Issues: {summary['performance_issues']}")
        report.append("")

        # Error Distribution
        if analysis['error_distribution']:
            report.append("ERROR DISTRIBUTION:")
            report.append("-" * 40)
            for level, count in analysis['error_distribution'].most_common():
                report.append(f"  {level}: {count}")
            report.append("")

        # API Performance
        if analysis['api_performance']:
            report.append("API PERFORMANCE:")
            report.append("-" * 40)
            for api_name, stats in analysis['api_performance'].items():
                report.append(f"  {api_name}:")
                report.append(f"    Total Calls: {stats['total_calls']}")
                report.append(f"    Avg Response: {stats['avg_response_time']:.1f}ms")
                report.append(f"    Max Response: {stats['max_response_time']:.1f}ms")
                report.append(f"    Slow Calls: {stats['slow_calls']}")
                report.append("")

        # Recommendations
        if analysis['recommendations']:
            report.append("RECOMMENDATIONS:")
            report.append("-" * 40)
            for i, rec in enumerate(analysis['recommendations'], 1):
                report.append(f"{i}. {rec}")
            report.append("")

        report.append("=" * 80)
        return "\n".join(report)

    def generate_html_report(self, analysis: Dict[str, Any]) -> str:
        """Tạo báo cáo HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ClausoNet 4.0 Pro - Log Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .section {{ margin: 20px 0; }}
                .metric {{ background-color: #ecf0f1; padding: 10px; margin: 5px; display: inline-block; }}
                .recommendation {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin: 5px 0; }}
                .error {{ color: #e74c3c; }}
                .warning {{ color: #f39c12; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #34495e; color: white; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>ClausoNet 4.0 Pro</h1>
                <h2>Log Analysis Report</h2>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="section">
                <h3>Summary</h3>
                <div class="metric">Log Files: {analysis['total_log_files']}</div>
                <div class="metric">Lines Processed: {analysis['total_lines_analyzed']:,}</div>
                <div class="metric error">Errors: {analysis['summary']['total_errors']}</div>
                <div class="metric warning">Warnings: {analysis['summary']['total_warnings']}</div>
                <div class="metric">API Calls: {analysis['summary']['api_calls_analyzed']}</div>
                <div class="metric">Performance Issues: {analysis['summary']['performance_issues']}</div>
            </div>
        """

        # Add API Performance table
        if analysis['api_performance']:
            html += """
            <div class="section">
                <h3>API Performance</h3>
                <table>
                    <tr>
                        <th>API Name</th>
                        <th>Total Calls</th>
                        <th>Avg Response (ms)</th>
                        <th>Max Response (ms)</th>
                        <th>Slow Calls</th>
                    </tr>
            """

            for api_name, stats in analysis['api_performance'].items():
                html += f"""
                    <tr>
                        <td>{api_name}</td>
                        <td>{stats['total_calls']}</td>
                        <td>{stats['avg_response_time']:.1f}</td>
                        <td>{stats['max_response_time']:.1f}</td>
                        <td>{stats['slow_calls']}</td>
                    </tr>
                """

            html += "</table></div>"

        # Add Recommendations
        if analysis['recommendations']:
            html += """
            <div class="section">
                <h3>Recommendations</h3>
            """

            for rec in analysis['recommendations']:
                html += f'<div class="recommendation">{rec}</div>'

            html += "</div>"

        html += """
        </body>
        </html>
        """

        return html

def main():
    """Hàm main để chạy từ command line"""
    import argparse

    parser = argparse.ArgumentParser(description='ClausoNet 4.0 Pro Log Analyzer')
    parser.add_argument('--analyze', action='store_true',
                       help='Perform log analysis')
    parser.add_argument('--logs-dir', default='logs/',
                       help='Logs directory path')
    parser.add_argument('--log-types', nargs='+',
                       choices=list(LogAnalyzer('').log_patterns.keys()),
                       help='Specific log types to analyze')
    parser.add_argument('--start-time',
                       help='Start time for analysis (ISO format: 2024-01-01T00:00:00)')
    parser.add_argument('--end-time',
                       help='End time for analysis (ISO format: 2024-01-01T23:59:59)')
    parser.add_argument('--hours', type=int, default=24,
                       help='Analyze last X hours (default: 24)')
    parser.add_argument('--output', '-o',
                       help='Output file path for analysis report')
    parser.add_argument('--format', choices=['text', 'json', 'html'], default='text',
                       help='Output format')
    parser.add_argument('--real-time', action='store_true',
                       help='Monitor logs in real-time')

    args = parser.parse_args()

    analyzer = LogAnalyzer(args.logs_dir)

    try:
        # Parse time arguments
        start_time = None
        end_time = None

        if args.start_time:
            start_time = datetime.fromisoformat(args.start_time)
        elif args.hours:
            start_time = datetime.now() - timedelta(hours=args.hours)

        if args.end_time:
            end_time = datetime.fromisoformat(args.end_time)
        else:
            end_time = datetime.now()

        if args.real_time:
            print("Real-time log monitoring (Press Ctrl+C to stop)")
            print("-" * 50)

            try:
                while True:
                    # Monitor for new log entries
                    # This is a simplified version - real implementation would use file watchers
                    time.sleep(5)
                    recent_analysis = analyzer.analyze_all_logs(
                        start_time=datetime.now() - timedelta(minutes=5),
                        log_types=args.log_types
                    )

                    if recent_analysis['summary']['total_errors'] > 0:
                        print(f"{datetime.now().strftime('%H:%M:%S')} - New errors detected: {recent_analysis['summary']['total_errors']}")

            except KeyboardInterrupt:
                print("\nReal-time monitoring stopped")

        elif args.analyze:
            print("ClausoNet 4.0 Pro - Log Analyzer")
            print(f"Analyzing logs from {start_time} to {end_time}")
            print("This may take a few moments...")
            print()

            # Perform analysis
            analysis = analyzer.analyze_all_logs(start_time, end_time, args.log_types)

            # Generate and output report
            if args.format == 'json':
                report = json.dumps(analysis, indent=2, ensure_ascii=False, default=str)
            elif args.format == 'html':
                report = analyzer.generate_html_report(analysis)
            else:
                report = analyzer.generate_text_report(analysis)

            # Output to file or console
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"Analysis report saved to: {args.output}")
            else:
                print(report)

        else:
            # Show available log files
            print("ClausoNet 4.0 Pro - Log Analyzer")
            print("=" * 40)
            print(f"Logs directory: {analyzer.logs_dir}")
            print()

            for log_type, pattern in analyzer.log_patterns.items():
                log_files = analyzer.find_log_files(log_type)
                print(f"{log_type.upper()} logs ({pattern}):")
                if log_files:
                    for log_file in log_files[:3]:  # Show first 3 files
                        size = log_file.stat().st_size / 1024  # KB
                        modified = datetime.fromtimestamp(log_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                        print(f"  • {log_file.name} ({size:.1f} KB, modified: {modified})")
                    if len(log_files) > 3:
                        print(f"  ... and {len(log_files) - 3} more files")
                else:
                    print("  No log files found")
                print()

            print("Use --analyze to perform log analysis")
            print("Use --help for more options")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
