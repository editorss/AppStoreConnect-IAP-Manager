#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理 - 保存和加载应用配置
"""

import json
import os
from typing import Optional, Dict, Any
from PyQt6.QtCore import QSettings


class ConfigManager:
    """配置管理器"""
    
    # 配置键常量
    KEY_AUTH_KEY_ID = "auth/key_id"
    KEY_AUTH_ISSUER_ID = "auth/issuer_id"
    KEY_AUTH_PRIVATE_KEY = "auth/private_key"
    KEY_WINDOW_GEOMETRY = "window/geometry"
    KEY_WINDOW_STATE = "window/state"
    KEY_LAST_TAB = "ui/last_tab"
    KEY_EXCLUDE_CHINA = "batch/exclude_china"
    KEY_LAST_SCREENSHOT_PATH = "batch/last_screenshot_path"
    
    def __init__(self):
        """初始化配置管理器"""
        self.settings = QSettings("AppStoreConnectTool", "IAPManager")
    
    # ============ 认证配置 ============
    
    def save_auth_config(self, key_id: str, issuer_id: str, private_key: str) -> None:
        """保存认证配置"""
        self.settings.setValue(self.KEY_AUTH_KEY_ID, key_id)
        self.settings.setValue(self.KEY_AUTH_ISSUER_ID, issuer_id)
        self.settings.setValue(self.KEY_AUTH_PRIVATE_KEY, private_key)
    
    def load_auth_config(self) -> tuple:
        """
        加载认证配置
        
        Returns:
            (key_id, issuer_id, private_key)
        """
        key_id = self.settings.value(self.KEY_AUTH_KEY_ID, "")
        issuer_id = self.settings.value(self.KEY_AUTH_ISSUER_ID, "")
        private_key = self.settings.value(self.KEY_AUTH_PRIVATE_KEY, "")
        return key_id, issuer_id, private_key
    
    def clear_auth_config(self) -> None:
        """清除认证配置"""
        self.settings.remove(self.KEY_AUTH_KEY_ID)
        self.settings.remove(self.KEY_AUTH_ISSUER_ID)
        self.settings.remove(self.KEY_AUTH_PRIVATE_KEY)
    
    def has_auth_config(self) -> bool:
        """检查是否有保存的认证配置"""
        key_id, issuer_id, private_key = self.load_auth_config()
        return bool(key_id and issuer_id and private_key)
    
    # ============ 窗口配置 ============
    
    def save_window_geometry(self, geometry: bytes) -> None:
        """保存窗口几何信息"""
        self.settings.setValue(self.KEY_WINDOW_GEOMETRY, geometry)
    
    def load_window_geometry(self) -> Optional[bytes]:
        """加载窗口几何信息"""
        return self.settings.value(self.KEY_WINDOW_GEOMETRY)
    
    def save_window_state(self, state: bytes) -> None:
        """保存窗口状态"""
        self.settings.setValue(self.KEY_WINDOW_STATE, state)
    
    def load_window_state(self) -> Optional[bytes]:
        """加载窗口状态"""
        return self.settings.value(self.KEY_WINDOW_STATE)
    
    def save_last_tab(self, index: int) -> None:
        """保存上次选中的标签页"""
        self.settings.setValue(self.KEY_LAST_TAB, index)
    
    def load_last_tab(self) -> int:
        """加载上次选中的标签页"""
        return self.settings.value(self.KEY_LAST_TAB, 0, type=int)
    
    # ============ 批量操作配置 ============
    
    def save_exclude_china(self, exclude: bool) -> None:
        """保存是否排除中国大陆和港澳台"""
        self.settings.setValue(self.KEY_EXCLUDE_CHINA, exclude)
    
    def load_exclude_china(self) -> bool:
        """加载是否排除中国大陆和港澳台"""
        return self.settings.value(self.KEY_EXCLUDE_CHINA, True, type=bool)
    
    def save_last_screenshot_path(self, path: str) -> None:
        """保存上次选择的截图路径"""
        self.settings.setValue(self.KEY_LAST_SCREENSHOT_PATH, path)
    
    def load_last_screenshot_path(self) -> str:
        """加载上次选择的截图路径"""
        return self.settings.value(self.KEY_LAST_SCREENSHOT_PATH, "")
    
    # ============ 通用方法 ============
    
    def set_value(self, key: str, value: Any) -> None:
        """设置配置值"""
        self.settings.setValue(key, value)
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.settings.value(key, default)
    
    def remove_value(self, key: str) -> None:
        """移除配置值"""
        self.settings.remove(key)
    
    def clear_all(self) -> None:
        """清除所有配置"""
        self.settings.clear()
    
    def sync(self) -> None:
        """同步配置到存储"""
        self.settings.sync()


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取配置管理器单例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
