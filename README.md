# IBKR DeMark 14 Trading Bot - 交易机器人

[![CI](https://github.com/bigzhu/ibkr_bot/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/bigzhu/ibkr_bot/actions/workflows/ci.yml)

一个使用 DeMark 14 技术指标进行交易决策的自动交易机器人.
项目正从 Binance(币安) 迁移至 IBKR, 交易与行情接入将统一对接 IB Gateway/TWS.

## 🏗️ 架构设计

### 模块化架构

每个模块单一职责,相互解耦,便于测试与维护:

```
ibkr_bot/
├── binance_api/        # IBKR 接入迁移入口(原 Binance 封装, 将逐步替换)
├── database/           # 数据模型与表管理,CRUD
├── indicators/         # 技术指标(demark,ema,atr,supertrend)
├── order_builder/      # 下单参数构建与校验
├── order_checker/      # 风险与数量等检查器
├── order_filler/       # 历史订单同步/撮合相关
├── scheduler/          # 任务调度(如有)
├── shared/             # 公共工具,配置,输出辅助
├── web_admin/          # 后端 API 与前端(如有)
├── scripts/            # 脚本与工具
└── data/               # 运行期数据(如数据库文件)
```

## 🎯 设计原则

- **单一职责**: 每个模块只负责一个特定功能
- **完全独立**: 不依赖外部目录的任何资源
- **金融数据零容忍**: 任何数据异常都立即失败
- **fail-fast**: 让程序在异常时立即失败
- **易于测试**: 每个模块都可独立测试

## 🚀 快速开始

### 1. 环境与运行(uv + 别名 p)

本项目使用 `uv` 管理环境与依赖,不直接调用 `python`;运行脚本请使用别名 `p`(等价于 `uv run python`).可在 shell 中添加:`alias p='uv run python'`.

在项目根目录执行 `direnv allow` 或 `source .envrc`, 系统会自动把仓库根目录加入 `PYTHONPATH`. 之后统一使用 `p -m package.module` 启动各类 CLI/脚本(例如 `p -m order_builder.app`), 无需再在代码中手动修改 `sys.path`.

```bash
# 安装依赖(示例)
uv sync

# 使用别名 p 运行脚本
p scripts/migrate_database.py --status
# 启动 Web API(二选一)
uv run python web_admin/api/start_api.py
# 或
./scripts/api_start.sh
```

### 2. IBKR 接入与配置

- 确保 IB Gateway 或 TWS 已启动并开启 API 访问,记录主机与端口.
- 建议使用独立 `clientId` 并优先启用 Paper 模式验证策略.
- 可在 `.env` 中预留以下配置(按需新增):

```bash
IBKR_HOST=127.0.0.1
IBKR_PORT=4002        # TWS/Paper 通常 7497/4002
IBKR_CLIENT_ID=1
IBKR_ACCOUNT=
IBKR_PAPER=true
BASE_CURRENCY=USD
```

### 3. 初始化数据库

```bash
p scripts/migrate_database.py
```

- 默认数据库文件位于 `data/bot.db`(已在 `.gitignore` 中忽略)
- 请勿将根目录下的临时/空 `.db` 文件作为持久库使用

### 4. 启动 Web 管理界面

```bash
uv run python web_admin/api/start_api.py
```

### 5. IBKR 接入要点

- 保持 IB Gateway/TWS 在线并开启 API 访问;重连后确认 session 未过期.
- 下单前确保合约标的(symbol, exchange, currency, secType)已在 IBKR 白名单内.
- 采用最小交易单位与基币(USD/EUR 等)进行数量计算,避免提交无效数量.
- 生产账号前先在 Paper 环境验证信号与风控链路.

## 🧹 代码质量(ruff + pyright)

在提交前请执行以下检查,确保格式与类型通过:

```bash
# 格式化
uv run ruff format .

# 风格检查并自动修复
uv run ruff check --fix .

# 类型检查
uv run pyright
```

## 📦 库用法(import)

在其他 Python 程序中按模块导入并调用:

```python
from order_builder import run_order_builder

# 编排完整流程: 获取信号 → 同步与撮合 → 清理 → 计算数量 → 检查 → 下单
run_order_builder("AAPL", "1d")

from decimal import Decimal
from order_checker import check
# 统一检查入口(严格顺序): DeMark → 交易所限制 → 操作模式 → 买入间隔(60m, BUY) → 每日限制 → 最大套住百分比 → 天级信号
check("AAPL", "1d", "BUY", 9, Decimal("0.5"), Decimal("123.45"))

from indicators.demark import demark
signal_type, signal_value, is_break, klines = demark(klines_data)

from order_filler.data_access import get_orders_by_pair
orders = get_orders_by_pair("AAPL")
```

在外部项目中使用本仓库模块时,请确保:
- 已通过 `uv pip install -e .` 可编辑安装到环境,或
- 以合适方式将本仓库根目录加入 `PYTHONPATH`.

## 🔒 提交前校验(pre-commit 可选)

安装并启用本地钩子,提交时自动执行格式化,静态检查与测试:

```bash
uv sync --dev
uv run pre-commit install

# 手动运行所有钩子
uv run pre-commit run --all-files
```

## 📊 功能特性

### DeMark 14 技术指标

- **TD Sequential 计算**: 基于价格序列的计数系统
- **TDUp/TDDn 序列**: 识别上涨和下跌趋势
- **信号强度分析**: 根据计数值评估信号强度
- **自动信号检测**: 实时监控并生成交易信号

### 订单撮合系统

- **历史订单同步**: 从交易所 API 同步历史订单
- **CSV 订单导入**: 支持批量导入订单数据
- **智能撮合算法**: 自动匹配买卖订单
- **盈亏计算**: 精确计算交易盈亏和统计

### Web 管理界面

- **配置管理**: 交易参数实时配置
- **信号监控**: DeMark 信号实时查看
- **订单管理**: 历史订单查询和分析
- **系统状态**: 监控系统运行状态

## 🧪 测试(使用 uv)

```bash
# 运行所有测试
uv run pytest tests/

# 运行特定模块测试
uv run pytest tests/test_demark/ -v

# 运行测试并生成覆盖率报告
uv run pytest tests/ \
  --cov=database --cov=indicators --cov=order_builder \
  --cov-report=html
```

## 🧰 运行检查器(命令行)

```bash
# 统一入口
p -m order_checker check <symbol> <timeframe> <side> <demark> <qty> <entry_price>

# 示例
p -m order_checker check ADAUSDC 15m BUY 9 0.5 1.2345
```

## 🤝 与智能体协作

- 规范: 参见 `AGENTS.md` (智能体在 Codex CLI 下的工作与输出规范)
- 仓库规则: 参见 `CLAUDE.md` (编码与业务约束, 包含 fail-fast, ruff/pyright 等要求)

## 🔧 开发指南

### 添加新模块

1. 在根目录创建新模块目录
2. 添加 `__init__.py` 文件
3. 实现模块功能,确保有 `if __name__ == "__main__":` 入口
4. 在 `tests/` 目录添加对应测试
5. 更新 `pyproject.toml` 配置

### 代码规范

- 使用 `ruff` 格式化与检查:`uv run ruff format .`,`uv run ruff check --fix .`
- 使用 `pyright` 进行类型检查:`uv run pyright`
- 运行脚本统一通过别名 `p`(`uv run python`),不要直接调用 `python`
- 遵循仓库规则文档:`CLAUDE.md` 与 `AGENTS.md`

## 📝 模块说明

### database/ - 数据库模块

统一的数据库操作接口,支持 SQLite,包含完整的 CRUD 操作和数据迁移功能.

### demark/ - DeMark 指标模块

纯函数实现的 DeMark 14 技术指标计算,包含信号检测和强度分析功能.

### binance_api/ - IBKR 交易接口模块(迁移中)

承载 IBKR 行情/下单适配代码,将逐步完成从 Binance 到 IBKR 的封装替换.

### order_filler/ - 订单处理模块

专门处理已完成订单的同步,导入,撮合和盈亏计算.

### web_admin/ - Web 管理端

基于 FastAPI 的 RESTful API,为前端提供完整的管理接口.

## 📈 版本历史

- **v2.1.0** - IBKR 迁移启动
  - 文档对齐 IBKR 网关接入与配置
  - 准备替换 Binance 封装为 IBKR 封装
- **v2.0.0** - 模块化重构版本
  - 全新模块化架构
  - 单一职责设计
  - 完整测试覆盖
  - 金融数据零容忍处理

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交变更
4. 通过所有测试
5. 提交 Pull Request

## 📄 许可证

本项目遵循 MIT 许可证.
