"""
订单数据访问层 - 统一导出接口

将所有数据访问操作集中在此包, 包括:
- crud: 基础增删改查
- queries: 复杂查询和统计
- updates: 订单字段更新
- matches: 撮合详情管理
"""

from order_filler.data_access.crud import (
    clear_all_orders,
    get_order_count,
    insert_order,
    insert_orders,
    order_exists,
)
from order_filler.data_access.matches import (
    get_order_matches_by_buy_order,
    get_order_matches_by_sell_order,
    insert_order_match,
)
from order_filler.data_access.queries import (
    get_latest_order_id,
    get_latest_order_time,
    get_orders_by_pair,
    get_pending_timeframes_from_db,
    get_today_unmatched_buy_orders_total,
    get_unmatched_orders,
)
from order_filler.data_access.updates import (
    update_order_matched_time,
    update_order_profit,
    update_order_unmatched_qty,
)

__all__ = [
    "clear_all_orders",
    "get_latest_order_id",
    "get_latest_order_time",
    "get_order_count",
    "get_order_matches_by_buy_order",
    "get_order_matches_by_sell_order",
    "get_orders_by_pair",
    "get_pending_timeframes_from_db",
    "get_today_unmatched_buy_orders_total",
    "get_unmatched_orders",
    "insert_order",
    "insert_order_match",
    "insert_orders",
    "order_exists",
    "update_order_matched_time",
    "update_order_profit",
    "update_order_unmatched_qty",
]
