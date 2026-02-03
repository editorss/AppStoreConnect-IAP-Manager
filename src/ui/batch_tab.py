#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量操作标签页 - 批量创建内购产品
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QCheckBox, QGroupBox, QMessageBox, QFileDialog, QHeaderView,
    QProgressBar, QTextEdit, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QColor

from ..core.api_service import AppStoreConnectAPIService, APIException
from ..core.models import (
    App, BatchProduct, InAppPurchaseTemplate, InAppPurchaseType,
    InAppPurchaseLocalization, BatchOperationResult, COMMON_PRICES
)


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


class BatchCreateWorker(QThread):
    """批量创建工作线程"""
    progress = pyqtSignal(int, int, str)  # current, total, message
    result = pyqtSignal(object)  # BatchOperationResult
    finished = pyqtSignal(int, int)  # success_count, fail_count
    
    def __init__(
        self,
        api_service: AppStoreConnectAPIService,
        app_id: str,
        products: list,
        exclude_china: bool,
        screenshot_path: str = None
    ):
        super().__init__()
        self.api_service = api_service
        self.app_id = app_id
        self.products = products
        self.exclude_china = exclude_china
        self.screenshot_path = screenshot_path
        self._is_cancelled = False
    
    def cancel(self):
        self._is_cancelled = True
    
    def run(self):
        success_count = 0
        fail_count = 0
        total = len(self.products)
        
        # 加载截图数据
        screenshot_data = None
        screenshot_name = ""
        if self.screenshot_path:
            try:
                with open(self.screenshot_path, 'rb') as f:
                    screenshot_data = f.read()
                screenshot_name = self.screenshot_path.split('/')[-1].split('\\')[-1]
            except Exception as e:
                pass
        
        for i, product in enumerate(self.products):
            if self._is_cancelled:
                break
            
            self.progress.emit(i + 1, total, f"正在创建: {product.display_name}")
            
            try:
                # 创建模板
                template = product.to_iap_template()
                
                # 创建内购产品
                iap = self.api_service.create_in_app_purchase(self.app_id, template)
                
                # 设置价格
                try:
                    price_points = self.api_service.fetch_price_points(iap.id)
                    matching_point = self.api_service.find_matching_price_point(
                        product.price, price_points
                    )
                    if matching_point:
                        self.api_service.create_price_schedule(iap.id, matching_point.id)
                except Exception:
                    pass
                
                # 创建本地化
                try:
                    for loc in template.localizations:
                        self.api_service.create_localization(iap.id, loc)
                except Exception:
                    pass
                
                # 设置销售范围
                try:
                    self.api_service.create_availability(iap.id, self.exclude_china)
                except Exception:
                    pass
                
                # 上传截图
                if screenshot_data:
                    try:
                        self.api_service.upload_review_screenshot(
                            iap.id, screenshot_data, screenshot_name
                        )
                    except Exception:
                        pass
                
                result = BatchOperationResult(product.product_id, True, "创建成功")
                success_count += 1
                
            except Exception as e:
                result = BatchOperationResult(product.product_id, False, str(e))
                fail_count += 1
            
            self.result.emit(result)
        
        self.finished.emit(success_count, fail_count)


