#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - License Manager
Quản lý license và xác thực người dùng
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

class LicenseManager:
    """Quản lý license cho ClausoNet 4.0 Pro"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('LicenseManager')
        self.license_path = Path("./license/clausonet.lic")
        
        # Tạo thư mục license nếu chưa có
        self.license_path.parent.mkdir(exist_ok=True)
    
    def validate_license(self) -> bool:
        """Kiểm tra license có hợp lệ không"""
        try:
            if not self.license_path.exists():
                self.logger.error("License file not found")
                return False
            
            # Load license data
            license_data = self._load_license()
            if not license_data:
                return False
            
            # Kiểm tra expiry date
            expiry_date = datetime.fromisoformat(license_data.get('expiry_date', ''))
            if datetime.utcnow() > expiry_date:
                self.logger.error("License expired")
                return False
            
            # Kiểm tra hardware binding
            if not self._verify_hardware_binding(license_data):
                self.logger.error("Hardware binding verification failed")
                return False
            
            self.logger.info("License validation successful")
            return True
            
        except Exception as e:
            self.logger.error(f"License validation failed: {e}")
            return False
    
    def get_license_status(self) -> Dict[str, Any]:
        """Lấy trạng thái license hiện tại"""
        if not self.license_path.exists():
            return {'status': 'not_activated', 'message': 'No license found'}
        
        try:
            license_data = self._load_license()
            if not license_data:
                return {'status': 'invalid', 'message': 'Cannot read license'}
            
            expiry_date = datetime.fromisoformat(license_data.get('expiry_date', ''))
            days_until_expiry = (expiry_date - datetime.utcnow()).days
            
            if self.validate_license():
                return {
                    'status': 'active',
                    'customer_key': license_data.get('customer_key', ''),
                    'expiry_date': license_data.get('expiry_date', ''),
                    'days_until_expiry': days_until_expiry,
                    'license_type': license_data.get('license_type', 'Pro')
                }
            else:
                return {'status': 'invalid', 'message': 'License validation failed'}
                
        except Exception as e:
            self.logger.error(f"Failed to get license status: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _load_license(self) -> Optional[Dict[str, Any]]:
        """Load license data từ file"""
        try:
            with open(self.license_path, 'r') as f:
                # Thực tế sẽ decrypt license file
                # Hiện tại giả lập load JSON
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load license: {e}")
            return None
    
    def _verify_hardware_binding(self, license_data: Dict[str, Any]) -> bool:
        """Kiểm tra hardware binding"""
        # Thực tế sẽ so sánh với hardware fingerprint
        # Hiện tại return True để test
        return True 