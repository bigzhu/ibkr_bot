"""
订单基础CRUD操作

提供订单的基本增删改查功能
"""

from collections.abc import Iterable, Sequence
from decimal import Decimal

from loguru import logger

from database.db_config import get_db_manager
from database.models import BinanceFilledOrder


def order_exists(order_no: str) -> bool:
    """
    检查订单是否已存在

    Args:
        order_no: 订单号

    Returns:
        订单是否存在
    """
    db = get_db_manager()
    sql = "SELECT 1 FROM filled_orders WHERE order_no = ? LIMIT 1"
    result = db.execute_query(sql, (order_no,))
    return len(result) > 0


def _derive_matched_time(order: BinanceFilledOrder) -> str | None:
    """根据订单状态推断撮合完成时间"""
    if order.matched_time:
        return order.matched_time

    if order.side.upper() != "BUY":
        return None

    if Decimal(str(order.unmatched_qty)) == Decimal("0"):
        return order.time

    return None


def insert_order(order: BinanceFilledOrder) -> bool:
    """
    插入新订单

    Args:
        order: 订单数据

    Returns:
        是否插入成功 (如果订单已存在返回False)
    """
    return insert_orders([order]) > 0


def _calculate_commission(order: BinanceFilledOrder) -> str:
    """按 0.1% 费率计算手续费"""
    trading_total_decimal = Decimal(str(order.trading_total))
    commission_rate = Decimal("0.001")
    return str(trading_total_decimal * commission_rate)


def _build_insert_params(order: BinanceFilledOrder) -> tuple[str | None, ...]:
    """构造订单插入参数"""
    return (
        order.date_utc,
        order.order_no,
        order.pair,
        order.order_type,
        order.side,
        order.order_price,
        order.order_amount,
        order.time,
        _derive_matched_time(order),
        order.executed,
        order.average_price,
        order.trading_total,
        order.status,
        order.unmatched_qty,
        order.client_order_id,
        _calculate_commission(order),
    )


def insert_orders(
    orders: Sequence[BinanceFilledOrder] | Iterable[BinanceFilledOrder],
) -> int:
    """
    批量插入订单, 使用 INSERT OR IGNORE 自动去重

    Args:
        orders: 订单序列

    Returns:
        成功插入的订单数量
    """
    orders_list = list(orders)
    if not orders_list:
        return 0

    sql = """
        INSERT OR IGNORE INTO filled_orders (
            date_utc, order_no, pair, order_type, side, order_price,
            order_amount, time, matched_time, executed, average_price, trading_total,
            status, unmatched_qty, client_order_id, commission
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params_list = [_build_insert_params(order) for order in orders_list]

    db = get_db_manager()
    with db.transaction() as conn:
        before = conn.total_changes
        _ = conn.executemany(sql, params_list)
        inserted = conn.total_changes - before

    return inserted


def clear_all_orders() -> int:
    """
    清空所有订单数据

    Returns:
        删除的订单数量
    """
    db = get_db_manager()

    # 先统计总数
    count_sql = "SELECT COUNT(*) FROM filled_orders"
    count_result = db.execute_query(count_sql)
    total_count = count_result[0][0] if count_result else 0

    # 使用 DELETE 清空表数据 (SQLite 不支持 TRUNCATE)
    delete_sql = "DELETE FROM filled_orders"
    with db.transaction() as conn:
        _ = conn.execute(delete_sql)
        # SQLite 手动重置自增ID
        _ = conn.execute("DELETE FROM sqlite_sequence WHERE name='filled_orders'")

    logger.info(f"已清空所有订单数据, 删除 {total_count} 条记录")
    return total_count


def get_order_count(pair: str) -> int:
    """
    获取指定交易对的订单总数

    Args:
        pair: 交易对符号

    Returns:
        订单总数
    """
    db = get_db_manager()
    sql = "SELECT COUNT(*) FROM filled_orders WHERE pair = ?"
    result = db.execute_query(sql, (pair,))
    return result[0][0] if result else 0
