"""订单执行模块

专门负责订单执行和结果处理的完整业务逻辑.
"""

from collections.abc import Sequence
from decimal import Decimal

from database.crud import update_trading_log
from database.order_models import BinanceOpenOrder
from order_builder.order.cancellation import execute_batch_cancel
from order_builder.order.retry import place_order_with_retry


def execute_order(
    symbol: str,
    side: str,
    qty: Decimal,
    entry_price: Decimal,
    timeframe: str,
    log_id: int,
    open_orders: Sequence[BinanceOpenOrder],
) -> str:
    """执行订单并处理结果

    Args:
        symbol: 交易对符号
        side: 买卖方向
        qty: 订单数量
        entry_price: 入场价格
        timeframe: 时间框架
        log_id: 交易日志 ID
        open_orders: 开仓订单列表

    Returns:
        str: 订单 ID

    Raises:
        ValueError: 如果下单失败
    """
    # 转换为可变列表,以支持下游函数的清空操作
    mutable_orders: list[BinanceOpenOrder] = list(open_orders)

    order_id = place_order_with_retry(
        symbol=symbol,
        side=side,
        qty=str(qty),
        stop_price=str(entry_price),
        timeframe=timeframe,
        open_orders=mutable_orders,
    )

    if mutable_orders:
        _ = execute_batch_cancel(symbol, mutable_orders)
    update_trading_log(log_id=log_id, order_id=order_id)
    return order_id
