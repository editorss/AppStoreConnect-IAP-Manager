#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包脚本 - 将应用打包为exe可执行文件
使用PyInstaller进行打包
"""

import subprocess
import sys
import os

def main():
    # 确保在正确的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("=" * 50)
    print("App Store Connect 内购管理工具 - 打包脚本")
    print("=" * 50)
    
    # 检查PyInstaller是否安装
    try:
        import PyInstaller
        print(f"✓ PyInstaller已安装: {PyInstaller.__version__}")
    except ImportError:
        print("正在安装PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 安装项目依赖
    print("\n正在安装项目依赖...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # PyInstaller打包命令
    print("\n开始打包...")
    
    pyinstaller_args = [
        "pyinstaller",
        "--name=内购管理工具",
        "--windowed",              # 不显示控制台窗口
        "--onefile",               # 打包成单个exe文件
        "--noconfirm",             # 覆盖已存在的文件
        "--clean",                 # 清理临时文件
        "--add-data=src;src",      # 包含src目录
        "main.py"
    ]
    
    # Windows下使用分号，其他系统使用冒号
    if sys.platform != "win32":
        pyinstaller_args[6] = "--add-data=src:src"
    
    subprocess.check_call(pyinstaller_args)
    
    print("\n" + "=" * 50)
    print("打包完成！")
    print("=" * 50)
    print(f"\n可执行文件位置: dist/内购管理工具.exe")
    print("\n可以将该文件复制到Windows电脑上直接运行。")


if __name__ == "__main__":
    main()
