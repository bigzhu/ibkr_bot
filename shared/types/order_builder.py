from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, TypedDict

from database.models import BinanceFilledOrder


class NoSignalResult(TypedDict):
    action: Literal["NO_SIGNAL"]
    symbol: str
    timeframe: str
    signal_value: int


class KlineAlreadyProcessedResult(TypedDict):
    action: Literal["KLINE_ALREADY_PROCESSED"]
    symbol: str
    timeframe: str
    signal_value: int
    reason: str


class OrderPlacedResult(TypedDict):
    action: Literal["ORDER_PLACED"]
    symbol: str
    timeframe: str
    signal_value: int
    qty: float
    price: float
    order_id: str


class ErrorResult(TypedDict):
    action: Literal["ERROR"]
    symbol: str
    timeframe: str
    signal_value: int
    error: str


RunResult = (
    NoSignalResult | KlineAlreadyProcessedResult | OrderPlacedResult | ErrorResult
)

UnmatchedOrders = Sequence[BinanceFilledOrder]
