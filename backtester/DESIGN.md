# Backtester Design

状态: 设计草案, 已融合当前实现; 设计冻结前不落地新代码.

本设计基于仓库中已存在的回测实现 (engine, broker, mock_client, strategy adapter, data layer), 在此基础上补齐边界与演进路线.

## 目标与非目标

- 目标 v1: 以 OHLCV 为驱动, 复用现有策略逻辑, 能完整跑通下单与成交, 输出最终净值, 可重复.
- 非目标 v1: 订单簿级撮合, 高频延迟仿真, 杠杆与资金费, 复杂滑点/流动性模型.

## 核心功能

### k 线数据同步

klines_syncer.py 用于同步币安的历史K线数据到本地的数据库表 `backtest_klines` 中, 支持增量更新.

避免回测运行时候反复查询币安API而被屏蔽, 并且提高回测的速度.

### 术语说明 (Glossary)

- symbol: 交易对符号, 例如 ADAUSDC
- base: 基础资产, 例如 ADA
- quote: 计价资产, 例如 USDC
- qty: 下单数量, 单位 base
- price: 价格(或 stopPrice), 单位 quote/base
- notional: 名义金额, qty × price, 单位 quote
- orderId: 整型订单ID, 每次回测开始时重置为起始值(默认 1), 单调递增, 不回绕
- clientOrderId: 客户端订单ID, 由交易系统传入; 未传则不返回该字段
- time: 订单创建时间, 使用当前 K 线 open_time, 单位毫秒
- updateTime: 最近一次状态更新时间, 成交或取消时为当前 K 线 open_time, 单位毫秒
- status: NEW(挂单), FILLED(已成交), CANCELED(已取消)
- initial_cash: 用户为回测指定的初始投入资金(quote 数量), 例如 --cash 10000

### Mock Interface Design

- 范围与优先级 (run_order_builder 视角)
  - 必需: get_klines, get_all_orders, get_open_orders, create_order, cancel_order, get_account

- 设计原则
  - 时序对齐: 价格读取与撮合全部以"当前 tick 的 K 线"驱动; STOP_LOSS 触发按高/低穿越 stopPrice, 成交价记为 stopPrice
  - 数据来源: 优先内存 DataFrame; 必要时 DB 兜底 (如历史订单同步)
  - 一致性: 余额由 Broker.cash 与 Broker.positions 映射出账户视图; 历史订单仅暴露回测期间产生的数据
  - Fail-fast: 输入缺失或不合法直接抛错; 日志记录但不吞异常

#### 接口规格 (逐项补充)

- get_klines(symbol, interval, limit, startTime?, endTime?)
  - 用途: DeMark 指标计算
  - 返回: Binance 数组格式 K 线 (严格沿用 DB 存储的真实币安字段值与类型)
  - 数据源: 本地数据库 backtest_klines (由 klines_syncer.py 同步);Mock 不做任何重采样/归整/填补/字段改写
  - 过滤与边界: 严格按传入的 startTime/endTime/limit 过滤并截断;不做周期归整或边界修正;空结果返回空数组
  - 排序: 始终按 open_time 升序返回
  - 错误: 参数非法直接抛出(fail-fast),不做修正
  - 测试: 覆盖仅 startTime,仅 endTime,start+end,仅 limit 与空数据场景(确认"无加工直通")

- get_all_orders(symbol, limit?, orderId?)
  - 用途: 同步历史订单
  - 请求参数:
    - symbol: required (uppercase)
    - limit: optional, if provided, truncate at limit; if absent, return all
    - orderId: optional, inclusive filter (>=) for incremental sync
  - 返回: 已成交订单列表; 支持从 orderId 增量
  - 数据源: 回测期间产生的已成交记录 (Mock Exchange 内部存储或独立回测表)
  - 时序: 订单按 orderId 升序; 批次边界稳定
  - 边界: 无数据返回空列表
  - 与实盘差异: 不强制 1000 限制; 仅包含回测期间数据
  - 测试: 增量过滤, 排序稳定, 无重复

