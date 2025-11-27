"""
订单更新操作

提供订单字段更新功能
"""

import sqlite3
from datetime import UTC, datetime

from loguru import logger

from database.db_config import get_db_manager
from shared.time_utils import to_utc_str


def update_order_unmatched_qty(
    order_no: str, unmatched_qty: str, *, conn: sqlite3.Connection | None = None
) -> bool:
    """
    更新订单未撮合数量

    Args:
        order_no: 订单号
        unmatched_qty: 新的未撮合数量

    Returns:
        是否更新成功
    """
    db = get_db_manager()
    sql = "UPDATE filled_orders SET unmatched_qty = ? WHERE order_no = ?"

    if conn is None:
        with db.transaction() as transaction_conn:
            _ = transaction_conn.execute(sql, (unmatched_qty, order_no))
    else:
        _ = conn.execute(sql, (unmatched_qty, order_no))
    logger.debug(f"更新Binance订单 {order_no} 未撮合数量: {unmatched_qty}")
    return True


def update_order_profit(
    order_no: str, profit: str, *, conn: sqlite3.Connection | None = None
) -> bool:
    """
    更新订单利润

    Args:
        order_no: 订单号 (SELL订单)
        profit: 利润金额

    Returns:
        是否更新成功
    """
    db = get_db_manager()
    sql = "UPDATE filled_orders SET profit = ? WHERE order_no = ?"

    if conn is None:
        with db.transaction() as transaction_conn:
            _ = transaction_conn.execute(sql, (profit, order_no))
    else:
        _ = conn.execute(sql, (profit, order_no))
    logger.debug(f"更新订单 {order_no} 利润: {profit}")
    return True


def update_order_matched_time(
    order_no: str,
    matched_time: datetime | str,
    *,
    conn: sqlite3.Connection | None = None,
) -> bool:
    """更新订单的撮合完成时间"""
    db = get_db_manager()
    time_str = (
        matched_time
        if isinstance(matched_time, str)
        else to_utc_str(
            matched_time if matched_time.tzinfo else matched_time.replace(tzinfo=UTC)
        )
    )

    sql = "UPDATE filled_orders SET matched_time = ?, updated_at = CURRENT_TIMESTAMP WHERE order_no = ?"

    if conn is None:
        with db.transaction() as transaction_conn:
            _ = transaction_conn.execute(sql, (time_str, order_no))
    else:
        _ = conn.execute(sql, (time_str, order_no))

    logger.debug(f"更新订单 {order_no} 撮合完成时间: {time_str}")
    return True
