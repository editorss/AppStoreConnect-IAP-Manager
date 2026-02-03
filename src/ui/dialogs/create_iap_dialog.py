#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建内购产品对话框
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QTextEdit, QCheckBox,
    QPushButton, QGroupBox, QMessageBox, QProgressDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont

from ...core.api_service import AppStoreConnectAPIService, APIException
from ...core.models import (
    App, InAppPurchaseTemplate, InAppPurchaseType,
    InAppPurchaseLocalization, COMMON_PRICES
)


class CreateIAPWorker(QThread):
    """创建内购产品工作线程"""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    
    def __init__(
        self,
        api_service: AppStoreConnectAPIService,
        app_id: str,
        template: InAppPurchaseTemplate,
        exclude_china: bool
    ):
        super().__init__()
        self.api_service = api_service
        self.app_id = app_id
        self.template = template
        self.exclude_china = exclude_china
    
    def run(self):
        try:
            # 步骤1: 创建内购产品
            self.progress.emit("正在创建内购产品...")
            iap = self.api_service.create_in_app_purchase(self.app_id, self.template)
            
            # 步骤2: 设置价格
            self.progress.emit("正在设置价格...")
            price_points = self.api_service.fetch_price_points(iap.id)
            matching_point = self.api_service.find_matching_price_point(
                self.template.price, price_points
            )
            if matching_point:
                self.api_service.create_price_schedule(iap.id, matching_point.id)
            
            # 步骤3: 创建本地化信息
            self.progress.emit("正在创建本地化信息...")
            for loc in self.template.localizations:
                self.api_service.create_localization(iap.id, loc)
            
            # 步骤4: 设置销售范围
            self.progress.emit("正在设置销售范围...")
            self.api_service.create_availability(iap.id, self.exclude_china)
            
            self.finished.emit(True, "内购产品创建成功！")
            
        except Exception as e:
            self.finished.emit(False, str(e))


class CreateIAPDialog(QDialog):
    """创建内购产品对话框"""
    
    def __init__(
        self,
        api_service: AppStoreConnectAPIService,
        app: App,
        parent=None
    ):
        super().__init__(parent)
        self.api_service = api_service
        self.app = app
        self._worker = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle(f"创建内购产品 - {self.app.name}")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)
        
        # 产品ID
        self.product_id_input = QLineEdit()
        self.product_id_input.setPlaceholderText("例如：com.app.coins_100")
        basic_layout.addRow("产品ID:", self.product_id_input)
        
        # 显示名称
        self.display_name_input = QLineEdit()
        self.display_name_input.setPlaceholderText("例如：100金币")
        basic_layout.addRow("显示名称:", self.display_name_input)
        
        # 描述
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("内购产品描述...")
        self.description_input.setMaximumHeight(80)
        basic_layout.addRow("描述:", self.description_input)
        
        # 类型
        self.type_combo = QComboBox()
        for iap_type in InAppPurchaseType:
            self.type_combo.addItem(iap_type.display_name, iap_type)
        basic_layout.addRow("类型:", self.type_combo)
        
        # 价格
        price_layout = QHBoxLayout()
        self.price_combo = QComboBox()
        self.price_combo.setEditable(True)
        for price in COMMON_PRICES:
            self.price_combo.addItem(f"${price}", price)
        price_layout.addWidget(self.price_combo)
        price_layout.addWidget(QLabel("美元"))
        basic_layout.addRow("价格:", price_layout)
        
        layout.addWidget(basic_group)
        
        # 选项
        options_group = QGroupBox("选项")
        options_layout = QVBoxLayout(options_group)
        
        self.family_share_check = QCheckBox("启用家庭共享")
        options_layout.addWidget(self.family_share_check)
        
        self.exclude_china_check = QCheckBox("去除中国大陆和港澳台销售")
        self.exclude_china_check.setChecked(True)
        options_layout.addWidget(self.exclude_china_check)
        
        layout.addWidget(options_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.create_btn = QPushButton("创建")
        self.create_btn.clicked.connect(self._create_iap)
        self.create_btn.setStyleSheet("""
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
        button_layout.addWidget(self.create_btn)
        
        layout.addLayout(button_layout)
        
        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)
    
    def _create_iap(self):
        """创建内购产品"""
        # 验证输入
        product_id = self.product_id_input.text().strip()
        display_name = self.display_name_input.text().strip()
        description = self.description_input.toPlainText().strip()
        
        if not product_id:
            QMessageBox.warning(self, "验证失败", "请输入产品ID")
            return
        
        if not display_name:
            QMessageBox.warning(self, "验证失败", "请输入显示名称")
            return
        
        if not description:
            description = display_name  # 默认使用显示名称作为描述
        
        # 获取价格
        price = self.price_combo.currentData()
        if not price:
            price = self.price_combo.currentText().replace("$", "").strip()
        
        # 构建模板
        template = InAppPurchaseTemplate(
            product_id=product_id,
            reference_name=display_name,
            type=self.type_combo.currentData(),
            display_name=display_name,
            description=description,
            price=price,
            family_shareable=self.family_share_check.isChecked(),
            localizations=[
                InAppPurchaseLocalization(
                    locale="en-US",
                    name=display_name,
                    description=description
                )
            ]
        )
        
        # 禁用按钮
        self.create_btn.setEnabled(False)
        self.status_label.setText("正在创建...")
        
        # 启动工作线程
        self._worker = CreateIAPWorker(
            self.api_service,
            self.app.id,
            template,
            self.exclude_china_check.isChecked()
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()
    
    @pyqtSlot(str)
    def _on_progress(self, message: str):
        """进度更新"""
        self.status_label.setText(message)
    
    @pyqtSlot(bool, str)
    def _on_finished(self, success: bool, message: str):
        """创建完成"""
        self.create_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "成功", message)
            self.accept()
        else:
            self.status_label.setText(f"创建失败: {message}")
            QMessageBox.critical(self, "创建失败", message)
