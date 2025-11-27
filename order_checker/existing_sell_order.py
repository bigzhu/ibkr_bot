"""SELL order price guard

If there are existing SELL open orders for the same symbol/timeframe, do not
place a new SELL with a lower price. This avoids undercutting our own orders.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from loguru import logger

from database.order_models import BinanceOpenOrder
from shared.constants import SELL

__all__ = ["check_sell_price_not_lower_than_open"]


def check_sell_price_not_lower_than_open(
    new_price: Decimal, open_orders: Sequence[BinanceOpenOrder]
) -> None:
    """Ensure new SELL price is not lower than existing SELL open orders.

    Args:
        new_price: price planned for the new SELL order
        open_orders: pre-fetched open orders to check against (guaranteed non-empty)

    Raises:
        ValueError: when `new_price` <= max(existing SELL open-order price)
    """
    sell_prices: list[Decimal] = []
    for order in open_orders:
        if order.side == SELL:
            price = Decimal(str(order.price))
            if price > 0:
                sell_prices.append(price)

    if not sell_prices:
        return

    max_sell_price = max(sell_prices)
    if new_price <= max_sell_price:
        # 按现有规范, 抛异常由上层记录为业务中断
        msg = f"{new_price} <= pending order {max_sell_price}"
        logger.info(f"业务中断: {msg}")
        raise ValueError(msg)
