"""Unmatched order helpers."""

from decimal import Decimal

from shared.types.order_builder import UnmatchedOrders


def count_effective_unmatched_orders(
    unmatched_orders: UnmatchedOrders, min_notional: Decimal
) -> int:
    """Count unmatched orders whose notional meets or exceeds the minimum requirement."""
    count = 0
    for order in unmatched_orders:
        qty_raw = getattr(order, "unmatched_qty", "0")
        price_raw = getattr(order, "average_price", "0")
        qty = Decimal(str(qty_raw))
        price = Decimal(str(price_raw))
        if qty <= 0 or price <= 0:
            continue
        if qty * price >= min_notional:
            count += 1
    return count
