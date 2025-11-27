"""Shared timeframe constants and SQL helpers."""

from __future__ import annotations

# Full set used across UI filters and validation
SUPPORTED_TIMEFRAMES: list[str] = [
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "4h",
    "1d",
    "1W",
    "1M",
]

# Default configs created for new symbols
DEFAULT_CONFIG_TIMEFRAMES: list[str] = ["1m", "3m", "5m", "15m", "30m", "1h", "4h"]


def timeframe_order_case(column: str) -> str:
    """Return a SQL CASE expression that orders timeframes in a logical order.

    Example usage:
        ORDER BY {timeframe_order_case('kline_timeframe')}
    """

    order = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h"]
    whens = "\n               ".join(
        [f"WHEN '{tf}' THEN {i + 1}" for i, tf in enumerate(order)]
    )
    return f"CASE {column}\n               {whens}\n               ELSE 99 END"
