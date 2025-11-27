# Filled Orders 模块

基于 mexc_order_filler 设计的币安已成交订单管理模块,专为 mexc_bot 项目设计.

## 🚀 主要特性

- **遵循 CLAUDE.md 规范**: fail-fast 原则,严格类型注解,禁用 try-except
- **模块化设计**: 每个功能独立模块,可单独运行和测试
- **双重用途**: 既可作为库导入使用,也可独立运行
- **统一数据管理**: 使用统一的数据库连接系统
- **金融级安全**: 异常向上传播,保护资金安全

## 📋 模块结构

```text
order_filler/
├── __init__.py              # 模块导出和接口定义
├── __main__.py              # 统一命令行入口
├── data_access/             # 数据访问层子包(v2 重构)
│   ├── __init__.py          # 统一数据访问接口导出
│   ├── crud.py              # 订单CRUD操作
│   ├── queries.py           # 订单查询功能
│   ├── updates.py           # 订单更新操作
│   └── matches.py           # 订单撮合详情
├── matching/                # 订单撮合模块子包(v3 重构)
│   ├── __init__.py          # 统一撮合接口导出
│   ├── engine.py            # 撮合引擎核心逻辑
│   ├── utils.py             # 撮合工具函数
│   ├── cli.py               # 命令行入口
│   └── proxy.py             # 代理撮合功能(1m代理其他周期)
├── sync/                    # 订单同步模块子包(v4 重构)
│   ├── __init__.py          # 统一同步接口导出
│   ├── orders.py            # API订单同步核心逻辑
│   └── cli.py               # 同步命令行入口
├── workflows/               # 工作流程编排(v5 重构)
│   ├── __init__.py          # 导出顶层工作流程
│   └── sync_and_match.py    # 一键同步撮合编排
├── profit_lock.py           # 利润锁定计算
├── csv_importer.py          # CSV导入功能
└── README.md                # 本文档
```

## ⚠️ 模块重构说明 (v5 Update - Workflows Subpackage)

### workflows 子包重构

**新增 `workflows/` 子包,将顶层编排逻辑 (sync_and_match_orders.py) 迁入**, 实现清晰的业务流程分离.

#### 新结构 (v5 重构):
```text
order_filler/workflows/
├── __init__.py              # 统一工作流程导出
└── sync_and_match.py        # 一键同步撮合: sync_and_match_orders()
```

#### 导入迁移指南

**✅ 新导入方式:**
```python
from order_filler.workflows import sync_and_match_orders
sync_and_match_orders('ADAUSDC', '15m')
```

---

## ⚠️ 模块重构说明 (v4 Update - Sync Subpackage)

### sync 子包重构

**原 `sync_orders.py` 已被重构到 `sync/` 子包**, 并分离出独立的 CLI 层.

#### 新结构 (v4 重构):
```text
order_filler/sync/
├── __init__.py          # 统一同步API导出
├── orders.py            # 核心同步逻辑: sync_orders_for_pair()
└── cli.py               # 命令行入口和测试
```

#### 导入迁移指南

**✅ 推荐: 直接从 sync 导入**
```python
from order_filler.sync import sync_orders_for_pair
sync_orders_for_pair('ADAUSDC', limit=1000)
```

---

## ⚠️ 模块重构说明 (v3 Update - Matching Subpackage)

### matching 子包重构

**原 `match_engine.py`, `match_utils.py`, `match_orders.py`, `proxy_matching.py` 已被整合到 `matching/` 子包**, 实现清晰的职责分离和模块化设计.

#### 新结构 (v3 重构):
```text
order_filler/matching/
├── __init__.py          # 统一撮合API导出
├── engine.py            # 核心撮合引擎: match_orders, process_order_matching
├── utils.py             # 撮合工具函数: add_to_buy_pool, calculate_match_profit, normalize_decimal_string, update_order_after_match
├── cli.py               # 命令行入口和测试
└── proxy.py             # 代理撮合: proxy_match_other_timeframes, calculate_safe_window_status
```

#### 导入方式

**✅ 推荐: 直接从 matching 导入**
```python
from order_filler.matching import (
    match_orders,                      # 执行订单撮合
    proxy_match_other_timeframes,      # 代理撮合其他时间周期
    add_to_buy_pool,                   # 买单池管理
    calculate_match_profit,            # 利润计算
)
```

**✅ 兼容: 通过 order_filler 导入**
```python
from order_filler import match_orders  # 支持lazy导入
```