- get_open_orders(symbol?)
  - 用途: 查询未成交挂单, 批量取消前查询
  - 请求参数:
    - symbol: optional (consistent with Binance). No timeframe filter supported
  - 返回: 挂单列表 pending_orders (status=NEW), 原样包含 clientOrderId
  - 字段结构: 与 create_order 返回一致 (status=NEW)
  - 排序: 建议按 orderId 升序
  - 时序: 读取时为最新状态
  - 边界: 无数据返回空列表
  - 测试: symbol 过滤, 字段完整性

- create_order(symbol, side, type, quantity, price?, stopPrice?, timeInForce?, newClientOrderId?)
  - 用途: 下单
  - 请求参数:
    - symbol: required, uppercase string, e.g. ADAUSDC
    - side: required, BUY | SELL
    - type: required, only STOP_LOSS supported in v0 (others error)
    - quantity: required, string (base units)
    - stopPrice: required, string (quote/base)
    - price: optional, ignored for STOP_LOSS
    - timeInForce: optional, ignored
    - newClientOrderId: optional, passthrough
  - 语义:
    - 当前系统仅支持 STOP_LOSS: 创建挂单入 pending_orders, 返回 NEW; 随行情触发成交.
    - 非 STOP_LOSS: v0 不实现/不使用 (后续里程碑可考虑支持即时成交语义).
  - 返回字段与类型 (最小集):
    - orderId(int), symbol(str), type(str=STOP_LOSS), side(str)
    - price(str="0"), stopPrice(str), origQty(str), executedQty(str="0")
    - cummulativeQuoteQty(str="0"), status(str="NEW"), clientOrderId(str, 仅在传入 newClientOrderId 时返回)
    - time(int ms), updateTime(int ms) = 当前 K 线 open_time (下单时刻)
  - 余额校验与占用:
    - BUY: 需 quote 可用余额(free)>= qty × stopPrice;下单时占用相应 quote 数量(记入占用余额(locked))
    - SELL: 需 base 可用余额(free)>= qty;下单时占用相应 base 数量(记入占用余额(locked))
    - 可用余额(free)不持久化,get_account 返回时按 free = total - locked 计算
    - 余额不足: 抛出 BinanceAPIException(code=-2010) 以保持兼容
  - 边界: 参数缺失抛错; 数量/名义值等限制由上游检查保障
  - 测试: STOP_LOSS 挂单路径, 参数校验, 返回字段完整性

- cancel_order(symbol, orderId | origClientOrderId)
  - 用途: 批量取消, 释放余额
  - 请求参数:
    - symbol: required
    - orderId: optional, at least one of orderId or origClientOrderId
    - origClientOrderId: optional; if both present, prefer orderId
  - 语义: 从 pending_orders 移除; 返回 CANCELED 订单字典
  - 返回字段与类型 (最小集):
    - orderId(int), symbol(str), type(str=STOP_LOSS), side(str)
    - price(str or "0"), stopPrice(str), origQty(str), executedQty(str)
    - cummulativeQuoteQty(str), status(str="CANCELED"), clientOrderId(str, 若创建时未传则不返回)
    - time(int ms), updateTime(int ms) = 取消时刻 (当前 K 线 open_time)
  - 余额释放:
    - BUY: 释放已占用的 quote(占用余额 locked 减少); SELL: 释放已占用的 base(占用余额 locked 减少)
  - 错误: 未找到订单直接抛错 (fail-fast)
  - 测试: 按 orderId 与 clientOrderId 两种路径, 幂等性校验

