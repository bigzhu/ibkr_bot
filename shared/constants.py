"""
共享常量定义

定义系统中使用的字符串常量,避免循环导入问题.
"""

from enum import Enum

# 订单方向常量
BUY = "BUY"
SELL = "SELL"

# 订单状态常量
ORDER_STATUS_NEW = "NEW"
ORDER_STATUS_PARTIALLY_FILLED = "PARTIALLY_FILLED"
ORDER_STATUS_FILLED = "FILLED"
ORDER_STATUS_CANCELED = "CANCELED"
ORDER_STATUS_REJECTED = "REJECTED"
ORDER_STATUS_EXPIRED = "EXPIRED"

# 订单类型常量
ORDER_TYPE_MARKET = "MARKET"
ORDER_TYPE_LIMIT = "LIMIT"
ORDER_TYPE_STOP_LOSS = "STOP_LOSS"
ORDER_TYPE_STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
ORDER_TYPE_TAKE_PROFIT = "TAKE_PROFIT"
ORDER_TYPE_TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"


# from_price 来源常量
class FromPriceSource(str, Enum):
    """数据来源常量,替代易错的魔法字符串"""

    KLINES = "klines"
    UNMATCHED_ORDERS = "unmatched_orders"


# DeMark 指标配置
# Setup 计数条件: 两种实现方式的切换开关
# True: 传统方式 - 基于收盘价严格比较 (close[n] > close[n-4] 或 close[n] < close[n-4])
#   优点: 符合行业标准,避免高低影线噪声,信号更稳定
#   缺点: 信号确认较晚(需等待收盘)
# False: 当前方式 - 基于高低价比较 (high[n] >= high[n-4] 或 low[n] <= low[n-4])
#   优点: 信号识别更快(影线即触)
#   缺点: 噪声较高,容易提前触发 Setup/Countdown
DEMARK_USE_CLOSE_PRICE_COMPARISON = True

# 订单管理策略
# True: DeMark信号最终方向确定后, 取消所有反方向未成交订单
# False: 不做自动取消, 保持现有挂单
CANCEL_OPPOSITE_OPEN_ORDERS_AFTER_SIGNAL = False

# 强制 BUY 单开关
# True: SELL 信号时额外下 BUY 单
#   - BUY 信号: 正常下 BUY 单(不受影响)
#   - SELL 信号: 先下 BUY 单, 有持仓时再下 SELL 单
#   - NONE 信号: 不下单(不受影响)
# False: 信号按原始逻辑处理(BUY→BUY, SELL→SELL, NONE→不下单)
ALWAYS_TRY_BUY_ORDER = False

# BUY 订单 last_price 计算策略
# True: last_price 取 min(未匹配订单最低价, DeMark K线最高价)
#   - 确保 last_price 不高于当前 K 线高点
#   - 适用于快速下跌行情, 避免使用过高的历史持仓价
# False: last_price 优先使用未匹配订单最低价, 无持仓时回退到 K 线高点
#   - 基于实际持仓成本计算
USE_MIN_LAST_PRICE_FOR_BUY = False
