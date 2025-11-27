"""
订单撮合引擎模块

实现核心的订单撮合算法,处理BUY/SELL订单的撮合逻辑
"""

import os
import sqlite3
from decimal import Decimal

from loguru import logger

# 统一双重用途模块导入处理(仅处理 ImportError)
try:
    from shared.path_utils import add_project_root_to_path
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from shared.path_utils import add_project_root_to_path

add_project_root_to_path()

# 导入工具函数
# 导入数据模型和订单操作
from database.db_config import get_db_manager
from database.models import BinanceFilledOrder, MatchingStats
from order_filler.data_access import (
    get_unmatched_orders,
    insert_order_match,
    update_order_matched_time,
    update_order_profit,
    update_order_unmatched_qty,
)
from order_filler.matching.utils import (
    add_to_buy_pool,
    calculate_match_profit,
    normalize_decimal_string,
    update_order_after_match,
)
from shared.clock import now_utc
from shared.constants import BUY, SELL

DISABLE_ORDER_MATCH_PERSISTENCE = os.getenv(
    "DISABLE_ORDER_MATCH_PERSISTENCE", "0"
).lower() in ("1", "true", "yes")


def match_sell_with_buy_pool(
    sell_order: BinanceFilledOrder,
    buy_pool: list[BinanceFilledOrder],
    pair: str,
    timeframe: str,
    conn: sqlite3.Connection,
) -> int:
    """
    用SELL订单与买单池撮合

    Args:
        sell_order: 卖单
        buy_pool: 买单池
        pair: 交易对符号
        timeframe: 时间周期

    Returns:
        撮合成功的买单数量
    """
    matched_count = 0
    sell_qty_remaining = Decimal(sell_order.unmatched_qty)
    sell_price = Decimal(sell_order.average_price)

    # 遍历买单池,按价格优先原则撮合(最便宜的先撮合)
    for buy_order in buy_pool.copy():
        if sell_qty_remaining <= 0:
            break

        buy_qty_remaining = Decimal(buy_order.unmatched_qty)
        if buy_qty_remaining <= 0:
            continue

        buy_price = Decimal(buy_order.average_price)

        # 确定撮合数量(取较小值)
        match_qty = min(sell_qty_remaining, buy_qty_remaining)

        # 计算撮合利润
        match_profit = calculate_match_profit(buy_price, sell_price, match_qty)

        # 更新订单信息
        _ = update_order_after_match(
            buy_order,
            sell_order,
            match_qty,
            match_profit,
        )

        # 记录撮合详情到数据库
        if not DISABLE_ORDER_MATCH_PERSISTENCE:
            _ = insert_order_match(
                sell_order_no=sell_order.order_no,
                buy_order_no=buy_order.order_no,
                sell_price=sell_order.average_price,
                buy_price=buy_order.average_price,
                matched_qty=str(match_qty),
                profit=str(match_profit),
                pair=pair,
                timeframe=timeframe,
                conn=conn,
            )

        # 更新BUY订单未匹配数量到数据库
        _ = update_order_unmatched_qty(
            buy_order.order_no, buy_order.unmatched_qty, conn=conn
        )
        matched_count += 1

        # 如果BUY订单完全撮合,从池中移除
        if Decimal(buy_order.unmatched_qty) == 0:
            _ = update_order_matched_time(buy_order.order_no, now_utc(), conn=conn)
            buy_pool.remove(buy_order)

        # 更新SELL剩余数量
        sell_qty_remaining -= match_qty

    # 处理剩余的SELL订单
    if sell_qty_remaining > 0:
        # 检查买单池中是否还有可用的BUY订单
        has_available_buy_orders = any(
            Decimal(order.unmatched_qty) > 0 for order in buy_pool
        )

        if not has_available_buy_orders:
            # 买单池已耗尽,强制设置SELL订单为完全匹配
            logger.debug(
                f"买单池已耗尽, SELL订单 {sell_order.order_no} 剩余数量 {sell_qty_remaining} 强制设置为完全匹配"
            )

            # 强制设置为0(完全匹配)
            sell_qty_remaining = Decimal("0")

    # 更新SELL订单的unmatched_qty字段
    sell_order.unmatched_qty = normalize_decimal_string(sell_qty_remaining)

    # 更新SELL订单到数据库
    _ = update_order_unmatched_qty(
        sell_order.order_no, sell_order.unmatched_qty, conn=conn
    )
    _ = update_order_profit(sell_order.order_no, sell_order.profit, conn=conn)

    return matched_count


def process_order_matching(
    unmatched_orders: list[BinanceFilledOrder],
    pair: str,
    timeframe: str,
    conn: sqlite3.Connection,
) -> tuple[list[BinanceFilledOrder], int]:
    """处理订单撮合逻辑"""
    buy_pool: list[BinanceFilledOrder] = []
    matched_pairs = 0

    for order in unmatched_orders:
        if order.side == BUY:
            add_to_buy_pool(buy_pool, order)
        elif order.side == SELL:
            matched_count = match_sell_with_buy_pool(
                order,
                buy_pool,
                pair,
                timeframe,
                conn,
            )
            matched_pairs += matched_count

    return buy_pool, matched_pairs


def match_orders(pair: str, timeframe: str) -> MatchingStats:
    """
    执行订单撮合

    Args:
        pair: 交易对符号
        timeframe: 时间周期,用于获取配置信息

    Returns:
        撮合统计信息
    """
    unmatched_orders = get_unmatched_orders(pair, timeframe)

    if not unmatched_orders:
        return MatchingStats(
            symbol=pair,
            processed_orders=0,
            matched_transactions=0,
            buy_orders_pooled=0,
            remaining_buy_orders=0,
        )

    db = get_db_manager()
    with db.transaction() as conn:
        buy_pool, matched_pairs = process_order_matching(
            unmatched_orders,
            pair,
            timeframe,
            conn,
        )

    remaining_buy_orders = len([o for o in buy_pool if Decimal(o.unmatched_qty) > 0])

    return MatchingStats(
        symbol=pair,
        processed_orders=len(unmatched_orders),
        matched_transactions=matched_pairs,
        buy_orders_pooled=len(buy_pool),
        remaining_buy_orders=remaining_buy_orders,
    )


if __name__ == "__main__":
    """撮合引擎测试"""
    logger.info("⚙️ 订单撮合引擎模块")
    logger.info("实现核心的订单撮合算法:")
    logger.info("- match_orders: 主撮合函数")
    logger.info("- match_sell_with_buy_pool: SELL订单与买单池撮合")
    logger.info("- process_order_matching: 撮合逻辑处理")
