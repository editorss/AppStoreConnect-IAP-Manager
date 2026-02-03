#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内购管理标签页 - 管理应用的内购产品
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QPushButton, QGroupBox, QMessageBox, QHeaderView, QMenu,
    QDialog, QFormLayout, QLineEdit, QComboBox, QTextEdit, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QAction

from ..core.api_service import AppStoreConnectAPIService, APIException
from ..core.models import App, InAppPurchase, InAppPurchaseType, InAppPurchaseState


class FetchAppsWorker(QThread):
    """获取应用列表工作线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, api_service: AppStoreConnectAPIService):
        super().__init__()
        self.api_service = api_service
    
    def run(self):
        try:
            apps = self.api_service.fetch_apps()
            self.finished.emit(apps)
        except Exception as e:
            self.error.emit(str(e))


class FetchIAPsWorker(QThread):
    """获取内购产品列表工作线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, api_service: AppStoreConnectAPIService, app_id: str):
        super().__init__()
        self.api_service = api_service
        self.app_id = app_id
    
    def run(self):
        try:
            iaps = self.api_service.fetch_in_app_purchases(self.app_id)
            self.finished.emit(iaps)
        except Exception as e:
            self.error.emit(str(e))


class DeleteIAPWorker(QThread):
    """删除内购产品工作线程"""
    finished = pyqtSignal(bool, str)
    
    def __init__(self, api_service: AppStoreConnectAPIService, iap_id: str):
        super().__init__()
        self.api_service = api_service
        self.iap_id = iap_id
    
    def run(self):
        try:
            self.api_service.delete_in_app_purchase(self.iap_id)
            self.finished.emit(True, "删除成功")
        except Exception as e:
            self.finished.emit(False, str(e))


