"""ATR指标业务封装模块

提供包含币安API调用的业务封装函数,方便外部直接调用.
封装层负责数据获取,技术层负责指标计算,职责分离清晰.
遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except
"""

from loguru import logger

if __name__ == "__main__":
    try:
        from shared.path_utils import ensure_project_root_for_script
    except ImportError:
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from shared.path_utils import ensure_project_root_for_script

    ensure_project_root_for_script(__file__)

from ibkr_api.common import get_configured_client
from ibkr_api.get_klines import klines
from indicators.atr.atr import calculate_atr, calculate_atr_percentage


def atr_with_ibkr_api(
    symbol: str, timeframe: str, period: int = 14
) -> tuple[float, float]:
    """通过币安API获取数据并计算ATR指标 - 业务封装函数

    这是业务封装函数,负责API调用和数据获取,然后调用纯技术函数计算指标.
    适合需要直接从币安获取数据的业务场景.

    Args:
        symbol: 交易对符号,如 "ADAUSDC", "BTCUSDT"
        timeframe: 时间周期格式,如 "1m", "5m", "1h", "1d"
        period: ATR计算周期,默认14

    Returns:
        tuple[float, float]: (ATR值, ATR百分比)

    Raises:
        ValueError: 当API配置或数据有问题时抛出异常
    """

    # 获取币安API客户端
    client = get_configured_client()

    # 获取K线数据 (ATR计算需要period+1根K线,多获取几根确保数据充足)
    limit = period + 5  # period+1根用于计算,额外4根作为缓冲
    klines_data = klines(client, symbol, timeframe, limit=limit)

    if not klines_data:
        raise ValueError(f"无法获取{symbol} {timeframe}的K线数据")

    logger.info(f"📊 获取到 {len(klines_data)} 根K线数据")

    # 计算ATR指标
    atr_value = calculate_atr(klines_data, period)
    atr_percentage = calculate_atr_percentage(klines_data, period)

    logger.info(f"💹 ATR({period}): {atr_value:.6f}")
    logger.info(f"📈 ATR百分比: {atr_percentage:.2f}%")

    return float(atr_value), float(atr_percentage)


if __name__ == "__main__":
    """测试ATR业务封装模块"""
    import sys

    if len(sys.argv) != 3:
        logger.info("用法: p atr/binance_atr.py SYMBOL TIMEFRAME")
        logger.info("示例: p atr/binance_atr.py ADAUSDC 15m")
        sys.exit(1)

    symbol = sys.argv[1].upper()
    timeframe = sys.argv[2]

    logger.info(f"🚀 开始计算 {symbol} {timeframe} 的ATR指标")

    atr_value, atr_percentage = atr_with_ibkr_api(symbol, timeframe)

    logger.info("=" * 50)
    logger.info(f"📊 {symbol} {timeframe} ATR分析结果:")
    logger.info(f"💹 ATR值: {atr_value:.6f}")
    logger.info(f"📈 ATR百分比: {atr_percentage:.2f}%")
    logger.info("=" * 50)
