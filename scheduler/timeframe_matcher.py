"""
时间周期匹配器 - 每分钟返回所有活跃的时间周期配置

功能:
1. 每次调用都从数据库查询所有活跃时间周期
2. 每分钟都返回这些周期,确保即使不是整点也能执行
3. 支持 1m, 5m, 15m, 30m, 1h, 4h, 1d 时间周期

设计说明:
原设计按时间整点判断(如15m只在00/15/30/45分执行),
现改为每分钟都返回所有活跃配置的时间周期,
让调度器能够连续检查是否需要挂单,避免因价格波动错过挂单机会.
当前实现移除了缓存,以便配置更新后马上生效.

用法:
    p timeframe_matcher.py  # 测试当前时间匹配
"""

import sys
from datetime import UTC, datetime

from loguru import logger

# 添加模块路径 - 仅用于双重用途模块支持
# (当前模块既可import使用, 也可独立运行)


def get_matched_timeframes(current_time: datetime) -> list[str]:
    """
    获取所有活跃的时间周期配置

    每次调用都会从数据库查询启用的时间周期,
    确保配置更新后无需重启即可生效.

    Args:
        current_time: 当前时间(参数保留以保持接口兼容性,但暂未使用)

    Returns:
        所有活跃的时间周期列表
    """
    # current_time 暂未使用, 保留用于未来按时间过滤等扩展
    _ = current_time
    return _load_active_timeframes_from_db()


def _load_active_timeframes_from_db() -> list[str]:
    """从数据库加载所有活跃的时间周期"""
    try:
        from database import get_database_manager
        from database.db_config import get_default_database_config

        db_manager = get_database_manager(get_default_database_config())
        results = db_manager.execute_query(
            """
            SELECT DISTINCT kline_timeframe
            FROM symbol_timeframe_configs
            WHERE is_active = 1
            ORDER BY
                CASE kline_timeframe
                    WHEN '1m' THEN 1
                    WHEN '5m' THEN 2
                    WHEN '15m' THEN 3
                    WHEN '30m' THEN 4
                    WHEN '1h' THEN 5
                    WHEN '4h' THEN 6
                    WHEN '1d' THEN 7
                    ELSE 99
                END
            """
        )
        timeframes = [row["kline_timeframe"] for row in results]
        logger.debug(f"从数据库加载活跃时间周期: {timeframes}")
        return timeframes
    except Exception as e:
        logger.warning(f"无法从数据库加载时间周期: {e}, 返回空列表")
        return []


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        logger.info(__doc__)
        sys.exit(0)

    try:
        from shared.path_utils import ensure_project_root_for_script
    except ImportError:
        sys.path.insert(
            0, str(__import__("pathlib").Path(__file__).resolve().parents[1])
        )
        from shared.path_utils import ensure_project_root_for_script

    ensure_project_root_for_script(__file__)

    # 测试当前时间匹配
    current_time = datetime.now(UTC)
    matched = get_matched_timeframes(current_time)

    logger.info(f"当前时间 (UTC): {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"匹配的活跃时间周期: {matched}")
    logger.info("说明: 现在每分钟都会返回数据库中启用的所有时间周期")
