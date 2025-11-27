"""
Web Admin API 数据库辅助函数
基于统一的数据库管理器,提供Web Admin需要的特定查询方法
"""

from contextlib import contextmanager
from typing import Any

from loguru import logger

from database.db_config import get_db_manager
from shared.timeframes import timeframe_order_case


def dict_row_factory(cursor: Any, row: tuple[Any, ...]) -> dict[str, Any]:
    """将 sqlite 行转换为字典的 row_factory"""
    columns: list[str] = [col[0] for col in cursor.description]
    return dict(zip(columns, row, strict=False))


@contextmanager
def with_dict_conn():
    """Yield a connection with dict row_factory set."""
    db_manager = get_db_manager()
    with db_manager.get_connection() as conn:
        conn.row_factory = dict_row_factory
        yield conn


def query_one_dict(
    sql: str, params: tuple[Any, ...] | list[Any] = ()
) -> dict[str, Any] | None:
    """Execute a query and return a single row as dict or None."""
    with with_dict_conn() as conn:
        cur = conn.execute(sql, params)
        return cur.fetchone()


def query_all_dict(
    sql: str, params: tuple[Any, ...] | list[Any] = ()
) -> list[dict[str, Any]]:
    """Execute a query and return all rows as list of dicts."""
    with with_dict_conn() as conn:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        return list(rows)


def compute_pagination(total: int, page: int, page_size: int) -> tuple[int, int]:
    """Compute total_pages and offset for pagination."""
    total_pages = (total + page_size - 1) // page_size
    offset = (page - 1) * page_size
    return total_pages, offset


def get_database_path() -> str:
    """
    获取数据库路径

    Returns:
        str: 数据库文件路径
    """
    db_manager = get_db_manager()
    return str(db_manager.config.db_path)


def get_all_trading_symbols() -> list[dict[str, Any]]:
    """获取所有交易对及其最新信号值和时间周期统计"""

    db_manager = get_db_manager()
    with db_manager.get_connection() as conn:
        conn.row_factory = dict_row_factory

        cursor = conn.execute(
            """
            WITH latest_logs AS (
                SELECT symbol, MAX(run_time) AS max_run_time
                FROM trading_logs
                WHERE kline_timeframe = '1m'
                GROUP BY symbol
            ),
            latest_values AS (
                SELECT tl.symbol,
                       tl.demark  AS latest_signal_value,
                       tl.run_time AS latest_signal_run_time
                FROM trading_logs tl
                INNER JOIN latest_logs ll
                    ON tl.symbol = ll.symbol AND tl.run_time = ll.max_run_time
                WHERE tl.kline_timeframe = '1m'
            ),
            config_stats AS (
                SELECT trading_symbol,
                       SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS active_config_count,
                       SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) AS inactive_config_count,
                       COUNT(*) AS total_config_count
                FROM symbol_timeframe_configs
                GROUP BY trading_symbol
            )
            SELECT ts.*,
                   lv.latest_signal_value   AS signal_value,
                   lv.latest_signal_run_time AS signal_timestamp,
                   COALESCE(cs.active_config_count, 0)   AS active_config_count,
                   COALESCE(cs.inactive_config_count, 0) AS inactive_config_count,
                   COALESCE(cs.total_config_count, 0)    AS total_config_count
            FROM trading_symbols ts
            LEFT JOIN latest_values lv ON lv.symbol = ts.symbol
            LEFT JOIN config_stats cs ON cs.trading_symbol = ts.symbol
            ORDER BY ts.symbol
            """
        )

        symbols: list[dict[str, Any]] = []
        for row in cursor.fetchall():
            symbols.append(row)

        return symbols


def get_all_timeframe_configs() -> list[dict[str, Any]]:
    """
    获取所有timeframe配置

    Returns:
        list[Dict[str, Any]]: 配置列表
    """
    db_manager = get_db_manager()
    with db_manager.get_connection() as conn:
        # 确保返回的行对象可以按字典方式访问
        conn.row_factory = dict_row_factory
        cursor = conn.execute(
            f"""SELECT id, trading_symbol, kline_timeframe, demark_buy, demark_sell,
                      daily_max_percentage,
                      minimum_profit_percentage,
                      monitor_delay, oper_mode, is_active, created_at, updated_at
               FROM symbol_timeframe_configs
               ORDER BY trading_symbol,
               {timeframe_order_case("kline_timeframe")}"""
        )

        configs: list[dict[str, Any]] = []
        for row in cursor.fetchall():
            # row现在已经是字典格式,直接添加到列表
            configs.append(row)

        return configs


