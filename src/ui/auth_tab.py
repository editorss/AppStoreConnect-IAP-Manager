#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API认证标签页 - 配置App Store Connect API认证信息
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QFileDialog,
    QGroupBox, QMessageBox, QProgressDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QThread, pyqtSlot
from PyQt6.QtGui import QFont

from ..core.api_service import AppStoreConnectAPIService
from ..core.jwt_authenticator import JWTAuthenticator


class ConnectionTestWorker(QThread):
    """连接测试工作线程"""
    finished = pyqtSignal(bool, str)
    
    def __init__(self, api_service: AppStoreConnectAPIService):
        super().__init__()
        self.api_service = api_service
    
    def run(self):
        success, message = self.api_service.test_connection()
        self.finished.emit(success, message)


class AuthTab(QWidget):
    """API认证标签页"""
    
    # 连接状态变化信号
    connection_status_changed = pyqtSignal(bool, str)
    
    def __init__(self, api_service: AppStoreConnectAPIService):
        super().__init__()
        self.api_service = api_service
        self.settings = QSettings("AppStoreConnectTool", "IAPManager")
        self._worker = None
        
        self._setup_ui()
        self._load_saved_config()
    
    def _setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 标题
        title = QLabel("App Store Connect API 认证配置")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 说明文字
        info_label = QLabel(
            "请输入从 App Store Connect 获取的 API 密钥信息。\n"
            "前往「用户和访问」→「密钥」生成新的 API 密钥。"
        )
        info_label.setStyleSheet("color: #666;")
        layout.addWidget(info_label)
        
        # 认证配置表单
        config_group = QGroupBox("认证信息")
        config_layout = QFormLayout(config_group)
        config_layout.setSpacing(15)
        
        # Key ID
        self.key_id_input = QLineEdit()
        self.key_id_input.setPlaceholderText("10位大写字母数字，如：ABC1234567")
        self.key_id_input.setMaxLength(10)
        config_layout.addRow("Key ID:", self.key_id_input)
        
        # Issuer ID
        self.issuer_id_input = QLineEdit()
        self.issuer_id_input.setPlaceholderText("UUID格式，如：xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        config_layout.addRow("Issuer ID:", self.issuer_id_input)
        
        # 私钥
        key_layout = QVBoxLayout()
        
        key_header = QHBoxLayout()
        key_label = QLabel("私钥 (.p8文件):")
        key_header.addWidget(key_label)
        
        self.import_key_btn = QPushButton("导入.p8文件")
        self.import_key_btn.clicked.connect(self._import_private_key)
        key_header.addWidget(self.import_key_btn)
        key_header.addStretch()
        
        key_layout.addLayout(key_header)
        
        self.private_key_input = QTextEdit()
        self.private_key_input.setPlaceholderText("-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----")
        self.private_key_input.setMaximumHeight(150)
        self.private_key_input.setStyleSheet("font-family: monospace;")
        key_layout.addWidget(self.private_key_input)
        
        self.key_status_label = QLabel("")
        self.key_status_label.setStyleSheet("color: #666; font-size: 12px;")
        key_layout.addWidget(self.key_status_label)
        
        config_layout.addRow(key_layout)
        
        layout.addWidget(config_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("保存配置")
        self.save_btn.clicked.connect(self._save_config)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        button_layout.addWidget(self.save_btn)
        
        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self._test_connection)
        self.test_btn.setEnabled(False)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        button_layout.addWidget(self.test_btn)
        
        self.clear_btn = QPushButton("清除配置")
        self.clear_btn.clicked.connect(self._clear_config)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        button_layout.addWidget(self.clear_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 状态显示
        status_group = QGroupBox("连接状态")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("未连接")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 4px;
                color: #666;
            }
        """)
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_group)
        
        layout.addStretch()
        
        # 监听输入变化
        self.key_id_input.textChanged.connect(self._on_input_changed)
        self.issuer_id_input.textChanged.connect(self._on_input_changed)
        self.private_key_input.textChanged.connect(self._on_input_changed)
    
    def _on_input_changed(self):
        """输入变化时更新状态"""
        key_id = self.key_id_input.text().strip()
        issuer_id = self.issuer_id_input.text().strip()
        private_key = self.private_key_input.toPlainText().strip()
        
        # 更新私钥状态
        if private_key:
            if "-----BEGIN PRIVATE KEY-----" in private_key and "-----END PRIVATE KEY-----" in private_key:
                self.key_status_label.setText("✓ 检测到PEM格式私钥")
                self.key_status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
            else:
                self.key_status_label.setText("⚠ 私钥格式可能不正确")
                self.key_status_label.setStyleSheet("color: #FF9800; font-size: 12px;")
        else:
            self.key_status_label.setText("")
    
    def _import_private_key(self):
        """导入私钥文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择.p8私钥文件",
            "",
            "Private Key Files (*.p8);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.private_key_input.setPlainText(content)
                QMessageBox.information(self, "成功", "私钥文件导入成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"读取私钥文件失败：{str(e)}")
    
    def _save_config(self):
        """保存配置"""
        key_id = self.key_id_input.text().strip()
        issuer_id = self.issuer_id_input.text().strip()
        private_key = self.private_key_input.toPlainText().strip()
        
        # 验证配置
        valid, msg = JWTAuthenticator.validate_all(key_id, issuer_id, private_key)
        if not valid:
            QMessageBox.warning(self, "验证失败", msg)
            return
        
        # 配置认证
        success, error_msg = self.api_service.configure_authentication(
            key_id, issuer_id, private_key
        )
        
        if success:
            # 保存到设置
            self.settings.setValue("auth/key_id", key_id)
            self.settings.setValue("auth/issuer_id", issuer_id)
            self.settings.setValue("auth/private_key", private_key)
            
            self.test_btn.setEnabled(True)
            self._update_status("已配置", "#2196F3")
            QMessageBox.information(self, "成功", "认证配置保存成功！\n请点击「测试连接」验证配置。")
        else:
            QMessageBox.critical(self, "配置失败", error_msg)
    
    def _test_connection(self):
        """测试连接"""
        self.test_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self._update_status("正在测试连接...", "#FF9800")
        
        # 使用工作线程避免UI卡顿
        self._worker = ConnectionTestWorker(self.api_service)
        self._worker.finished.connect(self._on_test_finished)
        self._worker.start()
    
    @pyqtSlot(bool, str)
    def _on_test_finished(self, success: bool, message: str):
        """测试完成回调"""
        self.test_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        
        if success:
            self._update_status("连接成功 ✓", "#4CAF50")
            self.connection_status_changed.emit(True, "API连接成功")
            QMessageBox.information(self, "成功", "API连接测试成功！")
        else:
            self._update_status(f"连接失败: {message}", "#f44336")
            self.connection_status_changed.emit(False, message)
            QMessageBox.critical(self, "连接失败", message)
    
    def _clear_config(self):
        """清除配置"""
        reply = QMessageBox.question(
            self, "确认",
            "确定要清除所有认证配置吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.key_id_input.clear()
            self.issuer_id_input.clear()
            self.private_key_input.clear()
            
            self.settings.remove("auth/key_id")
            self.settings.remove("auth/issuer_id")
            self.settings.remove("auth/private_key")
            
            self.test_btn.setEnabled(False)
            self._update_status("配置已清除", "#666")
            self.connection_status_changed.emit(False, "配置已清除")
    
    def _load_saved_config(self):
        """加载保存的配置"""
        key_id = self.settings.value("auth/key_id", "")
        issuer_id = self.settings.value("auth/issuer_id", "")
        private_key = self.settings.value("auth/private_key", "")
        
        if key_id and issuer_id and private_key:
            self.key_id_input.setText(key_id)
            self.issuer_id_input.setText(issuer_id)
            self.private_key_input.setPlainText(private_key)
            
            # 自动配置认证
            success, _ = self.api_service.configure_authentication(
                key_id, issuer_id, private_key
            )
            if success:
                self.test_btn.setEnabled(True)
                self._update_status("已加载保存的配置", "#2196F3")
    
    def _update_status(self, text: str, color: str):
        """更新状态显示"""
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 4px;
                color: {color};
                font-weight: bold;
            }}
        """)