class BatchTab(QWidget):
    """批量操作标签页"""
    
    def __init__(self, api_service: AppStoreConnectAPIService):
        super().__init__()
        self.api_service = api_service
        self.apps = []
        self.products = []
        self.selected_app = None
        self.screenshot_path = None
        self._worker = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("批量创建内购产品")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 应用选择
        app_layout = QHBoxLayout()
        app_layout.addWidget(QLabel("选择应用:"))
        
        self.app_combo = QComboBox()
        self.app_combo.setMinimumWidth(300)
        self.app_combo.currentIndexChanged.connect(self._on_app_changed)
        app_layout.addWidget(self.app_combo)
        
        self.refresh_apps_btn = QPushButton("刷新")
        self.refresh_apps_btn.clicked.connect(self.refresh_apps)
        app_layout.addWidget(self.refresh_apps_btn)
        
        app_layout.addStretch()
        layout.addLayout(app_layout)
        
        # 使用分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 产品表格区域
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.add_row_btn = QPushButton("添加行")
        self.add_row_btn.clicked.connect(self._add_row)
        toolbar.addWidget(self.add_row_btn)
        
        self.load_template_btn = QPushButton("预设模板")
        self.load_template_btn.clicked.connect(self._load_template)
        toolbar.addWidget(self.load_template_btn)
        
        self.import_txt_btn = QPushButton("导入TXT")
        self.import_txt_btn.clicked.connect(self._import_txt)
        toolbar.addWidget(self.import_txt_btn)
        
        self.import_excel_btn = QPushButton("导入Excel/CSV")
        self.import_excel_btn.clicked.connect(self._import_excel)
        toolbar.addWidget(self.import_excel_btn)
        
        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self._clear_all)
        toolbar.addWidget(self.clear_btn)
        
        toolbar.addStretch()
        
        self.product_count_label = QLabel("0 个产品")
        toolbar.addWidget(self.product_count_label)
        
        table_layout.addLayout(toolbar)
        
        # 产品表格
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels([
            "选择", "产品ID", "显示名称", "描述", "价格"
        ])
        self.products_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.products_table.setColumnWidth(0, 50)
        self.products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.products_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.products_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.products_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.products_table.setAlternatingRowColors(True)
        table_layout.addWidget(self.products_table)
        
        splitter.addWidget(table_widget)
        
        # 选项和操作区域
        options_widget = QWidget()
        options_layout = QVBoxLayout(options_widget)
        options_layout.setContentsMargins(0, 0, 0, 0)
        
        # 选项
        options_group = QGroupBox("选项")
        options_inner = QVBoxLayout(options_group)
        
        self.exclude_china_check = QCheckBox("去除中国大陆和港澳台销售")
        self.exclude_china_check.setChecked(True)
        options_inner.addWidget(self.exclude_china_check)
        
        # 截图选择
        screenshot_layout = QHBoxLayout()
        screenshot_layout.addWidget(QLabel("审核截图:"))
        
        self.screenshot_label = QLabel("未选择")
        self.screenshot_label.setStyleSheet("color: #666;")
        screenshot_layout.addWidget(self.screenshot_label)
        
        self.select_screenshot_btn = QPushButton("选择图片")
        self.select_screenshot_btn.clicked.connect(self._select_screenshot)
        screenshot_layout.addWidget(self.select_screenshot_btn)
        
        screenshot_layout.addStretch()
        options_inner.addLayout(screenshot_layout)
        
        options_layout.addWidget(options_group)
        
        # 创建按钮和进度
        create_layout = QHBoxLayout()
        
        self.create_btn = QPushButton("开始批量创建")
        self.create_btn.clicked.connect(self._start_batch_create)
        self.create_btn.setEnabled(False)
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 30px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        create_layout.addWidget(self.create_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self._cancel_batch_create)
        self.cancel_btn.setEnabled(False)
        create_layout.addWidget(self.cancel_btn)
        
        create_layout.addStretch()
        
        self.progress_label = QLabel("")
        create_layout.addWidget(self.progress_label)
        
        options_layout.addLayout(create_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        options_layout.addWidget(self.progress_bar)
        
        # 结果日志
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setVisible(False)
        options_layout.addWidget(self.log_text)
        
        splitter.addWidget(options_widget)
        
        splitter.setSizes([400, 200])
        layout.addWidget(splitter)
    
    def refresh_apps(self):
        """刷新应用列表"""
        if not self.api_service.is_authenticated:
            QMessageBox.warning(self, "提示", "请先完成API认证配置")
            return
        
        self.refresh_apps_btn.setEnabled(False)
        self.app_combo.clear()
        self.app_combo.addItem("加载中...")
        
        self._worker = FetchAppsWorker(self.api_service)
        self._worker.finished.connect(self._on_apps_loaded)
        self._worker.error.connect(self._on_apps_error)
        self._worker.start()
    
    @pyqtSlot(list)
    def _on_apps_loaded(self, apps: list):
        """应用列表加载完成"""
        self.refresh_apps_btn.setEnabled(True)
        self.apps = apps
        self.app_combo.clear()
        
        if not apps:
            self.app_combo.addItem("没有找到应用")
            return
        
        self.app_combo.addItem("请选择应用")
        for app in apps:
            self.app_combo.addItem(f"{app.name} ({app.bundle_id})", app)
    
    @pyqtSlot(str)
    def _on_apps_error(self, error: str):
        """应用列表加载失败"""
        self.refresh_apps_btn.setEnabled(True)
        self.app_combo.clear()
        self.app_combo.addItem("加载失败")
        QMessageBox.critical(self, "错误", f"获取应用列表失败：{error}")
    
    def _on_app_changed(self, index: int):
        """应用选择变化"""
        if index > 0 and index <= len(self.apps):
            self.selected_app = self.apps[index - 1]
            self._update_create_button()
        else:
            self.selected_app = None
            self.create_btn.setEnabled(False)
    
    def _add_row(self):
        """添加一行"""
        row = self.products_table.rowCount()
        self.products_table.insertRow(row)
        
        # 选择复选框
        check = QCheckBox()
        check.setChecked(True)
        check_widget = QWidget()
        check_layout = QHBoxLayout(check_widget)
        check_layout.addWidget(check)
        check_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        check_layout.setContentsMargins(0, 0, 0, 0)
        self.products_table.setCellWidget(row, 0, check_widget)
        
        # 其他列
        for col in range(1, 5):
            self.products_table.setItem(row, col, QTableWidgetItem(""))
        
        # 价格默认值
        self.products_table.item(row, 4).setText("0.99")
        
        self._update_product_count()
    
    def _load_template(self):
        """加载预设模板"""
        templates = [
            BatchProduct(product_id="", display_name="400 coins", description="400 coins", price="0.99"),
            BatchProduct(product_id="", display_name="800 coins", description="800 coins", price="1.99"),
            BatchProduct(product_id="", display_name="2450 coins", description="2450 coins", price="4.99"),
            BatchProduct(product_id="", display_name="5150 coins", description="5150 coins", price="9.99"),
            BatchProduct(product_id="", display_name="10800 coins", description="10800 coins", price="19.99"),
            BatchProduct(product_id="", display_name="29400 coins", description="29400 coins", price="49.99"),
            BatchProduct(product_id="", display_name="63700 coins", description="63700 coins", price="99.99"),
        ]
        
        self._clear_all()
        
        for template in templates:
            self._add_product_row(template)
        
        QMessageBox.information(self, "提示", f"已加载 {len(templates)} 个预设模板")
    
    def _add_product_row(self, product: BatchProduct):
        """添加产品行"""
        row = self.products_table.rowCount()
        self.products_table.insertRow(row)
        
        # 选择复选框
        check = QCheckBox()
        check.setChecked(product.is_selected)
        check_widget = QWidget()
        check_layout = QHBoxLayout(check_widget)
        check_layout.addWidget(check)
        check_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        check_layout.setContentsMargins(0, 0, 0, 0)
        self.products_table.setCellWidget(row, 0, check_widget)
        
        # 产品ID
        self.products_table.setItem(row, 1, QTableWidgetItem(product.product_id))
        
        # 显示名称
        self.products_table.setItem(row, 2, QTableWidgetItem(product.display_name))
        
        # 描述
        self.products_table.setItem(row, 3, QTableWidgetItem(product.description))
        
        # 价格
        self.products_table.setItem(row, 4, QTableWidgetItem(product.price))
        
        self._update_product_count()
    
    def _import_txt(self):
        """导入TXT文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择TXT文件", "", "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            from ..utils.file_parser import FileParser
            
            try:
                products = FileParser.parse_txt_file(file_path)
                self._clear_all()
                for product in products:
                    self._add_product_row(product)
                QMessageBox.information(self, "成功", f"成功导入 {len(products)} 个产品")
            except Exception as e:
                QMessageBox.critical(self, "导入失败", str(e))
    
    def _import_excel(self):
        """导入Excel/CSV文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "",
            "Excel/CSV Files (*.xlsx *.xls *.csv);;All Files (*)"
        )
        
        if file_path:
            from ..utils.file_parser import FileParser
            
            try:
                if file_path.lower().endswith('.csv'):
                    products = FileParser.parse_csv_file(file_path)
                else:
                    products = FileParser.parse_excel_file(file_path)
                
                self._clear_all()
                for product in products:
                    self._add_product_row(product)
                QMessageBox.information(self, "成功", f"成功导入 {len(products)} 个产品")
            except Exception as e:
                QMessageBox.critical(self, "导入失败", str(e))
    
    def _clear_all(self):
        """清空所有"""
        self.products_table.setRowCount(0)
        self._update_product_count()
    
    def _select_screenshot(self):
        """选择审核截图"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择审核截图", "",
            "Image Files (*.png *.jpg *.jpeg);;All Files (*)"
        )
        
        if file_path:
            self.screenshot_path = file_path
            file_name = file_path.split('/')[-1].split('\\')[-1]
            self.screenshot_label.setText(file_name)
            self.screenshot_label.setStyleSheet("color: #4CAF50;")
    
    def _update_product_count(self):
        """更新产品数量显示"""
        count = self.products_table.rowCount()
        self.product_count_label.setText(f"{count} 个产品")
        self._update_create_button()
    
    def _update_create_button(self):
        """更新创建按钮状态"""
        has_products = self.products_table.rowCount() > 0
        has_app = self.selected_app is not None
        self.create_btn.setEnabled(has_products and has_app)
    
    def _get_selected_products(self) -> list:
        """获取选中的产品列表"""
        products = []
        for row in range(self.products_table.rowCount()):
            check_widget = self.products_table.cellWidget(row, 0)
            if check_widget:
                check = check_widget.findChild(QCheckBox)
                if check and check.isChecked():
                    product = BatchProduct(
                        product_id=self.products_table.item(row, 1).text().strip(),
                        display_name=self.products_table.item(row, 2).text().strip(),
                        description=self.products_table.item(row, 3).text().strip(),
                        price=self.products_table.item(row, 4).text().strip()
                    )
                    if product.product_id and product.display_name:
                        products.append(product)
        return products
    
    def _start_batch_create(self):
        """开始批量创建"""
        products = self._get_selected_products()
        
        if not products:
            QMessageBox.warning(self, "提示", "请选择至少一个有效的产品")
            return
        
        if not self.selected_app:
            QMessageBox.warning(self, "提示", "请选择应用")
            return
        
        # 确认
        reply = QMessageBox.question(
            self, "确认",
            f"确定要为应用「{self.selected_app.name}」创建 {len(products)} 个内购产品吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 开始创建
        self.create_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(products))
        self.progress_bar.setValue(0)
        self.log_text.setVisible(True)
        self.log_text.clear()
        
        self._worker = BatchCreateWorker(
            self.api_service,
            self.selected_app.id,
            products,
            self.exclude_china_check.isChecked(),
            self.screenshot_path
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.result.connect(self._on_result)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()
    
    def _cancel_batch_create(self):
        """取消批量创建"""
        if self._worker:
            self._worker.cancel()
    
    @pyqtSlot(int, int, str)
    def _on_progress(self, current: int, total: int, message: str):
        """进度更新"""
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"{current}/{total}: {message}")
    
    @pyqtSlot(object)
    def _on_result(self, result: BatchOperationResult):
        """单个结果"""
        if result.success:
            self.log_text.append(f"✅ {result.product_id}: {result.message}")
        else:
            self.log_text.append(f"❌ {result.product_id}: {result.message}")
    
    @pyqtSlot(int, int)
    def _on_finished(self, success_count: int, fail_count: int):
        """完成"""
        self.create_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_label.setText(f"完成: 成功 {success_count}, 失败 {fail_count}")
        
        QMessageBox.information(
            self, "完成",
            f"批量创建完成！\n\n成功: {success_count}\n失败: {fail_count}"
        )