**✅ 细粒度: 直接从子模块导入**
```python
from order_filler.matching.engine import match_orders
from order_filler.matching.proxy import proxy_match_other_timeframes
```

---

## ⚠️ 模块重构说明 (v2 Update)

### orders.py 已被拆分

**原 `order_filler/orders.py` 文件已不存在**, 其功能已完全重构到 `data_access/` 子包中.

#### 旧结构 (已废弃):
```text
order_filler/
├── orders.py          # ❌ 已删除
├── order_crud.py      # ❌ 已删除
├── order_queries.py   # ❌ 已删除
├── order_updates.py   # ❌ 已删除
└── order_matches.py   # ❌ 已删除
```

#### 新结构 (v2 重构):
```text
order_filler/
└── data_access/       # ✅ 新数据访问层
    ├── crud.py        # 订单CRUD: order_exists, insert_order, insert_orders, clear_all_orders, get_order_count
    ├── queries.py     # 订单查询: get_unmatched_orders, get_orders_by_pair, get_latest_order_id, 等
    ├── updates.py     # 订单更新: update_order_unmatched_qty, update_order_profit, update_order_matched_time
    └── matches.py     # 撮合管理: insert_order_match, get_order_matches_by_sell_order, 等
```

#### 导入迁移指南

**❌ 旧导入方式 (不再可用):**
```python
from order_filler import orders
orders.insert_order(...)
```

**✅ 新导入方式 (统一接口):**
```python
from order_filler.data_access import insert_order
insert_order(...)
```

所有导入都应该使用 `from order_filler.data_access import ...` 的格式.

#### 核心接口列表

数据访问层统一导出的所有函数:

- **CRUD**: `order_exists`, `insert_order`, `insert_orders`, `clear_all_orders`, `get_order_count`
- **查询**: `get_unmatched_orders`, `get_orders_by_pair`, `get_latest_order_id`, `get_latest_order_time`, `get_today_unmatched_buy_orders_total`, `get_pending_timeframes_from_db`
- **更新**: `update_order_unmatched_qty`, `update_order_profit`, `update_order_matched_time`
- **撮合**: `insert_order_match`, `get_order_matches_by_sell_order`, `get_order_matches_by_buy_order`

## ⚙️ 数据库要求

模块依赖 `order_filler` 数据表,包含以下字段:

| 字段          | 类型    | 说明                |
| ------------- | ------- | ------------------- |
| order_id      | INTEGER | 订单ID (主键)       |
| symbol        | TEXT    | 交易对              |
| side          | TEXT    | 买卖方向 (BUY/SELL) |
| quantity      | TEXT    | 交易数量            |
| price         | TEXT    | 交易价格            |
| commission    | TEXT    | 手续费              |
| time          | INTEGER | 交易时间戳          |
| unmatched_qty | TEXT    | 未撮合数量          |

## 🛠️ 核心功能

### 1. 订单同步 (sync/orders.py)

从币安 API 同步已成交订单到本地数据库:

```python
from order_filler import sync_orders_for_pair

# 同步指定交易对的订单
sync_orders_for_pair('ADAUSDC', limit=1000)
```

### 2. 订单撮合 (matching/engine.py)

对 BUY/SELL 订单进行撮合计算:

```python
from order_filler.matching import match_orders

# 撮合指定交易对的订单
stats = match_orders('ADAUSDC')
print(f"撮合笔数: {stats.matched_pairs}")
```

核心撮合引擎在 `matching/engine.py` 中实现了高效的订单匹配算法.

### 3. 利润锁定 (profit_lock.py)

计算可安全卖出的数量以保证利润:

```python
from order_filler import calculate_profit_lockable_quantity
from decimal import Decimal

# 计算可锁定利润的数量
lockable_qty = calculate_profit_lockable_quantity(
    'ADAUSDC',
    Decimal('0.1'),      # 可用数量
    Decimal('50000'),    # 当前价格
    Decimal('0.02')      # 最小利润2%
)
```

### 4. 一键操作 (workflows/sync_and_match.py)

同步和撮合一体化操作:

```python
from order_filler.workflows import sync_and_match_orders

# 一键同步和撮合
sync_and_match_orders('ADAUSDC', '15m')
```

### 5. CSV导入 (csv_importer.py)

从币安导出的 CSV 文件导入订单:

```python
from order_filler import import_binance_csv

# 导入CSV文件
stats = import_binance_csv('path/to/binance_trades.csv')
print(f"导入订单: {stats.newly_added}")
```

