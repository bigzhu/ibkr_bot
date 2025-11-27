# Backtester

状态: 规划中, 已有最小可用实现; 当前阶段仅维护文档与设计, 不新增代码实现.

本目录用于回测系统的设计与规划, 并记录已实现的功能, 使用方式与局限. 目标是在实现前明确范围, 架构, 数据模型, 撮合规则与验证方式, 以便后续小步实现与可验证演进.

## 快速开始
- 同步历史 K 线到本地数据库:
  - `p backtester/klines_syncer.py ADAUSDC 1h --months 12`
  - 或模块方式: `p -m backtester.klines_syncer ADAUSDC 1h --months 12`
- 运行回测:
  - `p -m backtester ADAUSDC 1h --cash 10000`

注: `p` 为 `uv run python` 的别名; 遵循仓库规范, 不直接使用 `python`.

## 已实现功能 (v0)
- CLI 入口: `backtester/__main__.py`
  - 命令: `p -m backtester SYMBOL TIMEFRAME --cash 10000`
  - 解析参数后构造 `BacktestEngine` 并执行 `engine.run()`.
- 回测引擎: `backtester/engine.py`
  - 从数据库加载 K 线为 `pandas.DataFrame`, index 为 `open_time (UTC)`.
  - 在每根 K 线上推进事件循环: 更新 `MockBinanceClient` 的 tick, 检查并触发挂单, 调用策略 `next()`.
  - 回测前清空相关结果表: `filled_orders`, `order_matches`, `trading_logs`.
  - 结束时以收盘价计算组合净值: `Broker.get_portfolio_value` 并输出.
- 模拟券商: `backtester/broker.py`
  - 账户与持仓: 现金 `cash`, 持仓字典 `positions`.
  - 手续费: 固定比例 `commission` (默认 0.1%).
  - 下单: `buy(symbol, qty, price)`, `sell(symbol, qty, price)` 立即成交, 仅现金与持仓校验, 无滑点与延迟.
  - 组合估值: `get_portfolio_value({symbol: price})`.
- 模拟客户端: `backtester/mock_client.py`
  - 模拟 `python-binance` 客户端最小子集: `get_asset_balance`, `get_symbol_ticker`, `get_open_orders`, `get_all_orders`, `create_order`, `cancel_order`, `get_exchange_info`, `get_klines`.
  - 订单: 支持市价即时成交; `STOP_LOSS` 作为挂单, 随行情触发; 记录到内存 `executed_orders` 与数据库 `filled_orders` 表.
  - 行情: 使用回测数据帧驱动, `update_tick(i)` 同步当前 K 线; `get_klines` 将 DataFrame 转为 Binance API 数组格式.
- 策略适配器: `backtester/strategy.py`
  - `Strategy` 基类: `init`, `next` 框架方法.
  - `DemarkStrategy`: 在 `init` 中 monkey patch `binance_api.common.get_configured_client` 及相关指标模块引用 (含 `td_iven`), 让内部下单走 `MockBinanceClient`.
  - 在 `next` 中每根 K 线调用已有的 `order_builder.app.run_order_builder(symbol, timeframe)` 执行真实策略逻辑.
- 数据加载: `backtester/data_loader.py`
  - 从 `backtest_klines` 读取指定 `symbol` 与 `timeframe` 的历史数据.
  - 列名清洗为常用字段: `open, high, low, close, volume, ...`, 并设置 `DatetimeIndex`.
- 数据同步: `backtester/klines_syncer.py`
  - 从真实 Binance API 拉取历史 K 线写入 `backtest_klines` 表; 支持按月回溯批量同步; 幂等插入.
- 数据库支持:
  - 表: `backtest_klines` (见 `database/schema.py` 与迁移 `v19`).
  - 索引: `idx_backtest_klines_symbol_timeframe_open_time`.
  - 回测开始前清理结果表以便复现.

## 模块结构
- `__main__.py`: CLI 入口, 构造并运行引擎.
- `engine.py`: 主循环, 数据准备与挂单检查.
- `broker.py`: 账户, 持仓与成交结算.
- `mock_client.py`: 模拟交易所与订单接口.
- `strategy.py`: 策略接口与适配器到现有策略代码.
- `data_loader.py`: 从数据库加载回测数据.
- `klines_syncer.py`: 拉取并写入回测 K 线数据.

## 当前撮合与规则 (v0)
- 市价单: 以当前 tick 的 `close` 价即时成交, 仅收取固定手续费, 不考虑滑点.
- 停损单: 作为挂单, 由引擎与 `MockBinanceClient` 随行情高低触发, 以 stop 价成交.
- 资金与持仓: 买入需现金充足; 卖出需持仓充足; 不支持空头.
- 账户货币: 以 quote 计价, 示例中默认 USDC.

## 限制与待办
- 未实现: 限价单, 部分成交, 滑点模型, 延迟与队列, 多标的组合, 详细 PnL 归因与报告.
- 策略接口耦合: 通过 monkey patch 嵌入现有策略, 后续可收敛到统一 API.
- 数据完整性: 依赖 `klines_syncer` 先行同步.

## 里程碑建议
- M1: 保持当前最小可用闭环; 增加最小集成测试与指标导出 CSV.
- M2: 完善撮合 (限价单, 部分成交, 滑点); 交易明细落库与导出.
- M3: 指标与可视化; 统一输出结构; 复现实验配置快照.
- M4: 参数搜索与样本外评估.

## 参考
- `database/schema.py`: 回测表与索引定义.
- `scripts/migrate_database.py`: 迁移 v19 创建 `backtest_klines` 表.
