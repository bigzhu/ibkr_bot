from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from indicators.supertrend.supertrend import calculate_supertrend_signal


def _make_kline(
    open_time: int,
    open_price: float,
    high: float,
    low: float,
    close: float,
) -> dict[str, object]:
    return {
        "open_time": open_time,
        "open": f"{open_price:.4f}",
        "high": f"{high:.4f}",
        "low": f"{low:.4f}",
        "close": f"{close:.4f}",
        "volume": "0",
        "close_time": open_time + 60_000,
        "quote_asset_volume": "0",
        "number_of_trades": 0,
        "taker_buy_base_asset_volume": "0",
        "taker_buy_quote_asset_volume": "0",
    }


def _build_klines(prices: list[float]) -> list[dict[str, object]]:
    klines: list[dict[str, object]] = []
    for idx, price in enumerate(prices):
        high = price + 0.5
        low = price - 0.5
        open_price = price - 0.2
        klines.append(_make_kline(idx * 60_000, open_price, high, low, price))
    return klines


def test_supertrend_signal_green_on_uptrend() -> None:
    klines = _build_klines([float(x) for x in range(1, 30)])
    color, value = calculate_supertrend_signal(
        klines, period=7, multiplier=Decimal("2")
    )

    assert color == "GREEN"
    assert isinstance(value, Decimal)


def test_supertrend_signal_red_on_downtrend() -> None:
    klines = _build_klines([float(x) for x in range(100, 70, -1)])
    color, _ = calculate_supertrend_signal(klines, period=7, multiplier=Decimal("2"))

    assert color == "RED"


def test_supertrend_signal_requires_enough_data() -> None:
    klines = _build_klines([1.0, 1.1, 1.2])
    with pytest.raises(ValueError):
        calculate_supertrend_signal(klines, period=7)
