"""
配置加载器 - 数据库配置查询纯函数

功能:
1. 根据时间周期列表查询活跃的交易配置
2. 提供配置过滤和格式化功能

用法:
    p config_loader.py  # 测试配置查询
"""

from typing import Any

from loguru import logger

if __name__ == "__main__":
    try:
        from shared.path_utils import ensure_project_root_for_script
    except ImportError:
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from shared.path_utils import ensure_project_root_for_script

    ensure_project_root_for_script(__file__)

from database import get_database_manager
from database.db_config import get_default_database_config


def get_active_configs_by_timeframes(
    db_manager: Any, timeframes: list[str]
) -> list[dict[str, Any]]:
    """
    根据时间维度列表获取活跃的交易配置

    Args:
        db_manager: 数据库管理器
        timeframes: 时间周期列表

    Returns:
        活跃的交易配置列表
    """
    if not timeframes:
        return []

    # 构建查询SQL - 同时检查交易对和配置的激活状态
    placeholders = ",".join(["?" for _ in timeframes])
    sql = f"""
        SELECT c.id, c.trading_symbol, c.kline_timeframe, c.demark_buy,
               c.daily_max_percentage,
               c.monitor_delay, c.oper_mode, c.is_active
        FROM symbol_timeframe_configs c
        INNER JOIN trading_symbols s ON c.trading_symbol = s.symbol
        WHERE c.kline_timeframe IN ({placeholders})
        AND c.is_active = 1
        AND s.is_active = 1
        ORDER BY c.trading_symbol, c.kline_timeframe
    """

    results = db_manager.execute_query(sql, tuple(timeframes))

    # 格式化结果
    matched_configs: list[dict[str, Any]] = []
    for row in results:
        config = format_config_row(row)
        matched_configs.append(config)

    debug_msg = (
        f"匹配到 {len(matched_configs)} 个激活配置 (交易对和配置均激活): "
        f"时间周期={timeframes}, 配置={[format_config_summary(c) for c in matched_configs]}"
    )
    logger.debug(debug_msg)

    return matched_configs


def format_config_row(row: dict[str, Any]) -> dict[str, Any]:
    """
    格式化单个配置行数据

    Args:
        row: 数据库查询结果行

    Returns:
        格式化后的配置字典
    """
    return {
        "id": row["id"],
        "trading_symbol": row["trading_symbol"],
        "kline_timeframe": row["kline_timeframe"],
        "demark_buy": row["demark_buy"],
        "daily_max_percentage": row["daily_max_percentage"],
        "monitor_delay": row["monitor_delay"],
        "oper_mode": row["oper_mode"],
        "is_active": bool(row["is_active"]),
    }


def format_config_summary(config: dict[str, Any]) -> str:
    """
    生成配置摘要字符串

    Args:
        config: 配置字典

    Returns:
        配置摘要字符串
    """
    return f"{config['trading_symbol']}-{config['kline_timeframe']}"


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        logger.info(__doc__)
        sys.exit(0)

    # 测试配置查询
    db_manager = get_database_manager(get_default_database_config())

    # 测试按时间周期查询
    test_timeframes = ["1m", "3m", "5m"]
    matched_configs = get_active_configs_by_timeframes(db_manager, test_timeframes)
    logger.info(f"时间周期 {test_timeframes} 匹配配置: {len(matched_configs)}")

    # 显示匹配配置的摘要
    if matched_configs:
        for config in matched_configs[:5]:
            logger.info(f"配置: {format_config_summary(config)}")
