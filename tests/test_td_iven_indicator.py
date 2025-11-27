from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from indicators.td_iven import MIN_REQUIRED_KLINES, td_iven
from shared.constants import BUY, SELL


def _build_klines_from_closes(closes: list[float]) -> list[dict[str, object]]:
    klines: list[dict[str, object]] = []
    for idx, close_price in enumerate(closes):
        kline = {
            "open_time": idx * 60_000,
            "open": f"{close_price - 0.2:.4f}",
            "high": f"{close_price + 0.5:.4f}",
            "low": f"{close_price - 0.5:.4f}",
            "close": f"{close_price:.4f}",
            "volume": "0",
            "close_time": idx * 60_000 + 60_000,
            "quote_asset_volume": "0",
            "number_of_trades": 0,
            "taker_buy_base_asset_volume": "0",
            "taker_buy_quote_asset_volume": "0",
        }
        klines.append(kline)
    return klines


def _build_buy_countdown_klines(length: int) -> list[dict[str, object]]:
    closes = [200.0 - idx for idx in range(length)]
    for idx in range(25, length, 5):
        closes[idx] = closes[idx - 4] + 0.1
    return _build_klines_from_closes(closes)


def _build_sell_countdown_klines(length: int) -> list[dict[str, object]]:
    closes = [100.0 + idx for idx in range(length)]
    for idx in range(25, length, 5):
        closes[idx] = closes[idx - 4] - 0.1
    return _build_klines_from_closes(closes)


def test_td_iven_buy_countdown_hits_13() -> None:
    klines = _build_buy_countdown_klines(37)

    side, setup, countdown = td_iven(klines)

    assert side == BUY
    assert setup >= 9
    assert countdown == 13


def test_td_iven_sell_countdown_hits_13() -> None:
    klines = _build_sell_countdown_klines(37)

    side, setup, countdown = td_iven(klines)

    assert side == SELL
    assert setup >= 9
    assert countdown == 13


def test_td_iven_countdown_continues_beyond_13() -> None:
    klines = _build_buy_countdown_klines(50)

    side, setup, countdown = td_iven(klines)

    assert side == BUY
    assert setup >= 9
    assert countdown > 13


def test_td_iven_setup_continues_beyond_9() -> None:
    closes = [200.0 - idx for idx in range(60)]
    klines = _build_klines_from_closes(closes)

    side, setup, _ = td_iven(klines)

    assert side == BUY
    assert setup > 9


def test_td_iven_requires_minimum_klines() -> None:
    closes = [150.0 - idx for idx in range(MIN_REQUIRED_KLINES - 1)]
    klines = _build_klines_from_closes(closes)

    with pytest.raises(ValueError):
        td_iven(klines)


def test_td_iven_returns_none_when_signal_absent() -> None:
    prices = [100.0 for _ in range(MIN_REQUIRED_KLINES)]
    klines = _build_klines_from_closes(prices)

    side, setup, countdown = td_iven(klines)

    assert side == "NONE"
    assert setup == 0
    assert countdown == 0
