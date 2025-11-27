"""ATR (Average True Range) 指标计算模块

提供ATR指标的纯技术计算功能,完全独立于外部依赖.
ATR用于衡量价格波动性,是风险管理和止损设置的重要指标.
遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except
"""

from decimal import Decimal

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

from shared.types import Kline


def calculate_atr(klines_data: list[Kline], period: int = 14) -> Decimal:
    """计算ATR (Average True Range) 指标"""
    highs, lows, closes = _prepare_price_series(klines_data, period)
    true_ranges = _calculate_true_ranges(highs, lows, closes)

    if len(true_ranges) < period:
        raise ValueError(
            f"True Range数据不足,需要至少{period}个,实际{len(true_ranges)}个"
        )

    recent_trs = true_ranges[-period:]
    return sum(recent_trs) / Decimal(str(period))


def calculate_atr_percentage(klines_data: list[Kline], period: int = 14) -> Decimal:
    """计算ATR百分比 (ATR相对于当前价格的百分比)"""
    atr = calculate_atr(klines_data, period)
    current_price = _extract_price(klines_data[-1], "close")

    if current_price == 0:
        raise ValueError("当前价格不能为0")

    return (atr / current_price) * Decimal("100")


def _prepare_price_series(
    klines_data: list[Kline], period: int
) -> tuple[list[Decimal], list[Decimal], list[Decimal]]:
    """Extract high/low/close sequences required by ATR calculation."""
    if not klines_data:
        raise ValueError("K线数据不能为空")
    if len(klines_data) < period + 1:
        raise ValueError(f"K线数据不足,需要至少{period + 1}根,实际{len(klines_data)}根")

    highs = [_extract_price(kline, "high") for kline in klines_data]
    lows = [_extract_price(kline, "low") for kline in klines_data]
    closes = [_extract_price(kline, "close") for kline in klines_data]
    return highs, lows, closes


def _calculate_true_ranges(
    highs: list[Decimal],
    lows: list[Decimal],
    closes: list[Decimal],
) -> list[Decimal]:
    """Compute True Range per bar following ATR definition."""
    true_ranges: list[Decimal] = []
    for i in range(1, len(highs)):
        high = highs[i]
        low = lows[i]
        prev_close = closes[i - 1]

        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        true_ranges.append(max(tr1, tr2, tr3))
    return true_ranges


def _extract_price(kline: Kline, field: str) -> Decimal:
    """Pull a single price field from the kline dict and cast to Decimal."""
    return Decimal(str(kline[field]))


if __name__ == "__main__":
    """测试ATR模块"""
    logger.info("ATR指标模块 - 技术计算入口")
    logger.info(
        "使用带API的数据获取请运行: uv run python -m indicators.atr SYMBOL TIMEFRAME"
    )
    logger.info("或在代码中调用: from indicators.atr.atr import calculate_atr")
