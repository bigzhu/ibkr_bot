"""
交易日志相关的CRUD操作

提供交易日志的创建,更新和查询功能,包括事件通知
"""

from contextlib import suppress
from typing import Any

from loguru import logger

from database.connection import DatabaseManager
from database.db_config import get_db_manager
from database.models import TradingLog
from shared.async_notifier import (
    enqueue_trading_log_created,
    enqueue_trading_log_updated,
)

_trading_log_enabled: bool = True
_fake_log_id_counter = 1


def set_trading_log_enabled(enabled: bool) -> None:
    global _trading_log_enabled
    _trading_log_enabled = enabled


def is_trading_log_enabled() -> bool:
    return _trading_log_enabled


def _next_fake_log_id() -> int:
    global _fake_log_id_counter
    current = _fake_log_id_counter
    _fake_log_id_counter += 1
    return current


"""交易日志通知改为异步后台发送,避免阻塞主流程"""


def _build_insert_query_and_params(log: TradingLog) -> tuple[str, tuple[object, ...]]:
    """根据TradingLog对象动态构建插入SQL查询和参数"""
    # 获取所有非None且非id的字段
    fields: list[str] = []
    values: list[str] = []
    params: list[object] = []

    for field_name, field_value in log.model_dump(exclude={"id", "created_at"}).items():
        if field_value is not None:
            fields.append(field_name)
            values.append("?")
            params.append(field_value)

    query = (
        f"INSERT INTO trading_logs ({', '.join(fields)}) VALUES ({', '.join(values)})"
    )
    return query, tuple(params)


def create_trading_log(log: TradingLog) -> int:
    """创建交易日志记录

    注意: 事件发布放在事务提交之后,避免长事务导致 SQLite 写锁占用时间过长.
    """
    if not _trading_log_enabled:
        fake_id = _next_fake_log_id()
        logger.debug("Trading log disabled, returning fake ID %s", fake_id)
        return fake_id

    db_manager = get_db_manager()
    query, params = _build_insert_query_and_params(log)

    # 先完成插入并提交
    with db_manager.transaction() as conn:
        cursor = conn.execute(query, params)
        log_id = cursor.lastrowid
        if log_id is None:
            raise RuntimeError("Failed to get last row id from database")
        logger.info(f"创建交易日志: {log.symbol}-{log.kline_timeframe}, ID: {log_id}")

    # 异步投递通知,不阻塞主流程
    with suppress(Exception):
        enqueue_trading_log_created(log_id, log.model_dump())

    return log_id


def update_trading_log(log_id: int, **kwargs: Any) -> None:
    """更新交易日志记录

    事件通知在事务提交后执行,减少写锁持有时间.
    """
    if not _trading_log_enabled:
        logger.debug("Trading log disabled, skip update for ID %s", log_id)
        return

    if not kwargs:
        return

    db_manager = get_db_manager()
    # 构建 SET 子句
    set_clause = ", ".join([f"{key} = ?" for key in kwargs])
    query = f"UPDATE trading_logs SET {set_clause} WHERE id = ?"

    values = [*kwargs.values(), log_id]

    # 先完成更新并提交
    with db_manager.transaction() as conn:
        _ = conn.execute(query, values)
        logger.info(f"更新交易日志 ID {log_id}: {kwargs}")

    # 异步投递通知,不阻塞主流程
    with suppress(Exception):
        enqueue_trading_log_updated(log_id, kwargs)


def get_recent_trading_logs(
    db_manager: DatabaseManager, symbol: str, timeframe: str, limit: int = 100
) -> list[TradingLog]:
    """获取最近的交易日志"""
    query = """
    SELECT * FROM trading_logs
    WHERE trading_symbol = ? AND kline_timeframe = ?
    ORDER BY processed_at DESC
    LIMIT ?
    """
    results = db_manager.execute_query(query, (symbol, timeframe, limit))
    return [TradingLog(**dict(row)) for row in results]


def check_kline_already_processed(symbol: str, timeframe: str, kline_time: int) -> bool:
    """检查该K线时间是否已经成功处理过(有order_id)

    只有成功下单的记录才算已处理,失败的记录不算.
    这样保证下单失败时,下一个K线周期内仍然可以重试.

    Args:
        symbol: 交易对符号
        timeframe: 时间周期
        kline_time: K线时间(毫秒时间戳)

    Returns:
        True表示该K线已成功处理过(有order_id),False表示未处理或处理失败
    """
    db_manager = get_db_manager()
    query = """
    SELECT COUNT(*) as count FROM trading_logs
    WHERE symbol = ? AND kline_timeframe = ? AND kline_time = ? AND order_id IS NOT NULL
    LIMIT 1
    """
    results = db_manager.execute_query(query, (symbol, timeframe, kline_time))
    if results:
        return results[0]["count"] > 0
    return False


def get_trading_log_by_order_id(order_id: str) -> TradingLog | None:
    """根据 order_id 获取最新的交易日志记录."""
    if not order_id:
        return None

    db_manager = get_db_manager()
    results = db_manager.execute_query(
        """
        SELECT * FROM trading_logs
        WHERE order_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (order_id,),
    )
    if not results:
        return None
    return TradingLog(**dict(results[0]))


if __name__ == "__main__":
    """交易日志CRUD测试"""
    logger.info("📈 交易日志CRUD模块")
    logger.info("提供交易日志相关的数据库操作:")
    logger.info("- create_trading_log: 创建交易日志记录")
    logger.info("- update_trading_log: 更新交易日志记录")
    logger.info("- get_recent_trading_logs: 获取最近交易日志")
