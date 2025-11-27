"""DeMark指标模块 - 传统方式实现

基于收盘价严格比较的传统 TD Sequential 实现.
符合行业标准,避免高低影线噪声,信号更稳定.

提供DeMark指标的纯技术计算功能,完全独立于外部依赖.
遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except
"""

from decimal import Decimal

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


def demark(klines_data: list[Kline]) -> tuple[str, int, bool, list[Kline]]:
    """从K线数据计算DeMark信号 - 传统方式实现

    基于收盘价严格比较: close[n] > close[n-4] 或 close[n] < close[n-4]
    符合行业标准,避免高低影线噪声,信号更稳定
    """
    _validate_klines(klines_data)
    close_prices = _extract_close_prices(klines_data)
    td_up, td_down = _calculate_demark_signals(close_prices)
    reverse_break_up, reverse_break_down = _calculate_reverse_break_flags(klines_data)
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


def _extract_close_prices(dict_klines: list[Kline]) -> pd.Series:
    if len(dict_klines) < 5:
        raise ValueError(f"K线数据不足,需要至少5根,实际{len(dict_klines)}根")
    close_prices: list[float] = []
    for kline in dict_klines:
        close_prices.append(float(kline["close"]))
    return pd.Series(close_prices, name="close")


def _calculate_demark_signals(close_prices: pd.Series) -> tuple[int | None, int | None]:
    if len(close_prices) < 5:
        return None, None

    td_up_counts, td_down_counts = _compute_td_series(close_prices)
    last_td_up = _extract_latest_signal(td_up_counts)
    last_td_down = _extract_latest_signal(td_down_counts)
    return last_td_up, last_td_down


def _compute_td_series(close_prices: pd.Series) -> tuple[pd.Series, pd.Series]:
    """计算 TD 序列的上涨与下跌计数 - 基于收盘价严格比较"""
    td_up_series = pd.Series(0, index=close_prices.index, dtype="int64")
    td_down_series = pd.Series(0, index=close_prices.index, dtype="int64")

    for index in range(4, len(close_prices)):
        previous_index = index - 4
        current_close = Decimal(str(close_prices.iloc[index]))
        previous_close = Decimal(str(close_prices.iloc[previous_index]))

        td_up_series.iloc[index] = _update_td_count(
            current_close > previous_close,
            td_up_series.iloc[index - 1],
        )
        td_down_series.iloc[index] = _update_td_count(
            current_close < previous_close,
            td_down_series.iloc[index - 1],
        )

    return td_up_series, td_down_series


def _extract_latest_signal(series: pd.Series) -> int | None:
    """获取最近一个大于零的 TD 信号."""
    latest_value = int(series.iloc[-1])
    return latest_value if latest_value > 0 else None


def _update_td_count(condition: bool, previous_count: int) -> int:
    if condition:
        return previous_count + 1 if previous_count > 0 else 1
    return 0


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


def _calculate_reverse_break_flags(klines_data: list[Kline]) -> tuple[bool, bool]:
    if len(klines_data) < 2:
        return False, False

    latest_close = float(klines_data[-1]["close"])
    previous_high = float(klines_data[-2]["high"])
    previous_low = float(klines_data[-2]["low"])
    reverse_break_up = latest_close < previous_low
    reverse_break_down = latest_close > previous_high
    return reverse_break_up, reverse_break_down


if __name__ == "__main__":
    """测试DeMark模块 - 传统方式"""
    from loguru import logger

    logger.info("DeMark指标模块 - 传统方式实现")
    logger.info(
        "使用带API的数据获取请运行: from demark.binance_demark import demark_with_binance_api"
    )
    logger.info("或在代码中调用: from demark.demark_traditional import demark")
