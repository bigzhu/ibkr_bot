"""TD IVEN 指标计算函数

提供与 indicators.demark 类似的接口, 仅返回 side/setup/countdown 三个维度.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from shared.constants import BUY, SELL
from shared.types import Kline

MIN_REQUIRED_KLINES = 34


def td_iven(klines_data: Sequence[Kline]) -> tuple[str, int, int]:
    """根据 K 线计算 TD IVEN 信号.

    返回 (side, setup, countdown):
    - side: BUY/SELL/NONE
    - setup: 对应 side 的 setup 计数 (1-9)
    - countdown: 对应 side 的标准 countdown 计数, 允许超过 13
    """

    if len(klines_data) < MIN_REQUIRED_KLINES:
        raise ValueError(
            f"TD IVEN 计算需要至少{MIN_REQUIRED_KLINES}根K线, 实际{len(klines_data)}根"
        )

    highs, lows, closes = _extract_hlc_series(klines_data)
    series = _build_td_series(highs, lows, closes)
    last_index = len(closes) - 1

    buy_setup = series.buy_setup[last_index]
    sell_setup = series.sell_setup[last_index]
    buy_countdown = _normalize_countdown(series.buy_countdown[last_index])
    sell_countdown = _normalize_countdown(series.sell_countdown[last_index])

    side, setup, countdown = _select_signal(
        buy_setup, sell_setup, buy_countdown, sell_countdown
    )
    return side, setup, countdown


def _select_signal(
    buy_setup: int,
    sell_setup: int,
    buy_countdown: int,
    sell_countdown: int,
) -> tuple[str, int, int]:
    """选择当前最有意义的 side/setup/countdown."""
    if sell_countdown > buy_countdown and sell_countdown > 0:
        return SELL, sell_setup, sell_countdown
    if buy_countdown > sell_countdown and buy_countdown > 0:
        return BUY, buy_setup, buy_countdown

    if sell_setup >= buy_setup and sell_setup > 0:
        return SELL, sell_setup, sell_countdown
    if buy_setup > 0:
        return BUY, buy_setup, buy_countdown

    return "NONE", 0, 0


def _normalize_countdown(value: int) -> int:
    """标准 countdown 只关心正向进度."""
    return value if value > 0 else 0


@dataclass
class _TDSeries:
    buy_setup: list[int]
    sell_setup: list[int]
    buy_setup_stage: list[int]
    sell_setup_stage: list[int]
    buy_countdown: list[int]
    sell_countdown: list[int]


def _build_td_series(
    highs: list[Decimal],
    lows: list[Decimal],
    closes: list[Decimal],
) -> _TDSeries:
    length = len(closes)
    buy_setup = [0] * length
    sell_setup = [0] * length
    buy_setup_stage = [0] * length
    sell_setup_stage = [0] * length
    buy_countdown = [0] * length
    sell_countdown = [0] * length

    high_trend_lines = [Decimal("0")] * length
    low_trend_lines = [Decimal("0")] * length
    buy_c8_close = [Decimal("0")] * length
    sell_c8_close = [Decimal("0")] * length

    buy_cycle_active = False
    sell_cycle_active = False

    for idx in range(length):
        close = closes[idx]
        low = lows[idx]
        high = highs[idx]

        prev_buy_total = buy_setup[idx - 1] if idx > 0 else 0
        prev_sell_total = sell_setup[idx - 1] if idx > 0 else 0
        prev_buy_stage = buy_setup_stage[idx - 1] if idx > 0 else 0
        prev_sell_stage = sell_setup_stage[idx - 1] if idx > 0 else 0

        if idx >= 4 and close < closes[idx - 4]:
            buy_setup_stage[idx] = 1 if prev_buy_stage == 9 else prev_buy_stage + 1
        else:
            buy_setup_stage[idx] = 0

        if idx >= 4 and close > closes[idx - 4]:
            sell_setup_stage[idx] = 1 if prev_sell_stage == 9 else prev_sell_stage + 1
        else:
            sell_setup_stage[idx] = 0

        highest9 = _window_highest(highs, idx, 9)
        lowest9 = _window_lowest(lows, idx, 9)
        prev_high_trend = high_trend_lines[idx - 1] if idx > 0 else Decimal("0")
        prev_low_trend = low_trend_lines[idx - 1] if idx > 0 else Decimal("0")

        if buy_setup_stage[idx] == 9:
            high_trend_lines[idx] = highest9
        elif close > prev_high_trend:
            high_trend_lines[idx] = Decimal("0")
        else:
            high_trend_lines[idx] = prev_high_trend

        if sell_setup_stage[idx] == 9:
            low_trend_lines[idx] = lowest9
        elif close < prev_low_trend:
            low_trend_lines[idx] = Decimal("0")
        else:
            low_trend_lines[idx] = prev_low_trend

        buy_trend_invalidated = (
            buy_cycle_active
            and prev_high_trend > Decimal("0")
            and high_trend_lines[idx] == Decimal("0")
        )
        sell_trend_invalidated = (
            sell_cycle_active
            and prev_low_trend > Decimal("0")
            and low_trend_lines[idx] == Decimal("0")
        )

        prev_buy_count = buy_countdown[idx - 1] if idx > 0 else 0
        prev_sell_count = sell_countdown[idx - 1] if idx > 0 else 0
        prev_buy_c8_close = buy_c8_close[idx - 1] if idx > 0 else Decimal("0")
        prev_sell_c8_close = sell_c8_close[idx - 1] if idx > 0 else Decimal("0")

        is_buy_condition = idx >= 2 and close < lows[idx - 2]
        is_sell_condition = idx >= 2 and close > highs[idx - 2]

        nonq_buy_candidate = (
            is_buy_condition and abs(prev_buy_count) == 12 and low > prev_buy_c8_close
        )
        nonq_sell_candidate = (
            is_sell_condition
            and abs(prev_sell_count) == 12
            and high < prev_sell_c8_close
        )

        buy_countdown[idx] = _resolve_standard_countdown(
            current_setup=buy_setup_stage[idx],
            opposite_setup=sell_setup_stage[idx],
            trend_line=high_trend_lines[idx],
            is_condition=is_buy_condition,
            previous_value=prev_buy_count,
            nonq_candidate=nonq_buy_candidate,
        )

        sell_countdown[idx] = _resolve_standard_countdown(
            current_setup=sell_setup_stage[idx],
            opposite_setup=buy_setup_stage[idx],
            trend_line=low_trend_lines[idx],
            is_condition=is_sell_condition,
            previous_value=prev_sell_count,
            nonq_candidate=nonq_sell_candidate,
        )

        buy_c8_close[idx] = close if buy_countdown[idx] == 8 else prev_buy_c8_close
        sell_c8_close[idx] = close if sell_countdown[idx] == 8 else prev_sell_c8_close

        buy_cycle_state = buy_cycle_active
        if sell_setup_stage[idx] == 9 or buy_trend_invalidated:
            buy_cycle_state = False
        if buy_setup_stage[idx] == 9:
            buy_cycle_state = True
        if buy_setup_stage[idx] > 0 or buy_cycle_state:
            buy_setup[idx] = prev_buy_total + 1
        else:
            buy_setup[idx] = 0
        buy_cycle_active = buy_cycle_state

        sell_cycle_state = sell_cycle_active
        if buy_setup_stage[idx] == 9 or sell_trend_invalidated:
            sell_cycle_state = False
        if sell_setup_stage[idx] == 9:
            sell_cycle_state = True
        if sell_setup_stage[idx] > 0 or sell_cycle_state:
            sell_setup[idx] = prev_sell_total + 1
        else:
            sell_setup[idx] = 0
        sell_cycle_active = sell_cycle_state

    return _TDSeries(
        buy_setup=buy_setup,
        sell_setup=sell_setup,
        buy_setup_stage=buy_setup_stage,
        sell_setup_stage=sell_setup_stage,
        buy_countdown=buy_countdown,
        sell_countdown=sell_countdown,
    )


def _resolve_standard_countdown(
    current_setup: int,
    opposite_setup: int,
    trend_line: Decimal,
    is_condition: bool,
    previous_value: int,
    nonq_candidate: bool,
) -> int:
    if current_setup == 9:
        return 1 if is_condition else 0
    if opposite_setup == 9 or trend_line == Decimal("0"):
        return 0
    if nonq_candidate:
        return -12
    if is_condition:
        return abs(previous_value) + 1
    return -abs(previous_value)


def _extract_hlc_series(
    klines_data: Sequence[Kline],
) -> tuple[list[Decimal], list[Decimal], list[Decimal]]:
    highs: list[Decimal] = []
    lows: list[Decimal] = []
    closes: list[Decimal] = []
    for item in klines_data:
        highs.append(Decimal(str(item["high"])))
        lows.append(Decimal(str(item["low"])))
        closes.append(Decimal(str(item["close"])))
    return highs, lows, closes


def _window_highest(series: Sequence[Decimal], idx: int, window: int) -> Decimal:
    start = max(0, idx - window + 1)
    value = series[start]
    for pos in range(start + 1, idx + 1):
        if series[pos] > value:
            value = series[pos]
    return value


def _window_lowest(series: Sequence[Decimal], idx: int, window: int) -> Decimal:
    start = max(0, idx - window + 1)
    value = series[start]
    for pos in range(start + 1, idx + 1):
        if series[pos] < value:
            value = series[pos]
    return value


__all__ = ["MIN_REQUIRED_KLINES", "td_iven"]
