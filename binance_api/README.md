# Binance API 模块

基于 Binance 官方 python-binance SDK 的简化 API 接口模块,专为 mexc_bot 项目设计.

## 🚀 主要特性

- **遵循 CLAUDE.md 规范**: 函数优先,fail-fast 原则,严格类型注解
- **模块化设计**: 每个功能独立模块,可单独运行和测试
- **双重用途**: 既可作为库导入使用,也可独立运行
- **统一配置**: 从数据库读取 API 配置,支持主网/测试网切换
- **金融级安全**: 异常向上传播,保护资金安全

## 📋 模块结构

```text
binance_api/
├── __init__.py          # 模块导出和接口定义
├── __main__.py          # 统一命令行入口
├── common.py            # 公共函数和配置管理
├── get_account.py       # 账户信息查询
├── get_balance.py       # 资产余额查询
├── get_exchange_info.py # 交易所信息查询
├── get_klines.py        # K线数据查询
├── get_open_orders.py   # 未成交订单查询
├── get_symbol_ticker.py # 价格行情查询
├── place_order.py       # 订单创建和管理
└── README.md            # 本文档
```

## ⚙️ 配置要求

在数据库 `system_config` 表中配置以下项:

| 配置键 | 说明 | 必需 |
|--------|------|------|
| MAIN_BINANCE_API_KEY | Binance API Key | ✅ |
| MAIN_BINANCE_SECRET_KEY | Binance Secret Key | ✅ |
| BINANCE_TESTNET | 是否使用测试网 (true/false) | ❌ (默认 false) |

## 🛠️ 使用方法

### 1. 统一命令行接口

```bash
# 查看使用帮助
p -m binance_api

# 测试API连接
p -m binance_api test

# 账户信息
p -m binance_api account

# 资产余额
p -m binance_api balance          # 所有余额
p -m binance_api balance BTC      # 指定资产

# 交易所信息
p -m binance_api exchange         # 交易所基本信息
p -m binance_api exchange ADAUSDC # 指定交易对信息

# 价格行情
p -m binance_api price ADAUSDC           # 当前价格
p -m binance_api price ADAUSDC 24hr      # 24小时统计
p -m binance_api price ADAUSDC orderbook # 订单簿价格

# K线数据
p -m binance_api klines ADAUSDC     # 默认1小时,20条
p -m binance_api klines ADAUSDC 1h 50  # 指定间隔和数量

# 未成交订单
p -m binance_api orders             # 所有订单
p -m binance_api orders ADAUSDC     # 指定交易对
p -m binance_api orders ADAUSDC buy # 指定方向
```

### 2. 独立模块运行

每个模块都可以独立运行:

```bash
# 账户信息
p binance_api/get_account.py

# 指定资产余额
p binance_api/get_balance.py BTC

# 交易对信息
p binance_api/get_exchange_info.py ADAUSDC

# K线数据
p binance_api/get_klines.py ADAUSDC 1h 100

# 价格信息
p binance_api/get_symbol_ticker.py ADAUSDC 24hr

# 未成交订单
p binance_api/get_open_orders.py ADAUSDC

# 测试下单
p binance_api/place_order.py test ADAUSDC BUY LIMIT 0.001 50000
```

### 3. 作为库导入使用

```python
from binance_api import (
    get_configured_client,
    account_info,
    get_balance,
    ticker_price,
    klines,
    place_order_test
)

# 获取配置好的客户端
client, config = get_configured_client()

if client:
    # 查询账户信息
    account = account_info(client)
    
    # 查询余额
    btc_balance = get_balance("BTC")
    
    # 查询价格
    price_info = ticker_price(client, "ADAUSDC")
    
    # 获取K线数据
    kline_data = klines(client, "ADAUSDC", "1h", 50)
    
    # 测试下单
    test_result = place_order_test(client, "ADAUSDC", "BUY", "LIMIT", "0.001", "50000")
```

## 🔧 核心函数

### 配置管理
- `get_configured_client()`: 获取已配置的客户端
- `get_api_config_from_db()`: 从数据库读取配置
- `create_binance_client()`: 创建 Binance 客户端

### 账户管理
- `account_info(client)`: 获取账户信息
- `get_balance(asset)`: 获取指定资产余额
- `get_all_balances(client)`: 获取所有余额

### 市场数据
- `ticker_price(client, symbol)`: 获取价格信息
- `klines(client, symbol, interval, limit)`: 获取K线数据
- `exchange_info(client)`: 获取交易所信息

### 订单管理
- `open_orders(client, symbol)`: 获取未成交订单
- `place_order_test()`: 测试下单
- `place_order()`: 实际下单
- `cancel_order()`: 取消订单

## 🚨 安全特性

1. **Fail-Fast 原则**: 异常立即向上传播,不使用默认值掩盖错误
2. **参数验证**: 在用户入口点进行严格的参数验证
3. **类型安全**: 所有函数都有完整的类型注解
4. **金融级精度**: 使用 Decimal 处理价格和数量
5. **测试优先**: 提供测试接口,避免意外交易

## 📝 开发规范

- 遵循 CLAUDE.md 中的所有规范
- 每个函数不超过 50 行代码
- 禁止使用 try-except (除 ImportError)
- 必须使用完整的类型注解
- 使用 loguru.logger 而非 print()
- 信任调用方原则,内部函数不重复验证参数

## 🧪 测试

```bash
# 测试API连接
p -m binance_api test

# 测试公共函数
p binance_api/common.py

# 测试各个模块
p binance_api/get_account.py
p binance_api/get_balance.py
p binance_api/get_exchange_info.py
```

## 🔄 与 MEXC API 模块的关系

binance_api 模块参考了 mexc_api 的设计模式,但针对 Binance API 的特性进行了适配:

- 使用 python-binance SDK 而非 mexc-sdk
- 支持测试网切换 (MEXC 只有主网)
- 数据库配置键名不同 (BINANCE_ vs MEXC_)
- API 响应格式略有差异

两个模块可以并存使用,为多交易所策略提供支持.