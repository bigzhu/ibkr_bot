# order_builder "没卖完" 检查点完整分析

## 执行摘要

禁用 `ENFORCE_PREVIOUS_SELL_VALIDATION` 后回测结果仍然相同的原因是**存在第二层隐藏的价格验证机制**,它独立于该标志,对所有情况生效.

---

## 检查点详细对比

### 检查点 1: reference_price_manager.py L154
**文件位置**: `/Users/bigzhu/Sync/Projects/mexc_bot/order_builder/reference_price_manager.py:154`

```python
if ENFORCE_PREVIOUS_SELL_VALIDATION and unmatched_price < order_price:
    raise ValueError(f"没卖完: {format_decimal(unmatched_price)}")
```

**特性**:
- 由 `ENFORCE_PREVIOUS_SELL_VALIDATION` 标志控制
- **仅在 BUY 侧且从未匹配订单获取价格时触发**
- `unmatched_price < order_price` 意味着: 前次买入价格低于本次新的买入价格
- 返回 `(unmatched_price, FromPriceSource.UNMATCHED_ORDERS)`

**禁用时的行为**:
- 该异常被跳过
- 仍然返回 `unmatched_price` 作为基准价格

---

### 检查点 2: calculation/metrics.py L52
**文件位置**: `/Users/bigzhu/Sync/Projects/mexc_bot/order_builder/calculation/metrics.py:52`

```python
if side == BUY and order_price >= from_price:
    error_msg = f"BUY 价格未下跌: {format_decimal(order_price)} >= {format_decimal(from_price)}"
    logger.info(f"业务中断: {error_msg}")
    raise ValueError(error_msg)
```

**特性**:
- **完全独立于任何标志,总是生效**
- 在所有 BUY 信号时执行
- `order_price >= from_price` 意味着: 新订单价格不低于基准价格
- 这是 BUY 逻辑的基本要求

**触发条件**:
- 当新的买入信号价格 >= 基准价格时触发
- 无论基准价格来自哪里(未匹配订单或K线)

---

### 检查点 3: calculation/core.py L93-99
**文件位置**: `/Users/bigzhu/Sync/Projects/mexc_bot/order_builder/calculation/core.py:93-99`

```python
if side == BUY and from_price < price:
    # "没卖完"错误由ENFORCE_PREVIOUS_SELL_VALIDATION控制,其他错误(信号价更低)总是抛出
    if from_price_source == FromPriceSource.UNMATCHED_ORDERS:
        if ENFORCE_PREVIOUS_SELL_VALIDATION:
            raise ValueError(f"没卖完: {format_decimal(from_price)}")
    else:
        raise ValueError(f"信号价更低: {format_decimal(from_price)}")
```

**特性**:
- 重复的价格检查,逻辑与 metrics.py 类似
- 区分两种异常情况:
  - 来自未匹配订单且 ENFORCE_PREVIOUS_SELL_VALIDATION=False: **允许通过**
  - 来自K线数据且价格更低: **总是抛出 "信号价更低"**
- 该检查在 metrics.py 之后调用

---

## 完整的函数调用流程

```
run_order_builder()
  └─ _prepare_execution_data()
      └─ calculate_qty()
          └─ calculate_price_metrics()  [metrics.py]
              │
              ├─ 获取 order_price (新订单价格)
              │   - BUY: demark_klines[-1]["high"]
              │   - SELL: demark_klines[-1]["low"]
              │
              ├─ get_optimized_from_price()  [reference_price_manager.py]
              │   │
              │   ├─ 尝试从未匹配订单获取
              │   │   └─ [检查点1] 
              │   │       if ENFORCE_PREVIOUS_SELL_VALIDATION and unmatched < order:
              │   │           raise "没卖完"
              │   │
              │   └─ 返回 (from_price, source)
              │
              └─ [检查点2] ⚠️ **总是生效**
                  if side == BUY and order_price >= from_price:
                      raise "BUY 价格未下跌"
                  
                  # 其中的逻辑:
                  # - from_price = 0.95 (前次未卖完订单)
                  # - order_price = 0.98 (新的BUY信号)
                  # - 条件: 0.98 >= 0.95 → TRUE → 抛异常
```

---

## 关键发现

### 发现 1: 两层相似但独立的检查

| 检查点 | 位置 | 条件 | 标志控制 | 触发场景 |
|--------|------|------|---------|---------|
| P1 | reference_price_manager.py:154 | `unmatched < order` | `ENFORCE_PREVIOUS_SELL_VALIDATION` | 仅从未匹配订单,且值更低 |
| P2 | metrics.py:52 | `order >= from_price` | **无** (总是生效) | 所有BUY信号 |
| P3 | core.py:93-99 | `from_price < price` | 部分控制 | 重复检查 |

