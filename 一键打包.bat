@echo off
chcp 65001 >nul
echo ================================================
echo   App Store Connect 内购管理工具 - Windows打包
echo ================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.9+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] 正在安装依赖...
pip install PyQt6 PyJWT cryptography requests openpyxl pyinstaller -q

echo.
echo [2/3] 正在打包应用...
pyinstaller --name="内购管理工具" --windowed --onefile --noconfirm --clean main.py

echo.
echo ================================================
echo [3/3] 打包完成！
echo ================================================
echo.
echo 可执行文件位置: dist\内购管理工具.exe
echo.
echo 你可以将 内购管理工具.exe 复制到任意位置直接运行
echo.

REM 打开输出目录
explorer dist

pause
