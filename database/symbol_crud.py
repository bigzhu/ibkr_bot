"""
交易对和时间框架配置相关的CRUD操作

提供交易对管理和时间框架配置的数据库操作
"""

import sqlite3
from typing import Any

from loguru import logger

from .connection import DatabaseManager
from .db_config import get_db_manager
from .models import SymbolTimeframeConfig, TradingSymbol


def create_trading_symbol(db_manager: DatabaseManager, symbol: TradingSymbol) -> int:
    """创建交易对记录"""
    query = """
    INSERT INTO trading_symbols (symbol, base_asset, quote_asset, is_active, description)
    VALUES (?, ?, ?, ?, ?)
    """
    with db_manager.transaction() as conn:
        cursor = conn.execute(
            query,
            (
                symbol.symbol,
                symbol.base_asset,
                symbol.quote_asset,
                symbol.is_active,
                symbol.description,
            ),
        )
        logger.info(f"创建交易对记录: {symbol.symbol}")
        row_id = cursor.lastrowid
        if row_id is None:
            raise RuntimeError("Failed to get last row id from database")
        return row_id


def get_symbol_info(symbol: str) -> TradingSymbol:
    """获取交易对信息"""
    db_manager = get_db_manager()
    query = "SELECT * FROM trading_symbols WHERE symbol = ?"
    result = db_manager.execute_query(query, (symbol,))
    if result:
        return TradingSymbol(**dict(result[0]))
    raise ValueError(f"交易对 {symbol} 不存在于数据库中")


def get_symbol_by_id(db_manager: DatabaseManager, symbol_id: int) -> str | None:
    """根据ID获取交易对符号"""
    query = "SELECT symbol FROM trading_symbols WHERE id = ?"
    result = db_manager.execute_query(query, (symbol_id,))
    return result[0]["symbol"] if result else None


def cascade_delete_related_data(
    conn: sqlite3.Connection, symbol: str
) -> dict[str, int]:
    """级联删除交易对相关数据"""
    deletion_counts: dict[str, int] = {}

    # 删除各个表中的相关记录
    deletion_queries = [
        ("configs", "DELETE FROM symbol_timeframe_configs WHERE trading_symbol = ?"),
    ]

    for key, query in deletion_queries:
        cursor = conn.execute(query, (symbol,))
        deletion_counts[key] = cursor.rowcount

    return deletion_counts


def build_deletion_result(
    success: bool, symbol: str, symbol_id: int, counts: dict[str, int]
) -> dict[str, Any]:
    """构建删除操作结果"""
    if not success:
        return {
            "success": False,
            "message": f"交易对 ID {symbol_id} 不存在"
            if not symbol
            else f"删除交易对失败,ID {symbol_id} 可能不存在",
            "deleted_counts": {} if not symbol else None,
        }

    total_deleted = sum(counts.values())
    return {
        "success": True,
        "message": f"成功删除交易对 {symbol} 及其相关数据,共 {total_deleted} 条记录",
        "data": {
            "symbol": symbol,
            "symbol_id": symbol_id,
            "deleted_counts": counts,
            "total_deleted": total_deleted,
        },
    }


def delete_trading_symbol(
    db_manager: DatabaseManager, symbol_id: int
) -> dict[str, Any]:
    """删除交易对记录 - 级联删除所有相关记录"""
    symbol = get_symbol_by_id(db_manager, symbol_id)
    if not symbol:
        logger.warning(f"交易对 ID {symbol_id} 不存在")
        return build_deletion_result(False, "", symbol_id, {})

    with db_manager.transaction() as conn:
        # 级联删除相关数据
        counts = cascade_delete_related_data(conn, symbol)

        # 删除交易对记录
        symbol_cursor = conn.execute(
            "DELETE FROM trading_symbols WHERE id = ?", (symbol_id,)
        )
        counts["symbol"] = symbol_cursor.rowcount

        logger.info(
            f"删除交易对 {symbol} (ID: {symbol_id}): 配置 {counts['configs']} 条, 交易对 {counts['symbol']} 条"
        )

    return build_deletion_result(counts["symbol"] > 0, symbol, symbol_id, counts)


def create_symbol_timeframe_config(
    db_manager: DatabaseManager, config: SymbolTimeframeConfig
) -> int:
    """创建交易对时间框架配置"""
    query = """
    INSERT INTO symbol_timeframe_configs
    (trading_symbol, kline_timeframe, demark_buy, demark_sell, daily_max_percentage,
     monitor_delay, oper_mode, is_active, minimum_profit_percentage)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    with db_manager.transaction() as conn:
        cursor = conn.execute(
            query,
            (
                config.trading_symbol,
                config.kline_timeframe,
                config.demark_buy,
                config.demark_sell,
                config.daily_max_percentage,
                config.monitor_delay,
                config.oper_mode.value,
                config.is_active,
                config.minimum_profit_percentage,
            ),
        )
        logger.info(f"创建配置: {config.trading_symbol}-{config.kline_timeframe}")
        row_id = cursor.lastrowid
        if row_id is None:
            raise RuntimeError("Failed to get last row id from database")
        return row_id


def get_symbol_timeframe_config(symbol: str, timeframe: str) -> SymbolTimeframeConfig:
    """获取交易对时间框架配置"""
    db_manager = get_db_manager()
    query = """
    SELECT * FROM symbol_timeframe_configs
    WHERE trading_symbol = ? AND kline_timeframe = ?
    """
    result = db_manager.execute_query(query, (symbol, timeframe))
    if result:
        return SymbolTimeframeConfig(**dict(result[0]))
    raise ValueError(f"交易对时间框架配置 {symbol} {timeframe} 不存在于数据库中")


if __name__ == "__main__":
    """交易对和时间框架配置CRUD测试"""
    logger.info("📊 交易对CRUD模块")
    logger.info("提供交易对和时间框架配置相关的数据库操作:")
    logger.info("- create_trading_symbol: 创建交易对记录")
    logger.info("- get_trading_symbol: 获取交易对信息")
    logger.info("- delete_trading_symbol: 删除交易对(级联)")
    logger.info("- create_symbol_timeframe_config: 创建时间框架配置")
    logger.info("- get_symbol_timeframe_config: 获取时间框架配置")
