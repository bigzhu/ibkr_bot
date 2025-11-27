"""SuperTrend 指标计算模块."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m indicators.supertrend.supertrend` 运行该模块, 无需手动修改 sys.path"
    )

from loguru import logger

from shared.types import Kline

SuperTrendColor = Literal["GREEN", "RED"]


def calculate_supertrend_signal(
    klines_data: list[Kline],
    period: int = 10,
    multiplier: Decimal | float | int = Decimal("3"),
) -> tuple[SuperTrendColor, Decimal]:
    """根据 K 线数据计算最新的 SuperTrend 信号颜色与数值."""

    if period <= 1:
        raise ValueError("SuperTrend period 必须大于1")
    if len(klines_data) < period + 2:
        raise ValueError(
            f"SuperTrend 计算需要至少 {period + 2} 根 K 线, 当前 {len(klines_data)} 根"
        )

    multiplier_decimal = _ensure_decimal(multiplier)

    highs = [_decimal_price(kline["high"]) for kline in klines_data]
    lows = [_decimal_price(kline["low"]) for kline in klines_data]
    closes = [_decimal_price(kline["close"]) for kline in klines_data]

    atr_series = _compute_atr_series(highs, lows, closes, period)

    supertrend_values: list[Decimal | None] = [None] * len(closes)
    final_upper: list[Decimal | None] = [None] * len(closes)
    final_lower: list[Decimal | None] = [None] * len(closes)

    for idx in range(len(closes)):
        atr_value = atr_series[idx]
        if atr_value is None:
            continue

        hl2 = (highs[idx] + lows[idx]) / Decimal("2")
        basic_upper = hl2 + multiplier_decimal * atr_value
        basic_lower = hl2 - multiplier_decimal * atr_value

        if idx == 0 or final_upper[idx - 1] is None:
            final_upper[idx] = basic_upper
            final_lower[idx] = basic_lower
            supertrend_values[idx] = (
                basic_lower if closes[idx] >= basic_lower else basic_upper
            )
            continue

        prev_final_upper = final_upper[idx - 1]
        prev_final_lower = final_lower[idx - 1]
        prev_close = closes[idx - 1]
        prev_supertrend = supertrend_values[idx - 1]

        if prev_final_upper is None or prev_final_lower is None:
            raise ValueError(
                f"前一个周期的band值不应为None: upper={prev_final_upper}, lower={prev_final_lower}"
            )

        upper_band = (
            basic_upper
            if basic_upper < prev_final_upper or prev_close > prev_final_upper
            else prev_final_upper
        )
        lower_band = (
            basic_lower
            if basic_lower > prev_final_lower or prev_close < prev_final_lower
            else prev_final_lower
        )

        if prev_supertrend is None:
            raise ValueError("前一个周期的supertrend值不应为None")

        if prev_supertrend == prev_final_upper:
            if closes[idx] <= upper_band:
                supertrend_values[idx] = upper_band
            else:
                supertrend_values[idx] = lower_band
        elif prev_supertrend == prev_final_lower:
            if closes[idx] >= lower_band:
                supertrend_values[idx] = lower_band
            else:
                supertrend_values[idx] = upper_band
        else:
            supertrend_values[idx] = (
                lower_band if closes[idx] >= lower_band else upper_band
            )

        final_upper[idx] = upper_band
        final_lower[idx] = lower_band

    last_index = _last_valid_index(supertrend_values)
    if last_index is None:
        raise ValueError("SuperTrend 计算未生成有效结果")

    trend_value = supertrend_values[last_index]
    if trend_value is None:
        raise ValueError("SuperTrend 最新值缺失")

    lower_at_last = final_lower[last_index]
    color: SuperTrendColor = (
        "GREEN" if lower_at_last is not None and trend_value == lower_at_last else "RED"
    )

    logger.debug(
        "SuperTrend(%s, period=%s, multiplier=%s) -> %s %.6f",
        last_index,
        period,
        multiplier_decimal,
        color,
        float(trend_value),
    )

    return color, trend_value


def _compute_atr_series(
    highs: list[Decimal],
    lows: list[Decimal],
    closes: list[Decimal],
    period: int,
) -> list[Decimal | None]:
    trs: list[Decimal] = [Decimal("0")]
    for i in range(1, len(highs)):
        high = highs[i]
        low = lows[i]
        prev_close = closes[i - 1]
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        trs.append(max(tr1, tr2, tr3))

    atr_values: list[Decimal | None] = [None] * len(trs)
    initial_slice = trs[1 : period + 1]
    if len(initial_slice) < period:
        raise ValueError("TR 数据不足以计算初始 ATR")

    initial_atr = sum(initial_slice) / Decimal(str(period))
    atr_values[period] = initial_atr

    for i in range(period + 1, len(trs)):
        prev_atr = atr_values[i - 1]
        if prev_atr is None:
            raise ValueError("ATR 序列缺少连续值")
        atr_values[i] = ((prev_atr * (period - 1)) + trs[i]) / Decimal(str(period))

    return atr_values


def _decimal_price(value: str) -> Decimal:
    return Decimal(str(value))


def _ensure_decimal(value: Decimal | float | int) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _last_valid_index(values: list[Decimal | None]) -> int | None:
    for idx in range(len(values) - 1, -1, -1):
        if values[idx] is not None:
            return idx
    return None


if __name__ == "__main__":
    logger.info("SuperTrend 指标模块 - 仅提供技术计算函数")
