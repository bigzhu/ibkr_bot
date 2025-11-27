"""止损市价单模块

专注于下止损市价单的功能.
"""

from loguru import logger

from database.order_models import BinanceOpenOrder
from ibkr_api.common import get_configured_client
from ibkr_api.place_order import place_order, place_order_test
from shared.constants import ORDER_TYPE_STOP_LOSS
from shared.timeframe_utils import timeframe_candidates


def check_client_order_id_exists(
    client_order_id: str, open_orders: list[BinanceOpenOrder]
) -> bool:
    """检查客户端订单ID是否已存在

    Args:
        client_order_id: 客户端订单ID
        open_orders: 现有的挂单列表

    Returns:
        bool: True表示已存在, False表示不存在
    """
    logger.debug(f"🔍 检查客户端订单ID: {client_order_id}")

    for order in open_orders:
        if order.client_order_id == client_order_id:
            logger.debug(f"✅ 找到重复的客户端订单ID: {client_order_id}")
            return True

    logger.debug(f"❌ 客户端订单ID不存在: {client_order_id}")
    return False


def generate_unique_client_order_id(
    base_timeframe: str, open_orders: list[BinanceOpenOrder]
) -> str:
    """生成唯一的客户端订单ID

    Args:
        base_timeframe: 基础时间周期
        open_orders: 现有的挂单列表

    Returns:
        str: 唯一的客户端订单ID
    """
    base, alt = timeframe_candidates(base_timeframe)

    if not check_client_order_id_exists(base, open_orders):
        logger.debug(f"✅ 使用基础时间周期: {base}")
        return base

    logger.info(f"🔄 使用替代客户端订单ID: {alt}")
    return alt


def place_stop_market_order(
    symbol: str,
    side: str,
    quantity: str,
    stop_price: str,
    timeframe: str,
    open_orders: list[BinanceOpenOrder],
) -> str:
    """下止损市价单 - 专用于 DeMark 信号交易

    固定参数配置:
    - 订单类型: STOP_LOSS (止损市价单)
    - 使用 quantity 而非 quoteOrderQty
    - 使用 timeframe 作为客户端订单ID
    - 自动获取 Binance 客户端

    Args:
        symbol: 交易对
        side: 订单方向 ("BUY" 或 "SELL")
        quantity: 数量 (字符串格式, 已处理精度)
        stop_price: 触发价格 (字符串格式)
        timeframe: 时间周期 (用作客户端订单ID, 如 "15m", "1h")

    Returns:
        str: 订单 ID
    """
    logger.info(
        f"🎯 止损市价单: {symbol} {side} 数量:{quantity} 触发价:{stop_price} 时间周期:{timeframe}"
    )

    client = get_configured_client()
    unique_client_order_id = generate_unique_client_order_id(timeframe, open_orders)

    return place_order(
        client=client,
        symbol=symbol,
        side=side,
        order_type=ORDER_TYPE_STOP_LOSS,
        quantity=quantity,
        stop_price=stop_price,
        client_order_id=unique_client_order_id,
    )


def test_stop_market_order(
    symbol: str,
    side: str,
    quantity: str,
    stop_price: str,
    timeframe: str,
) -> str:
    """测试止损市价单 - 不会实际成交

    Args:
        symbol: 交易对
        side: 订单方向
        quantity: 数量
        stop_price: 触发价格
        timeframe: 时间周期 (用作客户端订单ID)

    Returns:
        str: 测试订单响应
    """
    logger.info(
        f"🧪 测试止损市价单: {symbol} {side} 数量:{quantity} 触发价:{stop_price} 时间周期:{timeframe}"
    )

    client = get_configured_client()
    # 测试模式下传入空列表即可
    unique_client_order_id = generate_unique_client_order_id(timeframe, [])

    return place_order_test(
        client=client,
        symbol=symbol,
        side=side,
        order_type="STOP_LOSS",
        quantity=quantity,
        stop_price=stop_price,
        client_order_id=unique_client_order_id,
    )
