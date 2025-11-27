# DeMark 交易机器人 - Web API 服务

## 功能说明
为 Quasar 前端提供 RESTful API 接口,管理 DeMark 交易机器人的配置参数

## 快速启动

### 方法1:使用启动脚本(推荐)
```bash
# Linux/macOS
./start_web_admin.sh

# Windows
start_web_admin.bat
```

### 方法2:使用 uv 命令
```bash
# 安装依赖
uv sync

# 启动服务
uv run web-admin
```

### 方法3:使用 uv 调用 Python
```bash
# 安装依赖
uv sync

# 启动服务
uv run python web_admin_server.py
```

## 访问信息
- **API 服务地址**: http://localhost:4444
- **API 文档**: http://localhost:4444/api/docs
- **前端界面**: 请使用 Quasar 前端项目 (frontend/)

## API 功能特性
- 🔐 **安全认证**: JWT 令牌认证,会话管理
- 🗃️ **数据管理**: 交易对,时间框架配置管理
- 📊 **交易日志**: 查询交易记录和统计
- 📈 **成交订单**: 同步和管理 Binance 成交订单
- ⚙️ **系统配置**: Binance API 配置和系统设置

## 目录结构
```
web_admin/
├── app/           # FastAPI 应用主模块
├── api/           # RESTful API 路由
│   └── v1/        # API v1 版本
├── models/        # 数据模型(Pydantic)
├── database/      # 数据库连接和操作
├── scheduler/     # 定时任务调度器
├── utils/         # 工具函数
└── README.md      # 说明文档
```

## 技术栈
- **FastAPI**: Web API 框架
- **SQLite**: 数据库
- **Pydantic**: 数据验证和序列化
- **JWT**: 身份认证
- **Uvicorn**: ASGI 服务器
- **APScheduler**: 定时任务调度

## 开发说明
- 数据库文件自动创建在 `data/bot.db`
- 日志级别可通过环境变量 `LOG_LEVEL` 设置
- 生产环境建议修改 JWT 密钥和数据库路径

## 安全注意事项
1. API 需要通过 JWT 令牌认证访问
2. 生产环境建议使用 HTTPS
3. 定期备份数据库文件
4. 不要在公网直接暴露 API 端口

## 相关项目
- **前端界面**: `frontend/` - Quasar/Vue.js 现代化前端
- **交易引擎**: `src/shared/trading/` - 核心交易逻辑