def get_timeframe_config_by_symbol(
    trading_symbol: str, kline_timeframe: str | None = None
) -> list[dict[str, Any]]:
    """
    根据交易对获取timeframe配置

    Args:
        trading_symbol: 交易对符号
        kline_timeframe: 可选的时间周期过滤

    Returns:
        list[Dict[str, Any]]: 配置列表
    """
    db_manager = get_db_manager()
    with db_manager.get_connection() as conn:
        # 确保返回的行对象可以按字典方式访问
        conn.row_factory = dict_row_factory
        if kline_timeframe:
            cursor = conn.execute(
                """SELECT * FROM symbol_timeframe_configs
                   WHERE trading_symbol = ? AND kline_timeframe = ?""",
                (trading_symbol, kline_timeframe),
            )
        else:
            cursor = conn.execute(
                f"""SELECT * FROM symbol_timeframe_configs
                   WHERE trading_symbol = ?
                   ORDER BY {timeframe_order_case("kline_timeframe")}""",
                (trading_symbol,),
            )

        configs: list[dict[str, Any]] = []
        for row in cursor.fetchall():
            configs.append(dict(row))

        return configs


def get_active_configs_by_timeframes(timeframes: list[str]) -> list[dict[str, Any]]:
    """
    根据时间维度列表获取活跃的配置

    Args:
        timeframes: 时间维度列表

    Returns:
        list[Dict[str, Any]]: 活跃配置列表,包含交易对信息
    """
    db_manager = get_db_manager()
    if not timeframes:
        return []

    with db_manager.get_connection() as conn:
        # 确保返回的行对象可以按字典方式访问
        conn.row_factory = dict_row_factory
        # 构建 IN 查询语句
        placeholders = ",".join(["?" for _ in timeframes])
        cursor = conn.execute(
            f"""SELECT
                   stc.id, stc.trading_symbol, stc.kline_timeframe,
                   stc.demark_buy, stc.demark_sell,
                   stc.daily_max_percentage,
                   stc.minimum_profit_percentage,
                   stc.monitor_delay, stc.oper_mode, stc.is_active,
                   ts.base_asset, ts.quote_asset, ts.description
               FROM symbol_timeframe_configs stc
               LEFT JOIN trading_symbols ts ON stc.trading_symbol = ts.symbol
               WHERE stc.kline_timeframe IN ({placeholders})
               AND stc.is_active = TRUE
               AND ts.is_active = TRUE
               ORDER BY stc.trading_symbol,
               {timeframe_order_case("stc.kline_timeframe")}""",
            timeframes,
        )

        configs: list[dict[str, Any]] = []
        for row in cursor.fetchall():
            configs.append(
                {
                    "id": row["id"],
                    "trading_symbol": row["trading_symbol"],
                    "kline_timeframe": row["kline_timeframe"],
                    "demark_buy": row["demark_buy"],
                    "demark_sell": row["demark_sell"],
                    "daily_max_percentage": row["daily_max_percentage"],
                    "minimum_profit_percentage": row["minimum_profit_percentage"],
                    "monitor_delay": row["monitor_delay"],
                    "oper_mode": row["oper_mode"],
                    "is_active": row["is_active"],
                    "base_asset": row["base_asset"],
                    "quote_asset": row["quote_asset"],
                    "description": row["description"],
                }
            )

        return configs


def get_system_config(key: str) -> str | None:
    """
    获取系统配置值

    Args:
        key: 配置键

    Returns:
        str | None: 配置值,如果不存在则返回None
    """
    db_manager = get_db_manager()
    with db_manager.get_connection() as conn:
        cursor = conn.execute(
            "SELECT config_value FROM system_config WHERE config_key = ?", (key,)
        )
        result = cursor.fetchone()
        if result:
            # 处理不同的row对象类型 - sqlite3.Row 可以按列名或索引访问
            value = (
                str(result["config_value"])
                if hasattr(result, "keys")
                else str(result[0])
            )
        else:
            value = None
        logger.debug(f"获取系统配置 {key}: result={result}, value={value}")
        return value


