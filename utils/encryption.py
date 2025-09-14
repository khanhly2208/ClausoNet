#!/usr/bin/env python3
"""
ClausoNet 4.0 Pro - Security Manager
Quản lý bảo mật và mã hóa cho hệ thống
"""

import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging
from typing import Dict, Any

class SecurityManager:
    """Quản lý bảo mật cho ClausoNet 4.0 Pro"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('SecurityManager')
        self.salt = b'clausonet_v4_security_salt_2024'
    
    def create_encryption_key(self, password: str) -> bytes:
        """Tạo encryption key từ password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_data(self, data: str, key: bytes) -> str:
        """Mã hóa dữ liệu"""
        cipher = Fernet(key)
        encrypted_data = cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_data(self, encrypted_data: str, key: bytes) -> str:
        """Giải mã dữ liệu"""
        cipher = Fernet(key)
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = cipher.decrypt(decoded_data)
        return decrypted_data.decode()
    
    def hash_data(self, data: str) -> str:
        """Tạo hash SHA-256"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_integrity(self, data: str, expected_hash: str) -> bool:
        """Kiểm tra tính toàn vẹn dữ liệu"""
        actual_hash = self.hash_data(data)
        return actual_hash == expected_hash 