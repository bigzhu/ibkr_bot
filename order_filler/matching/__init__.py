"""
订单撮合模块子包

将订单撮合功能组织为独立子包,包含:
- engine: 核心撮合引擎和算法
- utils: 撮合工具函数和辅助逻辑
- cli: 命令行入口和测试
- proxy: 代理撮合逻辑(1m代理其他时间周期)

统一导出公开 API,内部实现逻辑完全隔离
"""

from order_filler.matching.engine import match_orders, process_order_matching
from order_filler.matching.proxy import proxy_match_other_timeframes
from order_filler.matching.utils import (
    add_to_buy_pool,
    calculate_match_profit,
    normalize_decimal_string,
    update_order_after_match,
)

__all__ = [
    "add_to_buy_pool",
    "calculate_match_profit",
    "match_orders",
    "normalize_decimal_string",
    "process_order_matching",
    "proxy_match_other_timeframes",
    "update_order_after_match",
]
