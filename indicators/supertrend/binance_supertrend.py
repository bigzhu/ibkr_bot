"""SuperTrend 指标业务封装模块."""

from __future__ import annotations

from decimal import Decimal

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m indicators.supertrend.binance_supertrend` 运行该模块, 无需手动修改 sys.path"
    )

from loguru import logger

from binance_api.common import get_configured_client
from binance_api.get_klines import klines
from indicators.supertrend.supertrend import (
    SuperTrendColor,
    calculate_supertrend_signal,
)
from shared.types import Kline


def supertrend_with_binance_api(
    symbol: str,
    timeframe: str,
    period: int = 10,
    multiplier: Decimal | float | int = Decimal("3"),
) -> tuple[SuperTrendColor, Decimal, list[Kline]]:
    """通过币安 API 计算最新的 SuperTrend 信号."""

    client = get_configured_client()
    limit = max(period * 3, period + 30)
    klines_data = klines(client, symbol, timeframe, limit=limit)

    if not klines_data:
        raise ValueError(f"无法获取 {symbol} {timeframe} 的 K 线数据")

    # 排除尚未收盘的最后一根
    completed = klines_data[:-1] if len(klines_data) > 1 else klines_data

    if len(completed) < period + 2:
        raise ValueError("SuperTrend 计算数据不足")

    color, value = calculate_supertrend_signal(
        completed,
        period=period,
        multiplier=multiplier,
    )
    logger.info(
        "SuperTrend(%s %s) -> %s %.6f",
        symbol,
        timeframe,
        color,
        float(value),
    )
    return color, value, completed


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        logger.info("用法: p supertrend/binance_supertrend.py SYMBOL TIMEFRAME")
        sys.exit(1)

    sym = sys.argv[1].upper()
    tf = sys.argv[2].lower()

    color, value, _ = supertrend_with_binance_api(sym, tf)
    logger.info("SuperTrend 信号: %s -> %s %.6f", sym, color, float(value))
