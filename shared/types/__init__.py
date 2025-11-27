"""
Shared type definitions package.

Provide precise types for common data structures to avoid using Any.
"""

from typing import Protocol, TypedDict, runtime_checkable


class Kline(TypedDict):
    """Standardized Binance kline item in dict form."""

    open_time: int
    open: str
    high: str
    low: str
    close: str
    volume: str
    close_time: int
    quote_asset_volume: str
    number_of_trades: int
    taker_buy_base_asset_volume: str
    taker_buy_quote_asset_volume: str


@runtime_checkable
class BinanceKlinesClient(Protocol):
    """Minimal protocol of a client that can fetch klines."""

    def get_klines(
        self,
        *,
        symbol: str,
        interval: str,
        limit: int,
    ) -> list[list[object]]: ...


__all__ = [
    "BinanceKlinesClient",
    "Kline",
]