def set_system_config(key: str, value: str) -> None:
    """
    设置系统配置值

    Args:
        key: 配置键
        value: 配置值
    """
    db_manager = get_db_manager()
    with db_manager.get_connection() as conn:
        _ = conn.execute(
            """INSERT OR REPLACE INTO system_config (config_key, config_value, updated_at)
               VALUES (?, ?, datetime('now'))""",
            (key, value),
        )
        conn.commit()


def get_all_system_configs() -> dict[str, dict[str, Any]]:
    """
    获取所有系统配置

    Returns:
        dict[str, dict[str, Any]]: 配置字典
    """
    db_manager = get_db_manager()
    with db_manager.get_connection() as conn:
        cursor = conn.execute(
            "SELECT config_key, config_value, created_at, updated_at FROM system_config"
        )
        configs: dict[str, dict[str, Any]] = {}
        for row in cursor.fetchall():
            configs[row[0]] = {
                "value": row[1],
                "created_at": row[2],
                "updated_at": row[3],
            }
        return configs


def _build_where_conditions(
    symbol: str | None = None,
    timeframe: str | None = None,
    execution_status: str | None = None,
    meets_conditions: bool | None = None,
    order_side: str | None = None,
) -> tuple[list[str], list[Any]]:
    """构建动态WHERE条件"""
    where_conditions: list[str] = []
    params: list[Any] = []

    if symbol:
        # 支持多个交易对,用逗号分隔
        symbols = [s.strip() for s in symbol.split(",") if s.strip()]
        if symbols:
            if len(symbols) == 1:
                where_conditions.append("symbol = ?")
                params.append(symbols[0])
            else:
                placeholders = ",".join(["?"] * len(symbols))
                where_conditions.append(f"symbol IN ({placeholders})")
                params.extend(symbols)

    if timeframe:
        # 支持多个时间周期,用逗号分隔
        timeframes = [t.strip() for t in timeframe.split(",") if t.strip()]
        if timeframes:
            if len(timeframes) == 1:
                where_conditions.append("kline_timeframe = ?")
                params.append(timeframes[0])
            else:
                placeholders = ",".join(["?"] * len(timeframes))
                where_conditions.append(f"kline_timeframe IN ({placeholders})")
                params.extend(timeframes)

    if execution_status:
        # 新表结构中,有error字段的记录表示异常执行
        if execution_status == "error":
            where_conditions.append("error IS NOT NULL")
        else:  # normal
            where_conditions.append("error IS NULL")

    if meets_conditions is not None:
        # 新表结构中,有order_id表示满足条件并挂单
        if meets_conditions:
            where_conditions.append("order_id IS NOT NULL")
        else:
            where_conditions.append("order_id IS NULL")

    if order_side:
        where_conditions.append("side = ?")
        params.append(order_side)

    return where_conditions, params


def _get_total_count(conn: Any, where_clause: str, params: list[Any]) -> int:
    """获取总记录数"""
    count_sql = f"SELECT COUNT(*) as total FROM trading_logs WHERE {where_clause}"
    count_cursor = conn.execute(count_sql, params.copy())
    result = count_cursor.fetchone()
    return int(result["total"])


