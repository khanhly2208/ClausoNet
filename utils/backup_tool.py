#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Backup and Restore Tool
Tạo và phục hồi backup cho cấu hình, cache, dữ liệu người dùng
"""

import os
import sys
import json
import shutil
import zipfile
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import yaml

class BackupTool:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()

        # Backup paths
        self.backup_dir = Path("./backups/")
        self.backup_dir.mkdir(exist_ok=True)

        # Directories to backup
        self.backup_targets = {
            'config': {
                'paths': ['config.yaml', 'license/', 'certs/'],
                'description': 'Configuration files and licenses'
            },
            'user_data': {
                'paths': ['data/templates/', 'data/assets/', 'projects/'],
                'description': 'User templates, assets, and projects'
            },
            'cache': {
                'paths': ['data/cache/', 'temp/'],
                'description': 'Cache and temporary files'
            },
            'logs': {
                'paths': ['logs/'],
                'description': 'Application logs'
            },
            'outputs': {
                'paths': ['output/'],
                'description': 'Generated videos and outputs'
            }
        }

        self.setup_logging()

    def setup_logging(self):
        """Thiết lập logging"""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/backup.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('BackupTool')

    def load_config(self) -> Dict[str, Any]:
        """Đọc cấu hình từ config.yaml"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config or {}
        except FileNotFoundError:
            return {}
        except Exception as e:
            print(f"Failed to load config: {e}")
            return {}

    def calculate_directory_size(self, path: Path) -> int:
        """Tính kích thước thư mục"""
        total_size = 0
        try:
            if path.is_file():
                return path.stat().st_size
            elif path.is_dir():
                for file_path in path.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
        except (OSError, PermissionError):
            pass
        return total_size

    def get_file_hash(self, file_path: Path) -> str:
        """Tính hash của file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return ""

    def scan_backup_targets(self) -> Dict[str, Any]:
        """Quét các target backup"""
        scan_results = {}

        for target_name, target_info in self.backup_targets.items():
            target_data = {
                'description': target_info['description'],
                'paths': [],
                'total_size': 0,
                'file_count': 0,
                'exists': False
            }

            for path_str in target_info['paths']:
                path = Path(path_str)

                if path.exists():
                    target_data['exists'] = True
                    size = self.calculate_directory_size(path)

                    file_count = 0
                    if path.is_file():
                        file_count = 1
                    elif path.is_dir():
                        file_count = len(list(path.rglob('*')))

                    target_data['paths'].append({
                        'path': str(path),
                        'size': size,
                        'file_count': file_count,
                        'last_modified': datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                    })

                    target_data['total_size'] += size
                    target_data['file_count'] += file_count

            scan_results[target_name] = target_data

        return scan_results

    def create_backup(self, targets: List[str] = None, backup_name: str = None) -> Dict[str, Any]:
        """Tạo backup"""
        if targets is None:
            targets = list(self.backup_targets.keys())

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if backup_name is None:
            backup_name = f"clausonet_backup_{timestamp}"

        backup_file = self.backup_dir / f"{backup_name}.zip"

        self.logger.info(f"Creating backup: {backup_file}")

        backup_info = {
            'backup_name': backup_name,
            'backup_file': str(backup_file),
            'created_at': datetime.now().isoformat(),
            'targets': targets,
            'files_backed_up': [],
            'total_size': 0,
            'success': False,
            'error_message': None
        }

        try:
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add backup manifest
                manifest = {
                    'backup_name': backup_name,
                    'created_at': backup_info['created_at'],
                    'clausonet_version': '4.0.0',
                    'targets': targets,
                    'files': []
                }

                for target in targets:
                    if target not in self.backup_targets:
                        self.logger.warning(f"Unknown backup target: {target}")
                        continue

                    target_paths = self.backup_targets[target]['paths']
                    self.logger.info(f"Backing up target: {target}")

                    for path_str in target_paths:
                        path = Path(path_str)

                        if not path.exists():
                            self.logger.warning(f"Path not found: {path}")
                            continue

                        if path.is_file():
                            # Backup single file
                            archive_name = str(path)
                            zip_file.write(path, archive_name)

                            file_info = {
                                'path': str(path),
                                'archive_path': archive_name,
                                'size': path.stat().st_size,
                                'hash': self.get_file_hash(path),
                                'modified': datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                            }

                            manifest['files'].append(file_info)
                            backup_info['files_backed_up'].append(str(path))
                            backup_info['total_size'] += file_info['size']

                        elif path.is_dir():
                            # Backup directory recursively
                            for file_path in path.rglob('*'):
                                if file_path.is_file():
                                    try:
                                        # Calculate relative path for archive
                                        archive_name = str(file_path)
                                        zip_file.write(file_path, archive_name)

                                        file_info = {
                                            'path': str(file_path),
                                            'archive_path': archive_name,
                                            'size': file_path.stat().st_size,
                                            'hash': self.get_file_hash(file_path),
                                            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                                        }

                                        manifest['files'].append(file_info)
                                        backup_info['files_backed_up'].append(str(file_path))
                                        backup_info['total_size'] += file_info['size']

                                    except (OSError, PermissionError) as e:
                                        self.logger.warning(f"Could not backup file {file_path}: {e}")

                # Write manifest to backup
                manifest_json = json.dumps(manifest, indent=2)
                zip_file.writestr('backup_manifest.json', manifest_json)

            backup_info['success'] = True
            backup_info['file_count'] = len(backup_info['files_backed_up'])

            # Save backup metadata
            metadata_file = self.backup_dir / f"{backup_name}_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Backup created successfully: {backup_file}")
            self.logger.info(f"Files backed up: {backup_info['file_count']}")
            self.logger.info(f"Total size: {backup_info['total_size']} bytes")

        except Exception as e:
            backup_info['success'] = False
            backup_info['error_message'] = str(e)
            self.logger.error(f"Backup failed: {e}")

            # Clean up failed backup
            if backup_file.exists():
                backup_file.unlink()

        return backup_info

    def list_backups(self) -> List[Dict[str, Any]]:
        """Liệt kê các backup có sẵn"""
        backups = []

        for backup_file in self.backup_dir.glob("*.zip"):
            metadata_file = self.backup_dir / f"{backup_file.stem}_metadata.json"

            backup_info = {
                'backup_file': str(backup_file),
                'backup_name': backup_file.stem,
                'size': backup_file.stat().st_size,
                'created_at': datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
                'has_metadata': metadata_file.exists()
            }

            # Load metadata if available
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    backup_info.update({
                        'targets': metadata.get('targets', []),
                        'file_count': metadata.get('file_count', 0),
                        'success': metadata.get('success', False),
                        'total_size': metadata.get('total_size', 0)
                    })
                except Exception as e:
                    self.logger.warning(f"Could not load metadata for {backup_file}: {e}")

            backups.append(backup_info)

        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        return backups

    def verify_backup(self, backup_file: str) -> Dict[str, Any]:
        """Xác minh tính toàn vẹn của backup"""
        backup_path = Path(backup_file)

        if not backup_path.exists():
            return {
                'valid': False,
                'error': 'Backup file not found'
            }

        verification_result = {
            'valid': False,
            'backup_file': str(backup_path),
            'has_manifest': False,
            'file_count': 0,
            'verified_files': 0,
            'corrupted_files': [],
            'missing_files': [],
            'error': None
        }

        try:
            with zipfile.ZipFile(backup_path, 'r') as zip_file:
                # Check if manifest exists
                if 'backup_manifest.json' in zip_file.namelist():
                    verification_result['has_manifest'] = True

                    # Load manifest
                    manifest_data = zip_file.read('backup_manifest.json')
                    manifest = json.loads(manifest_data.decode('utf-8'))

                    verification_result['file_count'] = len(manifest.get('files', []))

                    # Verify each file
                    for file_info in manifest.get('files', []):
                        archive_path = file_info['archive_path']
                        expected_hash = file_info.get('hash', '')

                        if archive_path in zip_file.namelist():
                            # Extract and verify hash
                            if expected_hash:
                                try:
                                    file_data = zip_file.read(archive_path)
                                    actual_hash = hashlib.md5(file_data).hexdigest()

                                    if actual_hash == expected_hash:
                                        verification_result['verified_files'] += 1
                                    else:
                                        verification_result['corrupted_files'].append({
                                            'path': archive_path,
                                            'expected_hash': expected_hash,
                                            'actual_hash': actual_hash
                                        })
                                except Exception as e:
                                    verification_result['corrupted_files'].append({
                                        'path': archive_path,
                                        'error': str(e)
                                    })
                            else:
                                verification_result['verified_files'] += 1
                        else:
                            verification_result['missing_files'].append(archive_path)

                # Test zip integrity
                bad_files = zip_file.testzip()
                if bad_files:
                    verification_result['error'] = f"Corrupted files in archive: {bad_files}"
                elif verification_result['has_manifest']:
                    verification_result['valid'] = (
                        len(verification_result['corrupted_files']) == 0 and
                        len(verification_result['missing_files']) == 0
                    )
                else:
                    verification_result['valid'] = True  # No manifest, but zip is valid

        except Exception as e:
            verification_result['error'] = str(e)

        return verification_result

    def restore_backup(self, backup_file: str, restore_targets: List[str] = None, force: bool = False) -> Dict[str, Any]:
        """Phục hồi từ backup"""
        backup_path = Path(backup_file)

        if not backup_path.exists():
            return {
                'success': False,
                'error': 'Backup file not found'
            }

        self.logger.info(f"Restoring from backup: {backup_path}")

        restore_result = {
            'success': False,
            'backup_file': str(backup_path),
            'restored_files': [],
            'skipped_files': [],
            'failed_files': [],
            'error': None
        }

        try:
            # Verify backup first
            if not force:
                verification = self.verify_backup(backup_file)
                if not verification['valid']:
                    return {
                        'success': False,
                        'error': f"Backup verification failed: {verification.get('error', 'Unknown error')}"
                    }

            with zipfile.ZipFile(backup_path, 'r') as zip_file:
                # Load manifest if available
                manifest = None
                if 'backup_manifest.json' in zip_file.namelist():
                    manifest_data = zip_file.read('backup_manifest.json')
                    manifest = json.loads(manifest_data.decode('utf-8'))

                files_to_restore = zip_file.namelist()

                # Filter by restore targets if specified
                if restore_targets and manifest:
                    files_to_restore = []
                    for file_info in manifest.get('files', []):
                        # Check if file belongs to any of the restore targets
                        file_path = file_info['path']
                        for target in restore_targets:
                            if target in self.backup_targets:
                                target_paths = self.backup_targets[target]['paths']
                                for target_path in target_paths:
                                    if file_path.startswith(target_path):
                                        files_to_restore.append(file_info['archive_path'])
                                        break

                # Restore files
                for archive_path in files_to_restore:
                    if archive_path == 'backup_manifest.json':
                        continue  # Skip manifest

                    try:
                        # Extract file
                        zip_file.extract(archive_path, '.')
                        restore_result['restored_files'].append(archive_path)

                    except Exception as e:
                        self.logger.warning(f"Failed to restore {archive_path}: {e}")
                        restore_result['failed_files'].append({
                            'path': archive_path,
                            'error': str(e)
                        })

            restore_result['success'] = True
            self.logger.info(f"Restore completed. Files restored: {len(restore_result['restored_files'])}")

        except Exception as e:
            restore_result['error'] = str(e)
            self.logger.error(f"Restore failed: {e}")

        return restore_result

    def auto_backup(self, targets: List[str] = None) -> Dict[str, Any]:
        """Tự động backup theo lịch"""
        if targets is None:
            targets = ['config', 'user_data']  # Backup important data only

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"auto_backup_{timestamp}"

        self.logger.info("Running automatic backup...")
        result = self.create_backup(targets, backup_name)

        # Clean up old auto backups (keep last 10)
        self.cleanup_old_backups(prefix="auto_backup_", keep_count=10)

        return result

    def cleanup_old_backups(self, prefix: str = "", keep_count: int = 5) -> int:
        """Dọn dẹp backup cũ"""
        backups = self.list_backups()

        # Filter by prefix
        if prefix:
            filtered_backups = [b for b in backups if b['backup_name'].startswith(prefix)]
        else:
            filtered_backups = backups

        # Sort by creation date and keep only the newest ones
        filtered_backups.sort(key=lambda x: x['created_at'], reverse=True)

        removed_count = 0
        for backup in filtered_backups[keep_count:]:
            try:
                # Remove backup file
                backup_file = Path(backup['backup_file'])
                if backup_file.exists():
                    backup_file.unlink()

                # Remove metadata file
                metadata_file = Path(backup['backup_file']).parent / f"{backup['backup_name']}_metadata.json"
                if metadata_file.exists():
                    metadata_file.unlink()

                removed_count += 1
                self.logger.info(f"Removed old backup: {backup['backup_name']}")

            except Exception as e:
                self.logger.warning(f"Failed to remove backup {backup['backup_name']}: {e}")

        return removed_count

    def generate_backup_report(self, backups: List[Dict[str, Any]], format: str = 'text') -> str:
        """Tạo báo cáo backup"""
        if format == 'json':
            return json.dumps(backups, indent=2, ensure_ascii=False)

        # Text format report
        report = []
        report.append("=" * 60)
        report.append("ClausoNet 4.0 Pro - Backup Report")
        report.append("=" * 60)
        report.append(f"Total Backups: {len(backups)}")
        report.append("")

        if not backups:
            report.append("No backups found.")
            return "\n".join(report)

        # Calculate statistics
        total_size = sum(b.get('total_size', 0) for b in backups)
        successful_backups = len([b for b in backups if b.get('success', True)])

        report.append("SUMMARY:")
        report.append(f"  Successful Backups: {successful_backups}/{len(backups)}")
        report.append(f"  Total Size: {total_size / (1024*1024):.1f} MB")
        report.append("")

        # List backups
        report.append("BACKUP LIST:")
        report.append("-" * 40)

        for backup in backups:
            status = "✓" if backup.get('success', True) else "✗"
            size_mb = backup.get('total_size', backup.get('size', 0)) / (1024*1024)

            report.append(f"{status} {backup['backup_name']}")
            report.append(f"    Created: {backup['created_at']}")
            report.append(f"    Size: {size_mb:.1f} MB")

            if 'targets' in backup:
                report.append(f"    Targets: {', '.join(backup['targets'])}")

            if 'file_count' in backup:
                report.append(f"    Files: {backup['file_count']}")

            report.append("")

        report.append("=" * 60)
        return "\n".join(report)

def main():
    """Hàm main để chạy từ command line"""
    import argparse

    parser = argparse.ArgumentParser(description='ClausoNet 4.0 Pro Backup Tool')
    parser.add_argument('--create', action='store_true',
                       help='Create new backup')
    parser.add_argument('--restore', metavar='BACKUP_FILE',
                       help='Restore from backup file')
    parser.add_argument('--list', action='store_true',
                       help='List available backups')
    parser.add_argument('--verify', metavar='BACKUP_FILE',
                       help='Verify backup integrity')
    parser.add_argument('--auto', action='store_true',
                       help='Run automatic backup')
    parser.add_argument('--cleanup', type=int, metavar='KEEP_COUNT',
                       help='Clean up old backups, keeping specified number')
    parser.add_argument('--targets', nargs='+',
                       choices=['config', 'user_data', 'cache', 'logs', 'outputs'],
                       help='Backup/restore targets')
    parser.add_argument('--name', help='Backup name')
    parser.add_argument('--force', action='store_true',
                       help='Force operation without verification')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='Output format')

    args = parser.parse_args()

    tool = BackupTool()

    try:
        if args.create:
            print("Creating backup...")
            result = tool.create_backup(args.targets, args.name)
            if result['success']:
                print(f"✓ Backup created: {result['backup_file']}")
                print(f"  Files: {result['file_count']}")
                print(f"  Size: {result['total_size'] / (1024*1024):.1f} MB")
            else:
                print(f"✗ Backup failed: {result['error_message']}")
                sys.exit(1)

        elif args.restore:
            print(f"Restoring from: {args.restore}")
            result = tool.restore_backup(args.restore, args.targets, args.force)
            if result['success']:
                print(f"✓ Restore completed")
                print(f"  Files restored: {len(result['restored_files'])}")
                if result['failed_files']:
                    print(f"  Failed files: {len(result['failed_files'])}")
            else:
                print(f"✗ Restore failed: {result['error']}")
                sys.exit(1)

        elif args.verify:
            print(f"Verifying backup: {args.verify}")
            result = tool.verify_backup(args.verify)
            if result['valid']:
                print("✓ Backup is valid")
                print(f"  Files verified: {result['verified_files']}/{result['file_count']}")
            else:
                print("✗ Backup verification failed")
                if result['error']:
                    print(f"  Error: {result['error']}")
                if result['corrupted_files']:
                    print(f"  Corrupted files: {len(result['corrupted_files'])}")
                if result['missing_files']:
                    print(f"  Missing files: {len(result['missing_files'])}")
                sys.exit(1)

        elif args.list:
            backups = tool.list_backups()
            report = tool.generate_backup_report(backups, args.format)
            print(report)

        elif args.auto:
            print("Running automatic backup...")
            result = tool.auto_backup(args.targets)
            if result['success']:
                print(f"✓ Auto backup completed: {result['backup_name']}")
            else:
                print(f"✗ Auto backup failed: {result['error_message']}")
                sys.exit(1)

        elif args.cleanup is not None:
            print(f"Cleaning up old backups (keeping {args.cleanup})...")
            removed = tool.cleanup_old_backups(keep_count=args.cleanup)
            print(f"✓ Removed {removed} old backups")

        else:
            # Show scan results
            print("ClausoNet 4.0 Pro - Backup Tool")
            print("Scanning backup targets...")
            print("")

            scan_results = tool.scan_backup_targets()

            for target, info in scan_results.items():
                status = "✓" if info['exists'] else "✗"
                size_mb = info['total_size'] / (1024*1024)

                print(f"{status} {target.upper()}: {info['description']}")
                print(f"    Size: {size_mb:.1f} MB")
                print(f"    Files: {info['file_count']}")
                print("")

            parser.print_help()

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
