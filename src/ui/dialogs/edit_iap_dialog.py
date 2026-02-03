#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编辑内购产品对话框
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QCheckBox, QPushButton, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont

from ...core.api_service import AppStoreConnectAPIService
from ...core.models import InAppPurchase


class UpdateIAPWorker(QThread):
    """更新内购产品工作线程"""
    finished = pyqtSignal(bool, str)
    
    def __init__(
        self,
        api_service: AppStoreConnectAPIService,
        iap_id: str,
        reference_name: str,
        family_shareable: bool
    ):
        super().__init__()
        self.api_service = api_service
        self.iap_id = iap_id
        self.reference_name = reference_name
        self.family_shareable = family_shareable
    
    def run(self):
        try:
            self.api_service.update_in_app_purchase(
                self.iap_id,
                self.reference_name,
                self.family_shareable
            )
            self.finished.emit(True, "更新成功")
        except Exception as e:
            self.finished.emit(False, str(e))


class EditIAPDialog(QDialog):
    """编辑内购产品对话框"""
    
    def __init__(
        self,
        api_service: AppStoreConnectAPIService,
        iap: InAppPurchase,
        parent=None
    ):
        super().__init__(parent)
        self.api_service = api_service
        self.iap = iap
        self._worker = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle(f"编辑内购产品 - {self.iap.product_id}")
        self.setMinimumWidth(450)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 产品信息（只读）
        info_group = QGroupBox("产品信息")
        info_layout = QFormLayout(info_group)
        
        product_id_label = QLabel(self.iap.product_id)
        product_id_label.setStyleSheet("color: #666;")
        info_layout.addRow("产品ID:", product_id_label)
        
        type_label = QLabel(self.iap.type.display_name)
        type_label.setStyleSheet("color: #666;")
        info_layout.addRow("类型:", type_label)
        
        state_label = QLabel(self.iap.state.display_name)
        state_label.setStyleSheet("color: #666;")
        info_layout.addRow("状态:", state_label)
        
        layout.addWidget(info_group)
        
        # 可编辑信息
        edit_group = QGroupBox("编辑信息")
        edit_layout = QFormLayout(edit_group)
        
        # 引用名称
        self.reference_name_input = QLineEdit(self.iap.reference_name)
        edit_layout.addRow("引用名称:", self.reference_name_input)
        
        # 家庭共享
        self.family_share_check = QCheckBox("启用家庭共享")
        self.family_share_check.setChecked(self.iap.family_shareable)
        edit_layout.addRow(self.family_share_check)
        
        layout.addWidget(edit_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._save)
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
        
        layout.addLayout(button_layout)
        
        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)
    
    def _save(self):
        """保存更改"""
        reference_name = self.reference_name_input.text().strip()
        
        if not reference_name:
            QMessageBox.warning(self, "验证失败", "请输入引用名称")
            return
        
        self.save_btn.setEnabled(False)
        self.status_label.setText("正在保存...")
        
        self._worker = UpdateIAPWorker(
            self.api_service,
            self.iap.id,
            reference_name,
            self.family_share_check.isChecked()
        )
        self._worker.finished.connect(self._on_finished)
        self._worker.start()
    
    @pyqtSlot(bool, str)
    def _on_finished(self, success: bool, message: str):
        """保存完成"""
        self.save_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "成功", "内购产品更新成功")
            self.accept()
        else:
            self.status_label.setText(f"保存失败: {message}")
            QMessageBox.critical(self, "保存失败", message)
