"""DeMark信号相关工具函数

提供基于DeMark信号强度调整百分比要求的通用功能
遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except
"""

from decimal import Decimal

from loguru import logger

from shared.constants import (
    BUY,
    SELL,
)
from shared.number_format import format_percentage


def adjust_percentage_by_demark_signal(
    base_percentage: Decimal,
    demark: int,
    min_demark_value: int,
) -> Decimal:
    """根据 demark 信号强度调整百分比要求

    Args:
        base_percentage: 基础百分比
        demark: demark 信号值
        min_demark_value: 最小 demark 阈值

    Returns:
        调整后的百分比
    """
    signal_excess = demark - min_demark_value
    if signal_excess > 0:
        # 每大于 1, 就减少 0.1 个百分点
        reduction_amount = Decimal("0.1") * signal_excess
        adjusted_percentage = base_percentage - reduction_amount

        # 最小不能小于 0.4%
        final_percentage = max(adjusted_percentage, Decimal("0.4"))

        logger.info(
            f"🎯 DeMark信号强度调整: ({demark} - {min_demark_value}) = {signal_excess}, "
            + f"减少 {format_percentage(reduction_amount)}, "
            + f"调整后要求: {format_percentage(final_percentage)}"
        )
        return final_percentage
    else:
        return base_percentage


def transform_demark_signal(
    side: str,
    value: int,
    unmatched_orders_count: int,
) -> tuple[str, int]:
    """根据业务规则对 DeMark 信号做二次加工 (v36)"""

    if side == BUY and value < 2:  ## 第一个 BUY 归到 尽快跑路
        return SELL, value

    # 没进货, 只有头3个允许进货
    # if side == SELL and 2 < value < 8 and unmatched_orders_count < 2:
    # if side == SELL and value <= 4 and unmatched_orders_count < 2:
    # if side == SELL and unmatched_orders_count < 2:  # 没进货, 一律追高买入(escape all)
    # if side == SELL and value <= 14:  # 信号没超过 14 一律追高买, 坚决不卖
    # if side == SELL:  # 两者翻转了, 和 demark 信号相反的操作
    # if side == SELL and value <= 2:  #
    # if side == SELL and value <= 2 and unmatched_orders_count < 2:
    if side == SELL and value < 4:  ## 1,2,3 前3个追高入场, 避免没上车
        return BUY, value

    return side, value