### 6. 订单数据管理

模块提供了完整的订单数据管理功能, 已集中到 `data_access/` 和 `matching/` 子包:

- **data_access/crud.py**: 订单的创建,读取,更新,删除操作
- **data_access/queries.py**: 复杂的订单查询功能 (查询,统计,分组等)
- **data_access/updates.py**: 批量更新订单状态 (数量,利润,撮合时间等)
- **data_access/matches.py**: 管理订单撮合详情记录 (撮合历史追踪)
- **matching/proxy.py**: 代理撮合功能,支持特殊场景的订单匹配 (1m代理其他时间周期)

## 🔧 使用方法

### 作为库导入使用

```python
from order_filler import (
    sync_orders_for_pair,
    match_orders,
    calculate_profit_lockable_quantity,
    sync_and_match_orders  # 来自 workflows/sync_and_match.py
)

# 完整工作流程
symbol = 'ADAUSDC'

# 1. 同步最新订单
sync_stats = sync_orders_for_pair(symbol, 1000)

# 2. 执行订单撮合
match_stats = match_orders(symbol)

# 3. 计算利润锁定
from decimal import Decimal
current_price = Decimal('50000')
available_qty = Decimal('0.1')

lockable_qty = calculate_profit_lockable_quantity(
    symbol, available_qty, current_price
)

print(f"可锁定利润数量: {lockable_qty}")
```

### 独立模块运行

每个模块都可以独立运行:

```bash
# 订单同步 (使用sync子包的cli入口)
p order_filler/sync/cli.py ADAUSDC 1000

# 订单撮合 (使用matching子包的cli入口)
p order_filler/matching/cli.py ADAUSDC 1m

# 利润锁定分析
p order_filler/profit_lock.py ADAUSDC 0.1 50000 0.02

# 一键同步和撮合 (使用workflows子包的编排)
p -m order_filler.workflows ADAUSDC 1m

# CSV导入
p order_filler/csv_importer.py ./binance_trades.csv
```

### 命令行入口

```bash
# 查看模块功能介绍
p -m order_filler
```

## 🔄 撮合算法

订单撮合采用以下规则:

1. **时间优先**: 按订单完成时间排序处理
2. **买单池**: BUY订单放入买单池,按价格升序排序
3. **撮合逻辑**: SELL订单与买单池中最便宜的BUY订单撮合
4. **数量冲抵**: 相互冲抵 unmatched_qty,冲抵为0时更新数据库
5. **精度保证**: 使用字符串存储价格,避免浮点精度问题

## 💰 利润锁定算法

利润锁定计算遵循以下原则:

1. **成本优先**: 按买入价格升序处理(最便宜先卖)
2. **利润保证**: 只有当前价格 >= 买入价格 × (1 + 最小利润率) 时才锁定
3. **数量限制**: 不超过可用数量和未撮合买单数量
4. **风险控制**: 确保每笔卖出都有保证的利润空间

## 🚨 安全特性

1. **Fail-Fast 原则**: 异常立即向上传播,不使用默认值掩盖错误
2. **参数验证**: 在用户入口点进行严格的参数验证
3. **类型安全**: 所有函数都有完整的类型注解
4. **金融级精度**: 使用 Decimal 和字符串处理价格数量
5. **事务保证**: 数据库操作使用事务确保一致性

## 📝 开发规范

- 遵循 CLAUDE.md 中的所有规范
- 每个函数不超过 50 行代码
- 禁止使用 try-except (除 ImportError)
- 必须使用完整的类型注解
- 使用 loguru.logger 而非 print()
- 信任调用方原则,内部函数不重复验证参数

## 🧪 测试

```bash
# 测试各个模块
p order_filler/sync/cli.py ADAUSDC 100
p order_filler/matching/cli.py ADAUSDC 1m
p order_filler/profit_lock.py ADAUSDC 0.1 50000 0.02
p -m order_filler.workflows ADAUSDC 1m
p order_filler/csv_importer.py ./binance_trades.csv
```

## 🔄 与 MEXC 模块的关系

order_filler 模块参考了 mexc_order_filler 的设计模式,专门针对币安交易所的已成交订单管理:

- 支持币安标准CSV格式和API格式
- 数据表名为 `order_filler`
- 使用币安API获取数据
- 支持币安特有的字段特性

两个模块可以并存使用,为多交易所订单管理策略提供支持.