### 发现 2: P2 才是真正的堡垒

关键是 **metrics.py 中的检查 (P2)** :

```python
if side == BUY and order_price >= from_price:
    raise ValueError(f"BUY 价格未下跌: ...")
```

这个检查不受任何标志控制,因此:
- 即使禁用 `ENFORCE_PREVIOUS_SELL_VALIDATION`
- P1 的异常被跳过
- **P2 仍然会因为 `order_price >= from_price` 而抛出异常**

### 发现 3: 价格回测场景

在回测中,当"没卖完"时:
- 前次BUY平均成交价: **0.95**
- 新的BUY信号价格: **0.98**
- 结果: `0.98 >= 0.95` → P2检查失败

---

## 为什么禁用标志后回测结果仍然相同?

### 场景: 未卖完的BUY重复

1. **第一次BUY**
   - 信号: BUY @ 0.95
   - 成交: 部分成交,平均价 0.93

2. **第二次信号到来**
   - 新信号: BUY @ 0.98
   - unmatched_orders: 存在,最低价 0.93
   - from_price 来源: `FromPriceSource.UNMATCHED_ORDERS`

3. **P1检查 (ENFORCE_PREVIOUS_SELL_VALIDATION)**
   ```python
   if ENFORCE_PREVIOUS_SELL_VALIDATION and 0.93 < 0.98:  # 禁用时跳过
       raise ValueError("没卖完")  # ← 被禁用,不执行
   ```

4. **P2检查 (metrics.py - 总是生效)** ⚠️ **关键障碍**
   ```python
   if side == BUY and 0.98 >= 0.93:  # from_price=0.93
       raise ValueError("BUY 价格未下跌")  # ← 总是抛出!
   ```

**结果**: 异常被抛出,第二次BUY 被阻止
**原因**: P2 不受标志控制

---

## 隐藏的检查逻辑总结

### 1. 直接的价格比较 (metrics.py:52)
- **影响**: 所有BUY信号
- **控制**: 无
- **逻辑**: 要求 `order_price < from_price` (价格必须下跌)

### 2. 条件价格比较 (core.py:93-99)
- **影响**: BUY信号且from_price来自未匹配订单或K线
- **控制**: 部分 (仅未匹配订单可被ENFORCE标志控制)
- **逻辑**: 区分异常类型

### 3. 流程中的重复验证
- reference_price_manager.py 中已经进行了初始验证
- metrics.py 中再次进行价格验证
- core.py 中第三次进行验证

---

## 完整的错误消息追踪

当禁用 `ENFORCE_PREVIOUS_SELL_VALIDATION` 时:

```
1. run_order_builder()
   └─ _prepare_execution_data()
       └─ calculate_qty()
           ├─ calculate_price_metrics()
           │   ├─ order_price = 0.98 (新BUY信号)
           │   ├─ from_price = 0.93 (来自未匹配订单)
           │   └─ [P2检查] 0.98 >= 0.93 → 抛出异常
           │       ❌ "BUY 价格未下跌: 0.98 >= 0.93"
           │
           └─ 异常向上传播到 run_order_builder 的 except 块
               └─ update_trading_log(error="BUY 价格未下跌: ...")
                   └─ 返回 ErrorResult(action="ERROR", ...)
```

---

## 为什么这个设计存在?

### P2的目的 (metrics.py 中的检查):
- **保护BUY逻辑的基本前提**: 新的买入信号必须低于成本
- **适用范围**: 无论数据源如何,都要验证

### P1的目的 (reference_price_manager.py):
- **特定场景**: 仅在从历史订单获取价格时
- **细粒度控制**: 允许用户选择是否允许多次分阶段建仓
- **有限影响**: 即使禁用,P2仍然起保护作用

### 设计的防御层次:
1. **P1**: 明确的"未卖完"警告 (可选,由标志控制)
2. **P2**: 隐含的价格逻辑检查 (强制,无法禁用)
3. **P3**: 重复验证 (冗余安全网)

---

## 建议

要真正禁用"没卖完"的检查,需要修改 metrics.py 中的条件:

```python
# 当前: 总是检查
if side == BUY and order_price >= from_price:
    raise ValueError(f"BUY 价格未下跌: ...")

# 建议: 也受标志控制
if side == BUY and order_price >= from_price:
    if ENFORCE_PREVIOUS_SELL_VALIDATION or from_price_source == FromPriceSource.KLINES:
        raise ValueError(f"BUY 价格未下跌: ...")
```

这样才能真正实现"允许多次分阶段建仓"的功能.
