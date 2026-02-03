#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JWT认证器 - 用于生成App Store Connect API所需的JWT令牌
使用ES256算法（P-256椭圆曲线）进行签名
"""

import time
import jwt
from typing import Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


class JWTAuthenticator:
    """JWT认证器类"""
    
    def __init__(self, key_id: str, issuer_id: str, private_key: str):
        """
        初始化JWT认证器
        
        Args:
            key_id: API Key ID（10位大写字母数字）
            issuer_id: Issuer ID（UUID格式）
            private_key: .p8私钥文件内容（PEM格式）
        """
        self.key_id = key_id
        self.issuer_id = issuer_id
        self.private_key = private_key
        self._parsed_key = None
        
    def _parse_private_key(self):
        """解析PEM格式的私钥"""
        if self._parsed_key is not None:
            return self._parsed_key
            
        try:
            # 清理私钥内容
            key_content = self.private_key.strip()
            
            # 确保私钥格式正确
            if not key_content.startswith("-----BEGIN"):
                raise ValueError("私钥格式错误：缺少BEGIN标记")
            if not key_content.endswith("-----"):
                raise ValueError("私钥格式错误：缺少END标记")
            
            # 解析私钥
            self._parsed_key = serialization.load_pem_private_key(
                key_content.encode('utf-8'),
                password=None,
                backend=default_backend()
            )
            
            return self._parsed_key
            
        except Exception as e:
            raise ValueError(f"私钥解析失败: {str(e)}")
    
    def generate_jwt(self) -> str:
        """
        生成JWT令牌
        
        Returns:
            用于API请求的JWT令牌字符串
            
        Raises:
            ValueError: 私钥解析失败时抛出
        """
        # 解析私钥
        private_key = self._parse_private_key()
        
        # 当前时间和过期时间（20分钟有效期）
        current_time = int(time.time())
        expiration_time = current_time + (20 * 60)  # 20分钟
        
        # JWT头部
        headers = {
            "alg": "ES256",
            "kid": self.key_id,
            "typ": "JWT"
        }
        
        # JWT载荷
        payload = {
            "iss": self.issuer_id,
            "iat": current_time,
            "exp": expiration_time,
            "aud": "appstoreconnect-v1"
        }
        
        # 生成JWT令牌
        token = jwt.encode(
            payload,
            private_key,
            algorithm="ES256",
            headers=headers
        )
        
        return token
    
    @staticmethod
    def validate_key_id(key_id: str) -> tuple[bool, str]:
        """
        验证Key ID格式
        
        Args:
            key_id: 要验证的Key ID
            
        Returns:
            (是否有效, 错误信息)
        """
        import re
        
        if not key_id:
            return False, "Key ID不能为空"
        
        # Key ID必须是10个大写字母和数字
        pattern = r'^[A-Z0-9]{10}$'
        if not re.match(pattern, key_id):
            return False, "Key ID格式错误：必须是10个大写字母和数字（如：ABC1234567）"
        
        return True, ""
    
    @staticmethod
    def validate_issuer_id(issuer_id: str) -> tuple[bool, str]:
        """
        验证Issuer ID格式
        
        Args:
            issuer_id: 要验证的Issuer ID
            
        Returns:
            (是否有效, 错误信息)
        """
        import re
        
        if not issuer_id:
            return False, "Issuer ID不能为空"
        
        # Issuer ID必须是UUID格式
        pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
        if not re.match(pattern, issuer_id):
            return False, "Issuer ID格式错误：必须是UUID格式（xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx）"
        
        return True, ""
    
    @staticmethod
    def validate_private_key(private_key: str) -> tuple[bool, str]:
        """
        验证私钥格式
        
        Args:
            private_key: 要验证的私钥内容
            
        Returns:
            (是否有效, 错误信息)
        """
        if not private_key:
            return False, "私钥不能为空"
        
        if "-----BEGIN PRIVATE KEY-----" not in private_key:
            return False, "私钥格式错误：缺少BEGIN PRIVATE KEY标记"
        
        if "-----END PRIVATE KEY-----" not in private_key:
            return False, "私钥格式错误：缺少END PRIVATE KEY标记"
        
        # 尝试解析私钥
        try:
            serialization.load_pem_private_key(
                private_key.strip().encode('utf-8'),
                password=None,
                backend=default_backend()
            )
        except Exception as e:
            return False, f"私钥解析失败：{str(e)}"
        
        return True, ""
    
    @classmethod
    def validate_all(cls, key_id: str, issuer_id: str, private_key: str) -> tuple[bool, str]:
        """
        验证所有认证参数
        
        Args:
            key_id: Key ID
            issuer_id: Issuer ID
            private_key: 私钥内容
            
        Returns:
            (是否全部有效, 错误信息)
        """
        # 验证Key ID
        valid, msg = cls.validate_key_id(key_id)
        if not valid:
            return False, msg
        
        # 验证Issuer ID
        valid, msg = cls.validate_issuer_id(issuer_id)
        if not valid:
            return False, msg
        
        # 验证私钥
        valid, msg = cls.validate_private_key(private_key)
        if not valid:
            return False, msg
        
        return True, ""


class JWTError(Exception):
    """JWT相关错误"""
    pass
