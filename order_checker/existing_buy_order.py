"""BUY order price guard

If there are existing BUY open orders for the same symbol/timeframe, do not
place a new BUY with a higher price. This avoids overpaying compared to pending orders.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from loguru import logger

from database.order_models import BinanceOpenOrder
from shared.constants import BUY

__all__ = ["check_buy_price_not_higher_than_open"]


def check_buy_price_not_higher_than_open(
    new_price: Decimal, open_orders: Sequence[BinanceOpenOrder]
) -> None:
    """Ensure new BUY price is not higher than existing BUY open orders.

    Args:
        new_price: price planned for the new BUY order
        open_orders: pre-fetched open orders to check against (guaranteed non-empty)

    Raises:
        ValueError: when `new_price` >= min(existing BUY open-order price)
    """
    buy_prices: list[Decimal] = []
    for order in open_orders:
        if order.side == BUY:
            price = Decimal(str(order.price))
            if price > 0:
                buy_prices.append(price)

    if not buy_prices:
        return

    min_buy_price = min(buy_prices)
    if new_price >= min_buy_price:
        # 按现有规范, 抛异常由上层记录为业务中断
        msg = f"{new_price} >= pending order {min_buy_price}"
        logger.info(f"业务中断: {msg}")
        raise ValueError(msg)
