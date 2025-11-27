"""参考价格获取模块

从未匹配订单或K线数据获取参考价格的基准价格:
- BUY单: 获取average_price最低的作为参考价格(持仓最低成本)
- SELL单: 获取average_price最高的作为参考价格(持仓最高成本,最坏情况)
- 无未匹配订单时: 从K线数据获取,BUY取DeMark 1高价,SELL取DeMark 1低价

核心策略:
- BUY 侧以最低成本计算, 确保不会买在更高位
- SELL 侧以最高成本计算, 保守估计收益率(最坏情况)
- 分离来自 K 线与历史订单的数据源, 确保数据一致性

遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except,无副作用
"""

from decimal import Decimal

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m order_builder.reference_price_manager` 运行该模块, 无需手动修改 sys.path"
    )

from loguru import logger

from shared.constants import SELL, FromPriceSource
from shared.number_format import format_decimal
from shared.types import Kline
from shared.types.order_builder import UnmatchedOrders


def _get_from_price_from_klines(side: str, demark_klines: list[Kline]) -> Decimal:
    """从K线数据获取基准价格(内部函数)

    Args:
        side: 信号类型(BUY/SELL)
        demark_klines: DeMark 序列 K 线数据(字典格式), klines[0] = DeMark 1

    Returns:
        Decimal: 基准价格

    Raises:
        Exception: 获取失败时抛出异常
    """
    # 使用传入的 DeMark K 线数据获取 DeMark 1 的价格
    demark_1_kline = demark_klines[0]  # DeMark 1

    if side == SELL:
        from_price = Decimal(str(demark_1_kline["low"]))
        logger.debug(f"SELL from_price = {from_price}")
    else:  # BUY
        from_price = Decimal(str(demark_1_kline["high"]))
        logger.debug(f"BUY from_price = {from_price}")

    return from_price


def _get_lowest_unmatched_price(
    unmatched_orders: UnmatchedOrders,
) -> Decimal | None:
    """从已有的未匹配订单列表获取最低价格

    用于 BUY 侧: 以最低成本计算, 确保不会买在更高位

    Args:
        unmatched_orders: 未匹配订单序列

    Returns:
        Decimal | None: 最低价格,无未匹配订单时返回None
    """
    if not unmatched_orders:
        return None

    lowest_price: Decimal | None = None
    for order in unmatched_orders:
        price = Decimal(order.average_price)
        if lowest_price is None or price < lowest_price:
            lowest_price = price

    return lowest_price


def _get_highest_unmatched_price(
    unmatched_orders: UnmatchedOrders,
) -> Decimal | None:
    """从已有的未匹配订单列表获取最高价格

    用于 SELL 侧: 以最高成本计算, 保守估计收益率(最坏情况)

    Args:
        unmatched_orders: 未匹配订单序列

    Returns:
        Decimal | None: 最高价格,无未匹配订单时返回None
    """
    if not unmatched_orders:
        return None

    highest_price: Decimal | None = None
    for order in unmatched_orders:
        price = Decimal(order.average_price)
        if highest_price is None or price > highest_price:
            highest_price = price

    return highest_price


def get_locked_balance(pair: str, timeframe: str) -> Decimal:
    """查询被套住的余额(未撮合BUY单的总价值)

    统计指定交易对和时间周期中未撮合的BUY单持仓,计算其总价值.
    仅统计该时间周期对应的订单(client_order_id为timeframe或timeframe_1).

    Args:
        pair: 交易对符号(如'ADAUSDC')
        timeframe: 时间周期(如'15m'),用于匹配client_order_id

    Returns:
        Decimal: 被套住的余额,单位为报价资产(如USDC),无被套资产时返回0

    Example:
        >>> locked = get_locked_balance('ADAUSDC', '15m')
        >>> print(f"被套余额: {locked}")
    """
    from database.db_config import get_db_manager
    from shared.timeframe_utils import timeframe_candidates

    db = get_db_manager()
    candidates = timeframe_candidates(timeframe)

    sql = """
        SELECT SUM(unmatched_qty * average_price) AS total_value
        FROM filled_orders
        WHERE pair = ?
        AND side = 'BUY'
        AND unmatched_qty > 0
        AND status = 'FILLED'
        AND client_order_id IN (?, ?)
    """

    result = db.execute_query(sql, (pair, candidates[0], candidates[1]))
    if result and result[0][0] is not None:
        return Decimal(str(result[0][0]))
    return Decimal("0")


def get_optimized_from_price(
    symbol: str,
    side: str,
    demark_klines: list[Kline],
    order_price: Decimal,
    unmatched_orders: UnmatchedOrders,
) -> tuple[Decimal, FromPriceSource]:
    """获取优化的基准价格

    优先从未匹配订单获取,无数据时回退到K线数据获取

    Args:
        symbol: 交易对符号
        side: 订单方向(BUY/SELL)
        demark_klines: DeMark K线数据,用作回退方案
        order_price: 新订单价格,用于BUY侧校验
        unmatched_orders: 已获取的未匹配订单列表

    Returns:
        tuple[Decimal, FromPriceSource]: (基准价格, 数据源)
            - BUY 侧返回最低价(成本最低)
            - SELL 侧返回最高价(最坏情况)
            - 数据源为 FromPriceSource.UNMATCHED_ORDERS 表示来自未匹配订单
            - 数据源为 FromPriceSource.KLINES 表示来自K线数据

    Raises:
        ValueError: BUY侧未卖完时抛出异常
    """
    klines_price = _get_from_price_from_klines(side, demark_klines)

    # BUY 侧: 使用最低价(成本最低)
    if side != SELL:
        unmatched_price = _get_lowest_unmatched_price(unmatched_orders)
        if unmatched_price is None:
            return (klines_price, FromPriceSource.KLINES)

        logger.info(
            f"📊 {symbol} BUY 从未匹配订单获取from_price(最低): {format_decimal(unmatched_price)}"
        )
        return (unmatched_price, FromPriceSource.UNMATCHED_ORDERS)

    # SELL 侧: 使用最高价(最坏情况,保守估计收益)
    unmatched_price = _get_highest_unmatched_price(unmatched_orders)
    if unmatched_price is None:
        return (klines_price, FromPriceSource.KLINES)

    logger.info(
        f"📊 {symbol} SELL 从未匹配订单获取from_price(最高): {format_decimal(unmatched_price)}"
    )
    return (unmatched_price, FromPriceSource.UNMATCHED_ORDERS)


if __name__ == "__main__":
    """参考价格获取模块 - 无测试入口"""
    logger.info("参考价格获取模块")
    logger.info("用途: 从未匹配订单或K线数据获取基准价格")
    logger.info("接口: get_optimized_from_price()")
    logger.info("  - 需传入已获取的unmatched_orders,避免重复查库")
    logger.info("  - 优先从未匹配订单获取,无数据时回退到K线数据获取")
