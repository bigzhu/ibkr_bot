# IBKR API 模块

基于 IB Gateway/TWS 的 ibapi 封装,提供账户/余额/持仓/订单查询与下单的最小接口.

## 🚀 主要特性

- **遵循 CLAUDE.md 规范**: 函数优先,fail-fast 原则,严格类型注解
- **模块化设计**: 每个功能独立模块,可单独运行和测试
- **双重用途**: 既可作为库导入使用,也可独立运行
- **统一配置**: 通过环境变量配置 IB Gateway/TWS 连接
- **金融级安全**: 异常向上传播,保护资金安全

## 📋 模块结构

```text
ibkr_api/
├── __init__.py          # 模块导出和接口定义
├── __main__.py          # 统一命令行入口
├── common.py            # 公共函数和配置管理
├── get_account.py       # 账户信息查询
├── get_balance.py       # 账户基础货币余额
├── get_positions.py     # 持仓查询
├── get_open_orders.py   # 未成交订单查询
├── get_executions.py    # 成交明细查询
├── place_order.py       # 下单(IBKR)
└── README.md            # 本文档
```

## ⚙️ 配置要求

通过环境变量配置:

| 配置键 | 说明 | 必需 |
|--------|------|------|
| IBKR_HOST | IB Gateway/TWS 主机, 默认 127.0.0.1 | ❌ |
| IBKR_PORT | Socket 端口, 实盘 Gateway 通常 4001, 纸盘 4002 | ❌ |
| IBKR_CLIENT_ID | 客户端 ID, 每个实例唯一 | ❌ |
| IBKR_ACCOUNT | 可选,指定账号 | ❌ |
| BASE_CURRENCY | 基础货币, 默认 USD | ❌ |
| IBKR_PAPER | 是否纸盘, 默认 true | ❌ |

## 🛠️ 使用方法

## 🛠️ 常用命令

```bash
# 账户信息
uv run python -m ibkr_api.get_account

# 基础货币余额
uv run python -m ibkr_api.get_balance

# 持仓列表
uv run python -m ibkr_api.get_positions

# 未成交订单
uv run python -m ibkr_api.get_open_orders

# 成交明细
uv run python -m ibkr_api.get_executions

# 下单示例(市价/限价)
uv run python -m ibkr_api.place_order AAPL 10 SMART USD BUY MKT
uv run python -m ibkr_api.place_order AAPL 10 SMART USD BUY LMT 150
```

## ⚠️ 注意事项

- Gateway/TWS 必须开启 API 并使用唯一 `IBKR_CLIENT_ID`; 不支持同账号多会话,重复登录会被踢或拒绝.
- 一次性 CLI 已在执行完毕后自动 `disconnect` 避免长连接挂起.
- 当前仅封装账户/余额/持仓/未完单/成交/下单; 行情与合约查询需后续补充。