- get_account()
  - 用途: 获取余额 (被 get_balance -> get_user_balance 使用)
  - 返回: { balances: [{asset, free, locked}, ...] }
  - 数据源: 模拟币安订单系统的内部账户状态(由 Broker 结算驱动), 下单/成交后即时生效; 不读取交易系统表
  - 边界: 未配置资产返回 0; 结构完整性保证
  - 测试: BUY/SELL 两方向余额随成交变化正确更新

#### 扩展模板 (新增接口时沿用)
- 用途:
- 签名:
- 输入校验:
- 返回结构:
- 数据源与时序:
- 错误与边界:
- 与实盘差异:
- 测试要点:

### 模拟币安订单系统 (Mock Exchange)

- 目标与范围
  - 目标: 以最小一致语义支撑 get_all_orders, get_open_orders, create_order, cancel_order 四个接口, 服务于回测流程.
  - 非目标: 订单簿级撮合, 部分成交, 滑点/延迟, 杠杆/资金费; 这些作为后续里程碑.

- 状态模型
  - 内存状态: pending_orders[], executed_orders[], order_id_counter.
  - 数据库交互: 不写入交易系统的 filled_orders/order_matches; 如需持久化可使用独立回测表或仅内存存储; 交易日志由上游模块负责.
  - 账户状态: Mock Exchange 维护 balances 视图:
    - 总量来源: Broker (cash 与 positions) 为总余额真源
    - 初始总量: total_quote = initial_cash; total_base = 0; quote 资产代号来自 trading_symbols.quote_asset, base 资产代号来自 trading_symbols.base_asset
    - 占用余额(locked): 挂单占用以 locked 形式记录(quote/base)
    - 可用余额(free): 在 get_account 响应时按需计算 free = total - locked(不持久化)
    - 成交: 通过 Broker.buy/sell 更新总量, 同步减少对应占用余额(locked);取消: 仅释放占用余额(locked)
    - get_account: 返回 balances 数组, 每项包含 {asset, free(可用余额), locked(占用余额)};不读取交易系统表

- 接口与语义对齐
- create_order
    - 当前系统仅支持 STOP_LOSS: 创建挂单入 pending_orders, 返回 NEW; 随行情触发成交.
    - 非 STOP_LOSS: v0 不实现/不使用 (后续里程碑可考虑支持即时成交语义).
  - get_open_orders
    - 返回 pending_orders; 可按 symbol 过滤(与币安一致, timeframe 不在参数中); 不做 timeframe 过滤; 原样返回 clientOrderId.
  - cancel_order
    - 按 orderId 或 origClientOrderId 从 pending_orders 移除, 返回 CANCELED 状态订单字典.
  - get_all_orders
    - 返回回测期间产生的已成交订单列表; 支持 orderId 增量与稳定排序.
    - 返回字段规范(最小集):
      - orderId(int), symbol(str), type(str=STOP_LOSS), side(str)
      - price(str="0"), stopPrice(str), origQty(str), executedQty(str), cummulativeQuoteQty(str)
      - status(str="FILLED"), time(int ms), updateTime(int ms), clientOrderId(str 可选)
    - 取值约定:
      - executedQty = origQty(v0 全量成交)
      - cummulativeQuoteQty = Decimal(origQty) × Decimal(stopPrice)(以 stopPrice 作为成交价)
      - price 固定为 "0"(触发价在 stopPrice 字段体现)
    - 排序: 始终按 orderId 升序; 过滤: orderId 为包含式(>=)
    - 数量限制: 不强制 1000 限制; 若传入 limit 则按 limit 截断, 未传入则返回全部
    - 范围: 仅返回已成交(FILLED)记录, 不返回已取消记录

- 订单生命周期与时序
  - 状态流转: NEW -> FILLED | CANCELED (v0 无部分成交).
  - 触发模型: 
    - BUY: 当本根 K 线的 high >= stopPrice 时触发
    - SELL: 当本根 K 线的 low <= stopPrice 时触发
    - 边界: 包含等于 (>= / <=)
  - 成交规范:
    - 成交价 = stopPrice
    - 数量: v0 全量成交, 不做部分成交
    - 时间戳: transactTime/updateTime 使用当前 K 线 open_time (毫秒)
    - 同根多单顺序: 按 orderId 升序依次处理
    - 新挂单评估时机: 策略执行完成后立刻在当前 K 线上评估, 允许同根触发
