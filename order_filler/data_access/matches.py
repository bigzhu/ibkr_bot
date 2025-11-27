"""
订单撮合详情操作

提供订单撮合记录的管理功能
"""

import sqlite3
from typing import Any

from loguru import logger

from database.db_config import get_db_manager

_INSERT_SQL = """
        INSERT INTO order_matches (
            sell_order_no, buy_order_no, sell_price, buy_price,
            matched_qty, profit, pair, timeframe
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

_SELECT_SQL_TEMPLATE = """
        SELECT
            id, sell_order_no, buy_order_no, sell_price, buy_price,
            matched_qty, profit, pair, timeframe,
            matched_at, created_at
        FROM order_matches
        WHERE {column} = ?
        ORDER BY matched_at ASC
    """


def insert_order_match(
    sell_order_no: str,
    buy_order_no: str,
    sell_price: str,
    buy_price: str,
    matched_qty: str,
    profit: str,
    pair: str,
    timeframe: str,
    *,
    conn: sqlite3.Connection | None = None,
) -> int:
    """
    插入撮合详情记录

    Args:
        sell_order_no: SELL单订单号
        buy_order_no: BUY单订单号
        sell_price: SELL单价格
        buy_price: BUY单价格
        matched_qty: 撮合数量
        profit: 单笔利润
        pair: 交易对
        timeframe: 时间周期

    Returns:
        插入的记录ID
    """
    db = get_db_manager()

    if conn is None:
        with db.transaction() as transaction_conn:
            cursor = transaction_conn.execute(
                _INSERT_SQL,
                (
                    sell_order_no,
                    buy_order_no,
                    sell_price,
                    buy_price,
                    matched_qty,
                    profit,
                    pair,
                    timeframe,
                ),
            )
            record_id = cursor.lastrowid
            if record_id is None:
                raise RuntimeError("Failed to get last row id from database")
    else:
        cursor = conn.execute(
            _INSERT_SQL,
            (
                sell_order_no,
                buy_order_no,
                sell_price,
                buy_price,
                matched_qty,
                profit,
                pair,
                timeframe,
            ),
        )
        record_id = cursor.lastrowid
        if record_id is None:
            raise RuntimeError("Failed to get last row id from database")

    logger.debug(
        f"撮合详情已记录: SELL {sell_order_no} 与 BUY {buy_order_no}, ID: {record_id}"
    )
    return record_id


def get_order_matches_by_sell_order(sell_order_no: str) -> list[dict[str, Any]]:
    """
    查询指定SELL单的撮合详情

    Args:
        sell_order_no: SELL单订单号

    Returns:
        撮合详情列表
    """
    return _fetch_matches("sell_order_no", sell_order_no)


def get_order_matches_by_buy_order(buy_order_no: str) -> list[dict[str, Any]]:
    """
    查询指定BUY单的撮合详情

    Args:
        buy_order_no: BUY单订单号

    Returns:
        撮合详情列表
    """
    return _fetch_matches("buy_order_no", buy_order_no)


# --- Helpers ----------------------------------------------------------------


def _fetch_matches(column: str, value: str) -> list[dict[str, Any]]:
    db = get_db_manager()
    sql = _SELECT_SQL_TEMPLATE.format(column=column)
    result = db.execute_query(sql, (value,))
    return [_row_to_match_dict(row) for row in result]


def _row_to_match_dict(row: Any) -> dict[str, Any]:
    return {
        "id": row[0],
        "sell_order_no": row[1],
        "buy_order_no": row[2],
        "sell_price": row[3],
        "buy_price": row[4],
        "matched_qty": row[5],
        "profit": row[6],
        "pair": row[7],
        "timeframe": row[8],
        "matched_at": row[9],
        "created_at": row[10],
    }
