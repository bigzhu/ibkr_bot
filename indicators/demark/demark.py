"""DeMark指标模块

提供DeMark指标的纯技术计算功能,完全独立于外部依赖.
遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except,彻底重构原则
"""

from typing import NamedTuple

import numpy as np
import pandas as pd

if __name__ == "__main__":
    try:
        from shared.path_utils import ensure_project_root_for_script
    except ImportError:
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from shared.path_utils import ensure_project_root_for_script

    ensure_project_root_for_script(__file__)

from shared.constants import BUY, SELL
from shared.types import Kline


class HLCSeries(NamedTuple):
    close: pd.Series
    high: pd.Series
    low: pd.Series


def demark(klines_data: list[Kline]) -> tuple[str, int, bool, list[Kline]]:
    """从K线数据计算DeMark信号 - 纯技术实现"""
    _validate_klines(klines_data)
    hlc_series = _extract_hlc_series(klines_data)
    td_up, td_down = _calculate_demark_signals(hlc_series)
    reverse_break_up, reverse_break_down = _calculate_reverse_break_flags(hlc_series)
    sequence_klines = _select_sequence_klines(klines_data, td_up, td_down)
    return _build_signal_payload(
        td_up,
        td_down,
        reverse_break_up,
        reverse_break_down,
        sequence_klines,
    )


def _validate_klines(klines_data: list[Kline]) -> None:
    if not klines_data:
        raise ValueError("K线数据不能为空")
    if len(klines_data) < 5:
        raise ValueError(f"K线数据不足,需要至少5根,实际{len(klines_data)}根")


def _extract_hlc_series(dict_klines: list[Kline]) -> HLCSeries:
    if len(dict_klines) < 5:
        raise ValueError(f"K线数据不足,需要至少5根,实际{len(dict_klines)}根")
    close_prices: list[float] = []
    high_prices: list[float] = []
    low_prices: list[float] = []
    for kline in dict_klines:
        close_prices.append(float(kline["close"]))
        high_prices.append(float(kline["high"]))
        low_prices.append(float(kline["low"]))

    close_series = pd.Series(close_prices, name="close")
    high_series = pd.Series(high_prices, name="high", index=close_series.index)
    low_series = pd.Series(low_prices, name="low", index=close_series.index)
    return HLCSeries(close_series, high_series, low_series)


def _calculate_demark_signals(hlc_series: HLCSeries) -> tuple[int | None, int | None]:
    if len(hlc_series.close) < 5:
        return None, None

    td_up_counts, td_down_counts = _compute_td_series(hlc_series)
    last_td_up = _extract_latest_signal(td_up_counts)
    last_td_down = _extract_latest_signal(td_down_counts)
    return last_td_up, last_td_down


def _calculate_reverse_break_flags(hlc_series: HLCSeries) -> tuple[bool, bool]:
    close_series, high_series, low_series = hlc_series
    if len(close_series) < 2:
        return False, False

    latest_close = float(close_series.iloc[-1])
    prev_high = float(high_series.iloc[-2])
    prev_low = float(low_series.iloc[-2])
    reverse_break_up = latest_close < prev_low
    reverse_break_down = latest_close > prev_high
    return reverse_break_up, reverse_break_down


def _compute_td_series(hlc_series: HLCSeries) -> tuple[pd.Series, pd.Series]:
    """计算 TD 序列的上涨与下跌计数."""
    close_series, high_series, low_series = hlc_series
    if len(high_series) != len(close_series) or len(low_series) != len(close_series):
        raise ValueError("高低价序列长度异常")

    high_values: np.ndarray = np.asarray(high_series, dtype=float)
    low_values: np.ndarray = np.asarray(low_series, dtype=float)

    up_conditions_array = np.zeros_like(high_values, dtype=bool)
    down_conditions_array = np.zeros_like(low_values, dtype=bool)
    up_conditions_array[4:] = high_values[4:] >= high_values[:-4]
    down_conditions_array[4:] = low_values[4:] <= low_values[:-4]

    td_up_series = pd.Series(0, index=close_series.index, dtype="int64")
    td_down_series = pd.Series(0, index=close_series.index, dtype="int64")

    td_up_series.iloc[4:] = _vectorized_td_count(up_conditions_array, 4)
    td_down_series.iloc[4:] = _vectorized_td_count(down_conditions_array, 4)

    return td_up_series, td_down_series


def _extract_latest_signal(series: pd.Series) -> int | None:
    """获取最近一个大于零的 TD 信号."""
    latest_value = int(series.iloc[-1])
    return latest_value if latest_value > 0 else None


def _vectorized_td_count(condition_array: np.ndarray, start_index: int) -> np.ndarray:
    target_conditions = condition_array[start_index:].astype(bool, copy=False)
    if target_conditions.size == 0:
        return np.array([], dtype="int64")

    indices = np.arange(target_conditions.size)
    last_reset_index = np.maximum.accumulate(np.where(target_conditions, -1, indices))
    counts = indices - last_reset_index
    counts = np.where(target_conditions, counts, 0)
    return counts.astype("int64")


def _select_sequence_klines(
    klines_data: list[Kline],
    td_up: int | None,
    td_down: int | None,
) -> list[Kline]:
    sequence_length = max(5, td_up or 0, td_down or 0)
    if len(klines_data) >= sequence_length:
        return klines_data[-sequence_length:]
    return klines_data


def _build_signal_payload(
    td_up: int | None,
    td_down: int | None,
    reverse_break_up: bool,
    reverse_break_down: bool,
    sequence_klines: list[Kline],
) -> tuple[str, int, bool, list[Kline]]:
    # 当同时出现 SELL 和 BUY 信号时, 优先返回 SELL
    if td_up and td_up > 0:
        return SELL, td_up, reverse_break_up, sequence_klines
    if td_down and td_down > 0:
        return BUY, td_down, reverse_break_down, sequence_klines
    return "NONE", 0, False, sequence_klines


# if __name__ == "__main__":
#     """测试DeMark模块(纯技术演示)"""
#     logger.info("DeMark指标模块 - 技术计算入口")
#     logger.info("使用带API的数据获取请运行: uv run python -m demark SYMBOL TIMEFRAME")
#     logger.info("或在代码中调用: from demark.demark import demark")
