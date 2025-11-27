# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🌐 项目概述

mexc_bot Web Admin 是 MEXC 交易机器人的 Web 管理界面,采用前后端分离架构.当前工作目录是 `web_admin` 子项目.

## 🏗️ 架构结构

### 后端 (FastAPI)

- **api/** - FastAPI 后端服务
  - `routes/` - API 路由定义
  - `models/` - Pydantic 数据模型
  - `utils/` - 工具函数和数据库助手
  - `services/` - 业务逻辑服务
  - `websocket.py` - WebSocket 实时通信

### 前端 (Vue.js + Quasar)

- **frontend/** - Vue.js 前端应用
  - `src/pages/` - 页面组件
  - `src/components/` - 通用组件
  - `src/stores/` - Pinia 状态管理
  - `src/services/` - API 调用服务
  - `src/router/` - 路由配置

## 🛠️ 开发命令

### 后端开发

```bash
# 启动 API 服务
uv run python api/start_api.py

# 运行代码检查
uv run ruff check .
uv run mypy .

# 格式化代码
uv run black .
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 开发模式启动
npm run dev

# 构建生产版本
npm run build

# 代码检查
npm run lint

# 格式化代码
npm run format
```

## 📋 核心功能模块

### 主要页面

- **DashboardPage** - 总览仪表板
- **ConfigPage** - 配置管理
- **SymbolsPage** - 交易对管理
- **TimeframeConfigPage** - 时间框架配置
- **FilledOrdersPage** - 已成交订单
- **BinanceFilledOrdersPage** - 币安成交订单
- **ProfitAnalysisPage** - 盈利分析
- **LogsPage** - 日志查看

## 🔗 API 路由文档

### 🔐 认证管理 (`/api/v1/auth`)

- `POST /login` - 用户登录
- `GET /verify` - 验证token有效性
- `POST /logout` - 用户登出
- `POST /change-password` - 修改密码

### ⚙️ 配置管理 (`/api/v1/config`)

- `GET /mexc/status` - 获取MEXC配置状态
- `POST /mexc/validate` - 验证MEXC配置
- `POST /mexc/save` - 保存MEXC配置
- `GET /log-level` - 获取日志级别
- `PUT /log-level` - 设置日志级别

### 📊 交易对管理 (`/api/v1/symbols`)

- `GET /list` - 获取交易对列表
- `POST /add` - 添加新交易对
- `PUT /{id}` - 更新交易对配置
- `DELETE /{id}` - 删除交易对
- `POST /refresh-all` - 刷新所有交易对
- `GET /{symbol}/signal-strength` - 获取信号强度

### ⏰ 时间框架配置 (`/api/v1/timeframe-configs`)

- `GET /` - 获取时间框架配置列表
- `GET /{symbol}` - 获取特定交易对配置
- `PUT /{configId}` - 更新配置
- `DELETE /{configId}` - 删除配置

### 📝 日志管理 (`/api/v1`)

- `GET /logs` - 获取系统日志
- `GET /logs/stats` - 获取日志统计
- `GET /logs/export` - 导出日志文件
- `POST /logs/clear` - 清理日志
- `GET /trading-logs/logs` - 获取交易日志
- `GET /trading-logs/stats` - 获取交易日志统计
- `GET /trading-logs/symbols` - 获取交易日志符号列表
- `POST /trading-logs/clear-all` - 清理所有交易日志

### 💰 成交订单管理 (`/api/v1`)

- `GET /filled-orders/` - 获取MEXC成交订单列表
- `GET /filled-orders/stats` - 获取订单统计
- `GET /filled-orders/symbols` - 获取订单交易对列表
- `POST /filled-orders/sync` - 同步MEXC成交订单
- `GET /binance-filled-orders/` - 获取币安成交订单列表
- `GET /binance-filled-orders/stats` - 获取币安订单统计
- `GET /binance-filled-orders/pairs` - 获取币安交易对列表
- `POST /binance-filled-orders/sync` - 同步币安成交订单
- `GET /binance-filled-orders/min-sell-conditions` - 获取最小卖出条件

### 📈 盈利分析 (`/api/profit-analysis`)

- `GET /sell-orders` - 获取有效SELL单明细(利润非0)
  - 支持日期过滤,交易对过滤,分页
  - 前端基于此数据进行每日收益和交易对汇总

### 🔄 内部事件通知 (`/api/v1/internal/events`)

- `POST /log-event` - 接收日志事件并转发到WebSocket
- `POST /order-event` - 接收订单事件并转发到WebSocket

## 🔧 技术栈

### 后端技术

- **FastAPI** - Web 框架
- **Pydantic** - 数据验证
- **WebSocket** - 实时通信
- **SQLite** - 数据库
- **Loguru** - 日志系统

### 前端技术

- **Vue 3** - 前端框架
- **Quasar** - UI 组件库
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP 客户端
- **TypeScript** - 类型安全

## 📡 实时功能

### WebSocket 端点

- `/ws/logs` - 日志实时推送
- 支持日志级别过滤和实时更新

### 状态管理

- **auth-store** - 认证状态
- **simple-auth** - 简化认证逻辑
- 使用 Pinia 进行响应式状态管理

## 🎯 开发规范

### API 开发

- 所有路由使用 FastAPI Router
- 数据模型使用 Pydantic 验证
- 错误处理统一使用 HTTPException
- 遵循 RESTful API 设计原则

### 前端开发

- 使用 Composition API
- 组件采用 `<script setup>` 语法
- 类型定义放在 `src/types/` 目录
- 样式使用 SCSS 和 Quasar 变量
- **组件复用原则** - 尽量构建可复用的 Vue 组件减少重复代码
  - 提取通用的表格,表单,卡片等组件
  - 封装通用的业务逻辑组件(如过滤器,分页器)
  - 创建通用的数据展示组件(如统计卡片,图表组件)
  - 避免在多个页面中重复相同的 UI 结构和逻辑

### 代码质量

- 后端代码必须通过 ruff,mypy 检查
- 前端代码必须通过 ESLint,TypeScript 检查
- 遵循项目根目录的 CLAUDE.md 规范

## 🔐 认证机制

- 基于 JWT 的认证系统
- 支持简单用户名/密码认证
- 前端路由守卫保护需要认证的页面
- 自动令牌续期和过期处理

## 📊 数据流架构

1. **前端** → HTTP/WebSocket → **API 路由** → **服务层** → **数据库**
2. **WebSocket** 用于实时日志推送和状态更新
3. **Pinia stores** 管理前端应用状态
4. **API services** 封装所有 HTTP 请求

## 🚀 部署配置

### Nginx 配置

- `nginx/trading.bigzhu.net.conf` - 生产环境配置
- 支持前端静态文件代理和 API 反向代理

### 环境要求

- **Python 3.11+** (后端)
- **Node.js 18+** (前端)
- **SQLite** (数据库)

## 💡 开发提示

- 后端修改后需要重启 API 服务
- 前端开发模式支持热重载
- WebSocket 连接在开发时自动重连
- 日志文件存储在 `logs/` 目录
- 数据库文件位于父目录的 `data/` 中

