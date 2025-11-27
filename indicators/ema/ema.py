"""EMA (Exponential Moving Average) 指标计算模块

提供EMA(指数移动平均)的纯计算逻辑,不包含任何外部依赖(如交易所API).
遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except
"""

from decimal import Decimal, getcontext

from shared.types import Kline

# 提升小数精度,以避免浮点累积误差(与ATR模块保持一致风格)
getcontext().prec = 28


def calculate_ema(
    klines_data: list[Kline], period: int = 20, price_field: str = "close"
) -> Decimal:
    """计算标准EMA(与TradingView/TA-Lib一致的定义),返回**最新一根K线的EMA值**

    计算方式:
        1) 用前 period 根K线的简单平均(SMA)作为EMA初始值

    Args:
        klines_data: K线数据列表,元素类型为 shared.types.Kline
        period: EMA周期,默认20
        price_field: 价格字段,默认 "close", 可选 "open" / "high" / "low" / "close"

    Returns:
        Decimal: 最新一根K线的EMA(period) 数值

    Raises:
        ValueError: 当数据不足或参数非法时
    """
    if period <= 0:
        raise ValueError(f"period 必须为正整数, 实际: {period}")

    if not klines_data:
        raise ValueError("K线数据为空")

    if len(klines_data) < period:
        raise ValueError(
            f"K线数量不足以计算EMA, 需要至少 {period} 根, 实际 {len(klines_data)} 根"
        )

    prices = [_extract_price(k, price_field) for k in klines_data]

    # 1) 初始EMA使用前 period 根的SMA
    initial_segment = prices[:period]
    sma = sum(initial_segment) / Decimal(str(period))
    ema_prev = sma

    # 2) 递推计算EMA
    alpha = Decimal(2) / Decimal(period + 1)
    one_minus_alpha = Decimal(1) - alpha

    for price in prices[period:]:
        ema_prev = price * alpha + ema_prev * one_minus_alpha

    return ema_prev


# ============ 内部工具函数 ============
def _extract_price(kline: Kline, field: str) -> Decimal:
    """Pull a single price field from the kline dict and cast to Decimal."""
    return Decimal(str(kline[field]))


# def _extract_price(kline: Kline, field: str) -> Decimal:
#     if field not in {"open", "high", "low", "close"}:
#         raise ValueError(f"不支持的price_field: {field}")
#     value = getattr(kline, field, None)
#     if value is None:
#         raise ValueError(f"Kline缺少字段: {field}")
#     # 确保以 Decimal 进行精确计算
#     return Decimal(str(value))
