"""订单检查通用函数模块

提供各种订单检查器的通用功能和数据获取方法.
遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except
"""

import sys
from decimal import Decimal
from typing import Any

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m order_checker.common` 运行该模块, 无需手动修改 sys.path"
    )

from loguru import logger

from database.crud import get_symbol_info
from database.db_config import get_db_manager
from database.models import BinanceFilledOrder
from ibkr_api.common import get_configured_client, get_current_price
from ibkr_api.get_balance import get_balance
from shared.timeframe_utils import timeframe_candidates

__all__ = [
    "calculate_unmatched_buy_total_value",
    "get_current_market_price",
    "get_quote_asset_balance",
    "get_recent_filled_buy_orders_by_timeframe",
    "get_today_unmatched_buy_orders_by_timeframe",
    "get_today_unmatched_buy_total_value",
    "get_unmatched_buy_orders",
    "get_unmatched_buy_orders_by_timeframe",
    "get_unmatched_value_by_timeframe",
    "raise_risk_limit_error",
]


def get_current_market_price(symbol: str) -> Decimal:
    """获取当前市场价格

    Args:
        symbol: 交易对符号

    Returns:
        当前市场价格

    Raises:
        Exception: API调用失败时抛出异常
    """
    client = get_configured_client()
    return get_current_price(client, symbol)


def get_quote_asset_balance(symbol: str) -> Decimal:
    """获取交易对计价资产的余额

    根据交易对符号获取其计价资产(quote asset)并返回该资产的当前余额

    Args:
        symbol: 交易对符号

    Returns:
        计价资产余额(Decimal类型保持精度)

    Raises:
        ValueError: 交易对配置不存在时抛出
    """
    # 获取交易对信息,确定计价资产
    symbol_info = get_symbol_info(symbol)
    quote_asset = symbol_info.quote_asset

    # 获取计价资产余额
    quote_balance_float = get_balance(quote_asset)
    return Decimal(str(quote_balance_float))


def get_unmatched_buy_orders(symbol: str) -> list[BinanceFilledOrder]:
    """获取所有时间维度的未匹配BUY订单

    Args:
        symbol: 交易对符号

    Returns:
        未匹配BUY订单列表
    """
    db = get_db_manager()
    sql = """
        SELECT * FROM filled_orders
        WHERE pair = ?
        AND side = 'BUY'
        AND unmatched_qty > 0
        AND status = 'FILLED'
        ORDER BY time DESC
    """

    rows = db.execute_query(sql, (symbol,))
    return [BinanceFilledOrder.from_db_dict(dict(row)) for row in rows]


def get_unmatched_buy_orders_by_timeframe(
    symbol: str, timeframe: str
) -> list[BinanceFilledOrder]:
    """获取指定时间维度的未匹配BUY订单"""
    candidates = timeframe_candidates(timeframe)
    rows = get_db_manager().execute_query(
        """
        SELECT * FROM filled_orders
        WHERE pair = ? AND side = 'BUY' AND unmatched_qty > 0 AND status = 'FILLED'
        AND (client_order_id = ? OR client_order_id = ? OR client_order_id IS NULL)
        ORDER BY time DESC
        """,
        (symbol, candidates[0], candidates[1]),
    )
    return [BinanceFilledOrder.from_db_dict(dict(row)) for row in rows]


def get_recent_filled_buy_orders_by_timeframe(
    symbol: str, timeframe: str, limit: int = 50
) -> list[BinanceFilledOrder]:
    """获取指定时间周期内最新的已撮合BUY订单

    Args:
        symbol: 交易对符号
        timeframe: 时间周期(如 '1m', '15m', '1h')
        limit: 返回的最大订单数量, 默认50

    Returns:
        已撮合BUY订单列表, 按成交时间倒序
    """
    if limit <= 0:
        raise ValueError("limit 必须为正整数")

    db = get_db_manager()
    sql = """
        SELECT * FROM filled_orders
        WHERE pair = ?
        AND side = 'BUY'
        AND status = 'FILLED'
        AND matched_time IS NOT NULL
        AND (client_order_id = ? OR client_order_id = ? OR client_order_id IS NULL)
        ORDER BY matched_time DESC
        LIMIT ?
    """

    candidates = timeframe_candidates(timeframe)
    rows = db.execute_query(sql, (symbol, candidates[0], candidates[1], limit))
    return [BinanceFilledOrder.from_db_dict(dict(row)) for row in rows]


def get_today_unmatched_buy_orders_by_timeframe(
    symbol: str, timeframe: str
) -> list[BinanceFilledOrder]:
    """获取今日指定时间周期的未匹配BUY订单

    以美股闭市时间(UTC 20:00)作为天的分界

    Args:
        symbol: 交易对符号
        timeframe: 时间周期(如 '1m', '15m', '1h')

    Returns:
        今日未匹配BUY订单列表
    """
    db = get_db_manager()
    sql = """
        SELECT * FROM filled_orders
        WHERE pair = ?
        AND side = 'BUY'
        AND unmatched_qty > 0
        AND status = 'FILLED'
        AND (client_order_id = ? OR client_order_id = ? OR client_order_id IS NULL)
        AND DATE(time, '-4 hours') = DATE('now', 'utc', '-4 hours')
        ORDER BY time DESC
    """

    candidates = timeframe_candidates(timeframe)
    rows = db.execute_query(sql, (symbol, candidates[0], candidates[1]))
    return [BinanceFilledOrder.from_db_dict(dict(row)) for row in rows]


def get_today_unmatched_buy_total_value(symbol: str, timeframe: str) -> Decimal:
    """获取当日指定时间周期的未撮合BUY订单总金额

    封装函数,避免重复代码.使用美股闭市时间(UTC 20:00)作为天的分界

    Args:
        symbol: 交易对符号
        timeframe: 时间周期(如 '1m', '15m', '1h')

    Returns:
        当日未撮合BUY订单总金额
    """
    today_orders = get_today_unmatched_buy_orders_by_timeframe(symbol, timeframe)
    return calculate_unmatched_buy_total_value(today_orders)


def calculate_unmatched_buy_total_value(
    unmatched_orders: list[BinanceFilledOrder],
) -> Decimal:
    """计算未匹配BUY订单总价值(按原始买入价格)

    Args:
        unmatched_orders: 未匹配订单列表

    Returns:
        总价值
    """
    return sum(
        (
            Decimal(order.unmatched_qty) * Decimal(order.average_price)
            for order in unmatched_orders
        ),
        Decimal("0"),
    )


def get_unmatched_value_by_timeframe(symbol: str, timeframe: str) -> Decimal:
    """获取指定时间维度的未匹配订单总价值"""
    return calculate_unmatched_buy_total_value(
        get_unmatched_buy_orders_by_timeframe(symbol, timeframe)
    )


def raise_risk_limit_error(
    check_type: str, current_value: Any, limit_value: Any, limit_desc: str
) -> None:
    """抛出风险限制错误

    Args:
        check_type: 检查类型名称
        current_value: 当前值
        limit_value: 限制值
        limit_desc: 限制描述

    Raises:
        ValueError: 风险限制错误
    """
    error_msg = f"超出{check_type}: {current_value} > {limit_value} ({limit_desc})"
    # 业务性中断, 降为 INFO, 避免控制台噪声
    logger.info(f"业务中断: {error_msg}")
    raise ValueError(error_msg)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        logger.info("Usage: p order_checker/common.py <SYMBOL> <TIMEFRAME>")
        logger.info("Example: p order_checker/common.py ADAUSDC 15m")
        sys.exit(1)

    symbol = sys.argv[1]
    timeframe = sys.argv[2]

    orders = get_unmatched_buy_orders_by_timeframe(symbol, timeframe)
    logger.info(f"找到 {len(orders)} 个未匹配的BUY订单:")
    for order in orders:
        logger.info(
            f"订单号: {order.order_no}, 数量: {order.unmatched_qty}, 价格: {order.average_price}"
        )
