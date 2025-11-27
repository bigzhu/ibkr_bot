"""EMA指标业务封装模块

提供包含币安API调用的业务封装函数,方便外部直接调用.
封装层负责数据获取,技术层负责指标计算,职责分离清晰.
遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except
"""

from decimal import Decimal

from loguru import logger

from ibkr_api.common import get_configured_client
from ibkr_api.get_klines import klines
from indicators.ema.ema import calculate_ema


def ema_with_ibkr_api(
    symbol: str, timeframe: str, period: int = 20, price_field: str = "close"
) -> Decimal:
    """通过币安API获取数据并计算EMA指标 - 业务封装函数

    这是业务封装函数,负责API调用和数据获取,然后调用纯技术函数计算指标.
    适合需要直接从币安获取数据的业务场景.

    Args:
        symbol: 交易对符号,如 "ADAUSDC", "BTCUSDT"
        timeframe: 时间周期格式,如 "1m", "5m", "1h", "1d"
        period: EMA计算周期,默认20
        price_field: 计算所使用的价格字段,默认 "close"

    Returns:
        Decimal: 最新一根K线的 EMA(period) 数值
    """
    client = get_configured_client()
    klines_data = klines(client, symbol=symbol.upper(), interval=timeframe, limit=250)

    if not klines_data:
        raise ValueError(f"无法获取{symbol} {timeframe}的K线数据")

    logger.info(f"📊 获取到 {len(klines_data)} 根K线数据")

    ema_value = calculate_ema(klines_data, period=period, price_field=price_field)
    logger.info(f"💹 EMA({period})[{price_field}]: {ema_value:.6f}")

    return ema_value


if __name__ == "__main__":
    # 允许独立运行进行快速测试: python -m ema.binance_ema BTCUSDT 1h 20
    import sys

    if len(sys.argv) < 3:
        print("用法: python -m ema.binance_ema SYMBOL TIMEFRAME [PERIOD] [PRICE_FIELD]")
        print("示例: python -m ema.binance_ema BTCUSDT 1h 20 close")
        sys.exit(1)

    symbol = sys.argv[1].upper()
    timeframe = sys.argv[2]
    period = int(sys.argv[3]) if len(sys.argv) >= 4 else 20
    price_field = sys.argv[4] if len(sys.argv) >= 5 else "close"

    logger.info(f"🚀 开始计算 {symbol} {timeframe} 的EMA({period})[{price_field}]")

    value = ema_with_ibkr_api(symbol, timeframe, period, price_field)
    logger.info("=" * 50)
    logger.info(
        f"📊 {symbol} {timeframe} EMA({period})[{price_field}] 结果: {value:.6f}"
    )
    logger.info("=" * 50)
