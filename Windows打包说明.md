# Windows打包说明

## 打包步骤

### 方法一：一键打包（推荐）

1. 将整个 `AppStoreConnectTool-Windows` 文件夹复制到Windows电脑
2. 双击运行 `一键打包.bat`
3. 等待打包完成（约1-2分钟）
4. 在 `dist` 文件夹中找到 `内购管理工具.exe`

### 方法二：手动打包

1. 安装Python 3.9+（https://www.python.org/downloads/）
2. 打开命令提示符，进入项目目录
3. 执行以下命令：

```cmd
pip install PyQt6 PyJWT cryptography requests openpyxl pyinstaller
pyinstaller --name="内购管理工具" --windowed --onefile --noconfirm --clean main.py
```

4. 在 `dist` 文件夹中找到生成的 `内购管理工具.exe`

## 注意事项

- 打包需要在Windows系统上进行（macOS无法打包exe）
- 首次打包可能需要下载大约200MB的依赖
- 生成的exe文件约80-100MB，可以独立运行
- 如果杀毒软件报警，请添加信任（PyInstaller打包的程序经常被误报）

## 文件说明

| 文件 | 用途 |
|-----|-----|
| `一键打包.bat` | Windows一键打包脚本 |
| `main.py` | 程序入口 |
| `src/` | 源代码目录 |
| `requirements.txt` | Python依赖列表 |
