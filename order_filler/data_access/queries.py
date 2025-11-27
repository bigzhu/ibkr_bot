"""
订单复杂查询操作

提供订单的复杂查询和统计功能
"""

from loguru import logger

from database import get_database_manager
from database.db_config import get_db_manager, get_default_database_config
from database.models import BinanceFilledOrder
from shared.timeframe_utils import base_timeframe, timeframe_candidates


def get_orders_by_pair(pair: str) -> list[BinanceFilledOrder]:
    """
    获取指定交易对的所有订单

    Args:
        pair: 交易对符号

    Returns:
        订单列表
    """
    db = get_db_manager()
    sql = """
        SELECT * FROM filled_orders
        WHERE pair = ?
        ORDER BY time DESC
    """

    rows = db.execute_query(sql, (pair,))

    return [BinanceFilledOrder.from_db_dict(dict(row)) for row in rows]


def get_unmatched_orders(
    pair: str, timeframe: str, side: str | None = None
) -> list[BinanceFilledOrder]:
    """
    获取指定交易对的未撮合订单

    Args:
        pair: 交易对符号
        timeframe: 时间周期,用于获取配置信息
        side: 交易方向过滤, None 表示不限制

    Returns:
        未撮合订单列表
    """
    db = get_db_manager()
    sql = """
        SELECT * FROM filled_orders
        WHERE pair = ? AND unmatched_qty > 0 AND status = 'FILLED'
        AND client_order_id IN (?, ?)
    """
    params: list[str | int] = []
    params.append(pair)
    candidates = timeframe_candidates(timeframe)
    params.extend((candidates[0], candidates[1]))

    if side:
        sql += " AND side = ?"
        params.append(side)

    sql += " ORDER BY time ASC"

    rows = db.execute_query(sql, tuple(params))

    return [BinanceFilledOrder.from_db_dict(dict(row)) for row in rows]


def get_latest_order_id(pair: str) -> int | None:
    """
    获取指定交易对的最新订单ID

    Args:
        pair: 交易对符号

    Returns:
        最新订单ID,如果没有订单则返回None
    """
    db = get_db_manager()
    sql = """
        SELECT MAX(CAST(order_no AS INTEGER)) as latest_order_id
        FROM filled_orders
        WHERE pair = ?
    """
    result = db.execute_query(sql, (pair,))
    if result and result[0][0]:
        return int(result[0][0])
    return None


def get_latest_order_time(pair: str) -> int | None:
    """
    获取指定交易对的最新订单时间戳(毫秒)

    Args:
        pair: 交易对符号

    Returns:
        最新订单时间戳(毫秒),如果没有订单则返回None
    """
    db = get_db_manager()
    sql = """
        SELECT MAX(CAST(time AS INTEGER)) as latest_time
        FROM filled_orders
        WHERE pair = ?
    """

    rows = db.execute_query(sql, (pair,))
    if rows and rows[0] and rows[0][0] is not None:
        return int(rows[0][0])
    return None


def get_today_unmatched_buy_orders_total(pair: str) -> float:
    """
    获取指定交易对今日未撮合BUY订单的总成交金额

    查询order_filler表中指定交易对今日成交且unmatched_qty不为0的BUY单,
    累加这些订单的trading_total字段值.

    Args:
        pair: 交易对符号

    Returns:
        累加的总成交金额
    """
    db = get_db_manager()
    sql = """
        SELECT SUM(unmatched_qty * CAST(average_price AS REAL)) as total_amount
        FROM filled_orders
        WHERE pair = ?
        AND side = 'BUY'
        AND unmatched_qty > 0
        AND status = 'FILLED'
        AND DATE(time) = DATE('now', 'utc')
    """

    result = db.execute_query(sql, (pair,))
    if result and result[0] and result[0][0] is not None:
        return float(result[0][0])
    return 0.0


def get_pending_timeframes_from_db(pair: str) -> list[str]:
    """
    从数据库查询需要代理撮合的时间周期,处理_1后缀

    Args:
        pair: 交易对符号

    Returns:
        需要代理撮合的基础时间周期列表
    """
    db_manager = get_database_manager(get_default_database_config())
    tf_candidates = timeframe_candidates("1m")
    in_clause = ", ".join([f"'{tf}'" for tf in tf_candidates])
    sql = f"""
        SELECT DISTINCT client_order_id
        FROM filled_orders
        WHERE pair = ?
          AND side = 'SELL'
          AND unmatched_qty > 0
          AND client_order_id NOT IN ({in_clause})
    """

    with db_manager.get_connection() as conn:
        results = conn.execute(sql, (pair,)).fetchall()
        raw_timeframes = [row[0] for row in results if row[0]]

    # 提取基础时间周期,去重
    base_timeframes: set[str] = set()
    for tf in raw_timeframes:
        base_tf = base_timeframe(tf)
        base_timeframes.add(base_tf)

    timeframes = list(base_timeframes)
    logger.debug(f"原始时间周期: {raw_timeframes}")
    logger.debug(f"提取基础时间周期: {timeframes}")

    return timeframes
