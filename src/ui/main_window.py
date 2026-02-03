#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口 - 应用程序主界面
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QCloseEvent

from ..core.api_service import AppStoreConnectAPIService
from .auth_tab import AuthTab
from .iap_tab import IAPTab
from .batch_tab import BatchTab


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化API服务
        self.api_service = AppStoreConnectAPIService()
        
        # 初始化设置
        self.settings = QSettings("AppStoreConnectTool", "IAPManager")
        
        # 设置窗口
        self._setup_ui()
        self._load_settings()
        
    def _setup_ui(self):
        """设置用户界面"""
        # 窗口基本设置
        self.setWindowTitle("App Store Connect API 内购管理工具")
        self.setMinimumSize(1000, 700)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 标题栏
        header_layout = QHBoxLayout()
        
        title_label = QLabel("App Store Connect API 内购管理工具")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
            }
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # 状态指示器
        self.status_indicator = QLabel("● 未连接")
        self.status_indicator.setStyleSheet("color: #999;")
        header_layout.addWidget(self.status_indicator)
        
        main_layout.addLayout(header_layout)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        
        # API认证标签页
        self.auth_tab = AuthTab(self.api_service)
        self.auth_tab.connection_status_changed.connect(self._on_connection_status_changed)
        self.tab_widget.addTab(self.auth_tab, "API认证")
        
        # 内购管理标签页
        self.iap_tab = IAPTab(self.api_service)
        self.tab_widget.addTab(self.iap_tab, "内购管理")
        
        # 批量操作标签页
        self.batch_tab = BatchTab(self.api_service)
        self.tab_widget.addTab(self.batch_tab, "批量操作")
        
        main_layout.addWidget(self.tab_widget)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
    def _on_connection_status_changed(self, connected: bool, message: str):
        """连接状态变化处理"""
        if connected:
            self.status_indicator.setText("● 已连接")
            self.status_indicator.setStyleSheet("color: #4CAF50;")
            self.status_bar.showMessage(message)
            # 刷新其他标签页的数据
            self.iap_tab.refresh_apps()
            self.batch_tab.refresh_apps()
        else:
            self.status_indicator.setText("● 未连接")
            self.status_indicator.setStyleSheet("color: #f44336;")
            self.status_bar.showMessage(message)
    
    def _load_settings(self):
        """加载设置"""
        # 恢复窗口大小和位置
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # 默认居中显示
            self.resize(1200, 800)
            screen = self.screen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
        
        # 恢复上次的标签页
        last_tab = self.settings.value("last_tab", 0, type=int)
        if 0 <= last_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(last_tab)
    
    def _save_settings(self):
        """保存设置"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("last_tab", self.tab_widget.currentIndex())
    
    def closeEvent(self, event: QCloseEvent):
        """窗口关闭事件"""
        self._save_settings()
        event.accept()
