"""订单查询模块

实现订单查询相关功能.
"""

from database.order_models import BinanceOpenOrder
from ibkr_api.get_open_orders import get_open_orders
from shared.timeframe_utils import is_timeframe_match


def get_open_orders_by_symbol_timeframe(
    symbol: str, timeframe: str
) -> list[BinanceOpenOrder]:
    """获取指定交易对和时间周期的未成交挂单

    Args:
        symbol: 交易对符号
        timeframe: 时间周期

    Returns:
        list[BinanceOpenOrder]: 符合条件的未成交挂单列表
    """
    open_orders = get_open_orders(symbol)
    filtered_orders = [
        order
        for order in open_orders
        if is_timeframe_match(order.client_order_id, timeframe)
    ]
    return filtered_orders
