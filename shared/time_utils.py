"""
时间工具模块 - 统一时间处理,确保所有时间都使用UTC

CLAUDE.md 要求:
- 统一使用UTC时间戳,避免时区问题
- 提供毫秒级精度的Unix时间戳
- 确保数据库时间的一致性
"""

import time
from datetime import UTC, datetime

from loguru import logger


def get_utc_timestamp_ms() -> int:
    """
    获取当前UTC时间的毫秒时间戳

    Returns:
        int: UTC毫秒时间戳
    """
    return int(time.time() * 1000)


def get_utc_datetime() -> datetime:
    """
    获取当前UTC时间的datetime对象

    Returns:
        datetime: UTC时间对象,带时区信息
    """
    return datetime.now(UTC)


def timestamp_ms_to_utc_str(timestamp_ms: int) -> str:
    """
    将毫秒时间戳转换为UTC时间字符串

    Args:
        timestamp_ms: 毫秒时间戳

    Returns:
        str: UTC时间字符串,格式:YYYY-MM-DD HH:MM:SS
    """
    dt = datetime.fromtimestamp(timestamp_ms / 1000, UTC)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_utc_str(dt_str: str) -> datetime:
    """将 "YYYY-MM-DD HH:MM:SS" UTC 字符串解析为带 UTC tzinfo 的 datetime"""
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)


def to_utc_str(dt: datetime) -> str:
    """将 datetime 格式化为 "YYYY-MM-DD HH:MM:SS" UTC 字符串"""
    # 确保为 UTC 时区
    dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    # 测试时间工具函数
    current_ms = get_utc_timestamp_ms()
    current_dt = get_utc_datetime()
    time_str = timestamp_ms_to_utc_str(current_ms)

    logger.info(f"UTC毫秒时间戳: {current_ms}")
    logger.info(f"UTC datetime: {current_dt}")
    logger.info(f"时间字符串: {time_str}")