def _get_paginated_logs(
    conn: Any, where_clause: str, params: list[Any], limit: int, offset: int
) -> list[dict[str, Any]]:
    """获取分页日志数据"""
    data_sql = f"""
        SELECT *
        FROM trading_logs
        WHERE {where_clause}
        ORDER BY run_time DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    cursor = conn.execute(data_sql, params)
    return list(cursor.fetchall())


def get_trading_logs_flexible(
    symbol: str | None = None,
    timeframe: str | None = None,
    execution_status: str | None = None,
    meets_conditions: bool | None = None,
    order_side: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """
    灵活获取交易日志,支持可选筛选条件

    Args:
        symbol: 交易对符号(可选)
        timeframe: 时间周期(可选)
        execution_status: 执行状态(可选)
        meets_conditions: 是否满足条件(可选)
        order_side: 挂单方向(可选)
        limit: 返回记录数量限制
        offset: 偏移量

    Returns:
        tuple[list[dict[str, Any]], int]: (交易日志列表, 总记录数)
    """
    db_manager = get_db_manager()

    with db_manager.get_connection() as conn:
        # 确保返回的行对象可以按字典方式访问
        conn.row_factory = dict_row_factory

        where_conditions, params = _build_where_conditions(
            symbol, timeframe, execution_status, meets_conditions, order_side
        )
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        total_count = _get_total_count(conn, where_clause, params)
        logs = _get_paginated_logs(conn, where_clause, params, limit, offset)

        return logs, total_count


def get_trading_logs(
    symbol: str, timeframe: str, limit: int = 1, offset: int = 0
) -> list[dict[str, Any]]:
    """
    获取交易日志(保持向后兼容)

    Args:
        symbol: 交易对符号
        timeframe: 时间周期
        limit: 返回记录数量限制
        offset: 偏移量

    Returns:
        list[dict[str, Any]]: 交易日志列表
    """
    logs, _ = get_trading_logs_flexible(
        symbol, timeframe, None, None, None, limit, offset
    )
    return logs


def get_trading_stats(
    symbol: str | None = None, days: int | None = None
) -> dict[str, Any]:
    """
    获取交易统计信息

    Args:
        symbol: 交易对过滤(可选)
        days: 统计天数(可选,不指定则统计全部)

    Returns:
        dict[str, Any]: 统计数据
    """
    db_manager = get_db_manager()
    with db_manager.get_connection() as conn:
        # 构建基础WHERE条件
        where_conditions = ["1=1"]  # 基础条件
        params: list[Any] = []

        if symbol:
            where_conditions.append("symbol = ?")
            params.append(symbol)

        if days:
            # 计算N天前的时间戳(毫秒)
            where_conditions.append("run_time >= ?")
            import time

            days_ago_ms = int((time.time() - days * 24 * 3600) * 1000)
            params.append(days_ago_ms)

        where_clause = " AND ".join(where_conditions)

        # 统计查询
        sql = f"""
            SELECT
                COUNT(*) as total_signals,
                COUNT(CASE WHEN side = 'BUY' THEN 1 END) as buy_signals,
                COUNT(CASE WHEN side = 'SELL' THEN 1 END) as sell_signals,
                COUNT(CASE WHEN order_id IS NOT NULL THEN 1 END) as conditions_met,
                COUNT(CASE WHEN error IS NOT NULL THEN 1 END) as error_count,
                COUNT(DISTINCT symbol) as symbols_count,
                COUNT(DISTINCT kline_timeframe) as timeframes_count,
                MAX(run_time) as latest_signal
            FROM trading_logs
            WHERE {where_clause}
        """

        cursor = conn.execute(sql, params)
        result = cursor.fetchone()

        # 使用列名访问sqlite3.Row对象
        return {
            "total_signals": result["total_signals"],
            "buy_signals": result["buy_signals"],
            "sell_signals": result["sell_signals"],
            "conditions_met": result["conditions_met"],
            "error_count": result["error_count"],
            "symbols_count": result["symbols_count"],
            "timeframes_count": result["timeframes_count"],
            "latest_signal": result["latest_signal"],
        }


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    logger.info("🗄️ Web Admin 数据库辅助函数")
    logger.info("基于统一数据库管理器,提供Web Admin API需要的查询方法")

    logger.info("\n🧪 测试数据库查询:")
    try:
        symbols = get_all_trading_symbols()
        logger.info(f"交易对数量: {len(symbols)}")

        configs = get_all_timeframe_configs()
        logger.info(f"时间周期配置数量: {len(configs)}")

        if symbols:
            symbol_configs = get_timeframe_config_by_symbol(symbols[0]["symbol"])
            logger.info(f"第一个交易对的配置数量: {len(symbol_configs)}")

        # 测试统计功能
        logger.info("\n📊 测试交易统计:")
        stats = get_trading_stats()
        logger.info(f"统计结果: {stats}")

    except Exception as e:
        logger.info(f"测试失败: {e}")
        import traceback

        traceback.print_exc()
