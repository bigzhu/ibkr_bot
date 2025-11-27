"""
代理撮合逻辑模块

实现1m时间周期代理其他时间周期的撮合逻辑,包括安全窗口计算
"""

from datetime import datetime

from loguru import logger

if __name__ == "__main__":
    try:
        from shared.path_utils import ensure_project_root_for_script
    except ImportError:
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from shared.path_utils import ensure_project_root_for_script

    ensure_project_root_for_script(__file__)

# 导入数据库和撮合功能
from order_filler.data_access import get_pending_timeframes_from_db
from order_filler.matching.engine import match_orders


def get_trigger_minutes_for_timeframe(timeframe: str) -> list[int] | None:
    """获取时间周期的触发分钟点列表"""
    if timeframe == "5m":
        return list(range(0, 60, 5))  # [0, 5, 10, ..., 55]
    elif timeframe == "15m":
        return [0, 15, 30, 45]
    elif timeframe == "30m":
        return [0, 30]
    elif timeframe == "1h" or timeframe == "4h":
        return [0]
    else:
        logger.warning(f"未知时间周期: {timeframe}")
        return None


def find_prev_next_triggers(
    trigger_minutes: list[int], current_minute: int
) -> tuple[int | None, int | None]:
    """找到上次和下次触发点"""
    prev_trigger = None
    next_trigger = None

    for minute in trigger_minutes:
        if minute <= current_minute:
            prev_trigger = minute
        if minute > current_minute and next_trigger is None:
            next_trigger = minute
            break

    # 如果没找到下次触发点,说明在下个小时
    if next_trigger is None:
        next_trigger = trigger_minutes[0] + 60

    # 如果没找到上次触发点,说明在上个小时
    if prev_trigger is None:
        prev_trigger = trigger_minutes[-1] - 60

    return prev_trigger, next_trigger


def calculate_time_distances(
    prev_trigger: int, next_trigger: int, current_minute: int, current_second: int
) -> tuple[int, int]:
    """计算距离上次和下次触发的时间(秒)

    通过统一到秒级坐标计算, 支持跨小时(prev<0 或 next>=60).
    """
    current_total = current_minute * 60 + current_second
    prev_total = prev_trigger * 60
    next_total = next_trigger * 60

    time_since_last = current_total - prev_total
    time_to_next = next_total - current_total

    return max(0, time_since_last), max(0, time_to_next)


def calculate_safe_window_status(
    current_time: datetime, timeframe: str
) -> tuple[bool, int, int]:
    """
    计算时间周期的双向安全窗口状态

    Args:
        current_time: 当前时间
        timeframe: 时间周期,如 '5m', '15m', '1h'

    Returns:
        (是否安全, 距离上次触发秒数, 距离下次触发秒数)
    """
    trigger_minutes = get_trigger_minutes_for_timeframe(timeframe)
    if trigger_minutes is None:
        return False, 0, 0

    current_minute = current_time.minute
    current_second = current_time.second

    prev_trigger, next_trigger = find_prev_next_triggers(
        trigger_minutes, current_minute
    )

    # 如果找不到触发点,返回不安全
    if prev_trigger is None or next_trigger is None:
        return False, 0, 0

    time_since_last, time_to_next = calculate_time_distances(
        prev_trigger, next_trigger, current_minute, current_second
    )

    # 双向安全检查: 距离上次触发≥80秒 AND 距离下次触发≥80秒
    is_safe = time_since_last >= 80 and time_to_next >= 80
    return is_safe, time_since_last, time_to_next


def proxy_match_other_timeframes(pair: str) -> None:
    """
    1m时间周期代理撮合其他时间周期的未撮合SELL单

    Args:
        pair: 交易对符号
    """
    # 直接查询需要代理撮合的时间周期
    pending_timeframes = get_pending_timeframes_from_db(pair)

    if not pending_timeframes:
        return

    current_time = datetime.now()

    for tf in pending_timeframes:
        # 计算双向安全窗口状态
        is_safe, time_since_last, time_to_next = calculate_safe_window_status(
            current_time, tf
        )

        if is_safe:
            logger.info(
                f"代理撮合 {tf} 时间周期: 距离上次触发{time_since_last}秒, 距离下次触发{time_to_next}秒"
            )
            _ = match_orders(pair, tf)
        else:
            logger.debug(
                f"跳过代理撮合 {tf}: 距离上次触发{time_since_last}秒, 距离下次触发{time_to_next}秒 (需要双向≥80秒)"
            )


if __name__ == "__main__":
    """代理撮合逻辑测试"""
    logger.info("🔄 代理撮合逻辑模块")
    logger.info("实现1m时间周期代理其他时间周期的撮合:")
    logger.info("- proxy_match_other_timeframes: 主代理撮合函数")
    logger.info("- calculate_safe_window_status: 安全窗口计算")
    logger.info("- get_pending_timeframes_from_db: 待撮合时间周期查询")
