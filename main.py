#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
App Store Connect API 内购管理工具 - Windows版
主程序入口
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.ui.main_window import MainWindow


def main():
    """应用程序入口"""
    # 启用高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("App Store Connect API Tool")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("AppStoreConnectTool")
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
