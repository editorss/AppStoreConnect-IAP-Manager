# App Store Connect API 内购管理工具 - Windows版

## 项目概述

这是一个基于App Store Connect API开发的Windows桌面应用程序，用于批量创建和管理应用内购买产品（In-App Purchases）。

## 功能特性

### API认证管理
- JWT令牌自动生成（ES256签名）
- .p8私钥文件导入
- 连接状态实时检测
- 认证信息本地保存

### 内购产品管理
- 支持四种内购类型：消耗型、非消耗型、自动续费订阅、非续费订阅
- 完整的产品信息配置：ID、名称、描述、价格等
- 多语言本地化支持
- 销售区域设置

### 批量操作功能
- JSON文件批量导入
- TXT文件快速导入（欢牛模板格式）
- Excel/CSV文件导入
- 实时进度显示
- 智能重试机制

## 技术栈

- **语言**: Python 3.11+
- **GUI框架**: PyQt6
- **JWT认证**: PyJWT + cryptography
- **HTTP请求**: requests
- **Excel解析**: openpyxl

## 获取可执行文件

### 方法一：从GitHub下载（推荐）

1. 将项目推送到GitHub
2. GitHub Actions会自动打包Windows exe和macOS app
3. 在Actions页面下载打包好的文件

### 方法二：本地打包

**Windows用户：**
```cmd
双击运行 一键打包.bat
```

**macOS用户：**
```bash
pip install pyinstaller PyQt6 PyJWT cryptography requests openpyxl
pyinstaller --name="内购管理工具" --windowed --onedir --noconfirm main.py
```

### 方法三：开发模式运行

```bash
pip install -r requirements.txt
python main.py
```

## 使用说明

### 第一步：获取API密钥

1. 登录 [App Store Connect](https://appstoreconnect.apple.com)
2. 进入「用户和访问」→「密钥」
3. 生成新的API密钥，选择「开发者」角色
4. 下载.p8私钥文件并记录Key ID和Issuer ID

### 第二步：配置认证

1. 在「API认证」标签页输入Key ID和Issuer ID
2. 导入.p8私钥文件
3. 点击「测试连接」确保配置正确

### 第三步：管理内购产品

- **单个创建**：在「内购管理」中选择应用后点击「创建内购产品」
- **批量创建**：在「批量操作」中导入配置文件进行批量创建

## 注意事项

- 产品ID创建后无法修改，请谨慎设置
- API有速率限制，批量操作会自动控制速度
- 私钥文件请妥善保管，避免泄露
- 创建的产品需要通过苹果审核才能正式上线

## 项目结构

```
AppStoreConnectTool-Windows/
├── main.py                      # 应用入口
├── requirements.txt             # Python依赖
├── src/
│   ├── core/                    # 核心业务逻辑
│   │   ├── jwt_authenticator.py # JWT认证（ES256签名）
│   │   ├── api_service.py       # API服务
│   │   └── models.py            # 数据模型
│   ├── ui/                      # 用户界面
│   │   ├── main_window.py       # 主窗口
│   │   ├── auth_tab.py          # API认证标签页
│   │   ├── iap_tab.py           # 内购管理标签页
│   │   ├── batch_tab.py         # 批量操作标签页
│   │   └── dialogs/             # 对话框
│   └── utils/                   # 工具函数
│       ├── file_parser.py       # 文件解析
│       └── config.py            # 配置管理
└── resources/                   # 资源文件
```

## 与macOS版本的区别

- 去除了代理设置功能
- 去除了激活码系统
- 使用Python + PyQt6实现，支持Windows平台
- 界面风格简洁实用

## 项目状态

- 开发完成

---

*基于macOS版本移植 - Python + PyQt6实现*