- 引擎顺序: update_tick -> 策略 next() -> 可能下新单/取消旧单 -> 触发挂单.

- 交易流程
  - 接收 create_order 的挂单请求 (仅 STOP_LOSS 类型, 作为挂单进入 pending_orders)
  - 挂单可能成交: 随后 K 线数据满足触发条件 (高/低穿越 stopPrice,包含等于)
  - 挂单可能取消: 接收到 cancel_order 请求时从 pending_orders 移除并返回 CANCELED
- 挂单成交后:
    - 调整账户余额: 通过 Broker 结算更新总余额;不考虑手续费
      - 记号: base=基础资产总余额, quote=计价资产总余额, qty=下单数量(单位 base), price=成交价(quote/base)
      - BUY: base' = base + qty; quote' = quote - qty × price
      - SELL: base' = base - qty; quote' = quote + qty × price
    - 同步占用余额(locked): 对应挂单释放 locked;可用余额(free)在 get_account 响应时按 total - locked 计算
    - 生成一条已成交记录 (Mock Exchange 内部存储 executed_orders; 不写入交易系统的 filled_orders)
    - get_all_orders 仅返回已成交记录; 用于同步与撮合
  - get_open_orders 返回当前处于挂单状态的记录 (pending_orders)

- ID 与客户端标识
  - orderId: 单调增长计数器; 每次回测启动时重置为起始值(实现可配置, 默认 1); 不回绕.
  - clientOrderId: 由交易系统传入; Mock 不生成/不强加规则; 原样存储与返回.

- 精度与限制
  - 精度与名义额校验由上游 precision_handler 与 DB 配置完成; Mock 信任入参, 仅记录.
  - 手续费: Mock Exchange 不考虑手续费(fee=0).
  - 余额与持仓变化通过 Broker 结算; Mock 不直接改动余额, 仅通过 Broker.buy/sell.

- 错误与边界
  - 未找到订单,重复取消,非法参数: 直接抛出异常 (fail-fast), 记录 warning/error 日志.
  - 幂等性: 取消同一订单多次视为错误; get_all_orders 增量需稳定且无重复.

- 可观测性
  - Backtest Trace 日志: 下单,触发,成交,取消,同步等关键事件都记录摘要与关键字段.

- 测试计划
  - 单测: create FILLED, create STOP_LOSS -> trigger, cancel by orderId/clientId, open_orders 过滤, all_orders 增量.
  - 集成: BUY -> STOP_LOSS SELL 触发 -> 批量取消旧单 -> 同步增量 -> 精度/名义额校验由上游通过.

- 会话重置流程 (Backtest Session Reset)
  - 重置 orderId 计数器到起始值(默认 1)
  - 清空 pending_orders 与 Mock 内部的已成交记录存储
  - 初始化账户状态: 仅维护占用余额(locked)=0;总余额来自 Broker(base/quote)
    - 初始化总额: total_quote = initial_cash, total_base = 0(仅设置 quote 初始余额, base 初始为 0)
    - get_account 响应时按需计算可用余额(free)= total - locked(不持久化)
    - 仅为当前回测的 symbol 返回 base/quote 两个资产项
  - 不写入交易系统的 filled_orders/order_matches 等表; 与交易系统表的清理互不依赖
  - 清理任何与上次回测相关的临时缓存, 确保可重复性

- 里程碑与扩展
  - v1: 即时成交 + STOP_LOSS 触发, 无部分成交.
  - v2: 限价与部分成交, 简单滑点模型.
  - v3: 延迟/撮合队列, 订单簿近似, 多标的组合.