class IAPTab(QWidget):
    """内购管理标签页"""
    
    def __init__(self, api_service: AppStoreConnectAPIService):
        super().__init__()
        self.api_service = api_service
        self.apps = []
        self.iaps = []
        self.selected_app = None
        self._worker = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 使用分割器实现左右布局
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：应用列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_header = QHBoxLayout()
        apps_label = QLabel("应用列表")
        apps_label.setFont(QFont("", 12, QFont.Weight.Bold))
        left_header.addWidget(apps_label)
        
        self.refresh_apps_btn = QPushButton("刷新")
        self.refresh_apps_btn.clicked.connect(self.refresh_apps)
        left_header.addWidget(self.refresh_apps_btn)
        
        left_layout.addLayout(left_header)
        
        self.apps_list = QListWidget()
        self.apps_list.itemClicked.connect(self._on_app_selected)
        left_layout.addWidget(self.apps_list)
        
        splitter.addWidget(left_widget)
        
        # 右侧：内购产品列表
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        right_header = QHBoxLayout()
        
        self.iap_title_label = QLabel("内购产品")
        self.iap_title_label.setFont(QFont("", 12, QFont.Weight.Bold))
        right_header.addWidget(self.iap_title_label)
        
        right_header.addStretch()
        
        self.refresh_iaps_btn = QPushButton("刷新")
        self.refresh_iaps_btn.clicked.connect(self._refresh_iaps)
        self.refresh_iaps_btn.setEnabled(False)
        right_header.addWidget(self.refresh_iaps_btn)
        
        self.create_iap_btn = QPushButton("创建内购")
        self.create_iap_btn.clicked.connect(self._show_create_dialog)
        self.create_iap_btn.setEnabled(False)
        self.create_iap_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        right_header.addWidget(self.create_iap_btn)
        
        right_layout.addLayout(right_header)
        
        # 内购产品表格
        self.iaps_table = QTableWidget()
        self.iaps_table.setColumnCount(5)
        self.iaps_table.setHorizontalHeaderLabels([
            "产品ID", "名称", "类型", "状态", "操作"
        ])
        self.iaps_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.iaps_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.iaps_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.iaps_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.iaps_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.iaps_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.iaps_table.setAlternatingRowColors(True)
        self.iaps_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.iaps_table.customContextMenuRequested.connect(self._show_context_menu)
        
        right_layout.addWidget(self.iaps_table)
        
        # 状态标签
        self.status_label = QLabel("请先在「API认证」标签页完成认证配置")
        self.status_label.setStyleSheet("color: #666; padding: 10px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.status_label)
        
        splitter.addWidget(right_widget)
        
        # 设置分割比例
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
    
    def refresh_apps(self):
        """刷新应用列表"""
        if not self.api_service.is_authenticated:
            QMessageBox.warning(self, "提示", "请先完成API认证配置")
            return
        
        self.refresh_apps_btn.setEnabled(False)
        self.apps_list.clear()
        self.status_label.setText("正在加载应用列表...")
        
        self._worker = FetchAppsWorker(self.api_service)
        self._worker.finished.connect(self._on_apps_loaded)
        self._worker.error.connect(self._on_apps_error)
        self._worker.start()
    
    @pyqtSlot(list)
    def _on_apps_loaded(self, apps: list):
        """应用列表加载完成"""
        self.refresh_apps_btn.setEnabled(True)
        self.apps = apps
        self.apps_list.clear()
        
        if not apps:
            self.status_label.setText("没有找到应用")
            return
        
        for app in apps:
            item = QListWidgetItem(f"{app.name}\n{app.bundle_id}")
            item.setData(Qt.ItemDataRole.UserRole, app)
            self.apps_list.addItem(item)
        
        self.status_label.setText(f"找到 {len(apps)} 个应用，请选择一个应用查看内购产品")
    
    @pyqtSlot(str)
    def _on_apps_error(self, error: str):
        """应用列表加载失败"""
        self.refresh_apps_btn.setEnabled(True)
        self.status_label.setText(f"加载失败: {error}")
        QMessageBox.critical(self, "错误", f"获取应用列表失败：{error}")
    
    def _on_app_selected(self, item: QListWidgetItem):
        """应用被选中"""
        self.selected_app = item.data(Qt.ItemDataRole.UserRole)
        self.iap_title_label.setText(f"内购产品 - {self.selected_app.name}")
        self.refresh_iaps_btn.setEnabled(True)
        self.create_iap_btn.setEnabled(True)
        self._refresh_iaps()
    
    def _refresh_iaps(self):
        """刷新内购产品列表"""
        if not self.selected_app:
            return
        
        self.refresh_iaps_btn.setEnabled(False)
        self.iaps_table.setRowCount(0)
        self.status_label.setText("正在加载内购产品...")
        
        self._worker = FetchIAPsWorker(self.api_service, self.selected_app.id)
        self._worker.finished.connect(self._on_iaps_loaded)
        self._worker.error.connect(self._on_iaps_error)
        self._worker.start()
    
    @pyqtSlot(list)
    def _on_iaps_loaded(self, iaps: list):
        """内购产品加载完成"""
        self.refresh_iaps_btn.setEnabled(True)
        self.iaps = iaps
        self.iaps_table.setRowCount(0)
        
        if not iaps:
            self.status_label.setText("该应用暂无内购产品")
            return
        
        self.status_label.setText(f"共 {len(iaps)} 个内购产品")
        
        for iap in iaps:
            row = self.iaps_table.rowCount()
            self.iaps_table.insertRow(row)
            
            # 产品ID
            self.iaps_table.setItem(row, 0, QTableWidgetItem(iap.product_id))
            
            # 名称
            self.iaps_table.setItem(row, 1, QTableWidgetItem(iap.reference_name))
            
            # 类型
            type_item = QTableWidgetItem(iap.type.display_name)
            self.iaps_table.setItem(row, 2, type_item)
            
            # 状态
            state_item = QTableWidgetItem(iap.state.display_name)
            # 根据状态设置颜色
            if iap.state in [InAppPurchaseState.READY_FOR_SALE, InAppPurchaseState.APPROVED]:
                state_item.setForeground(QColor("#4CAF50"))
            elif iap.state in [InAppPurchaseState.REJECTED, InAppPurchaseState.REMOVED]:
                state_item.setForeground(QColor("#f44336"))
            elif iap.state in [InAppPurchaseState.WAITING_FOR_REVIEW, InAppPurchaseState.IN_REVIEW]:
                state_item.setForeground(QColor("#FF9800"))
            self.iaps_table.setItem(row, 3, state_item)
            
            # 操作按钮
            delete_btn = QPushButton("删除")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 4px 10px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            delete_btn.clicked.connect(lambda checked, i=iap: self._delete_iap(i))
            self.iaps_table.setCellWidget(row, 4, delete_btn)
    
    @pyqtSlot(str)
    def _on_iaps_error(self, error: str):
        """内购产品加载失败"""
        self.refresh_iaps_btn.setEnabled(True)
        self.status_label.setText(f"加载失败: {error}")
        QMessageBox.critical(self, "错误", f"获取内购产品失败：{error}")
    
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        row = self.iaps_table.rowAt(pos.y())
        if row < 0 or row >= len(self.iaps):
            return
        
        iap = self.iaps[row]
        
        menu = QMenu(self)
        
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self._delete_iap(iap))
        menu.addAction(delete_action)
        
        menu.exec(self.iaps_table.mapToGlobal(pos))
    
    def _delete_iap(self, iap: InAppPurchase):
        """删除内购产品"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除内购产品「{iap.reference_name}」吗？\n产品ID: {iap.product_id}\n\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._worker = DeleteIAPWorker(self.api_service, iap.id)
            self._worker.finished.connect(self._on_delete_finished)
            self._worker.start()
    
    @pyqtSlot(bool, str)
    def _on_delete_finished(self, success: bool, message: str):
        """删除完成回调"""
        if success:
            QMessageBox.information(self, "成功", "内购产品删除成功")
            self._refresh_iaps()
        else:
            QMessageBox.critical(self, "删除失败", message)
    
    def _show_create_dialog(self):
        """显示创建内购对话框"""
        from .dialogs.create_iap_dialog import CreateIAPDialog
        
        dialog = CreateIAPDialog(self.api_service, self.selected_app, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_iaps()
