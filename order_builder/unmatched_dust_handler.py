"""
unmatched_qty 残留处理器 - 处理无法满足最小名义价值的残留数量

专注功能: 检测和清理 order_filler 表中的 unmatched_qty 残留
当残留数量无法满足币安最小名义价值要求时,自动清零相关 BUY 订单
遵循 CLAUDE.md 规范: fail-fast 原则, 无 try-except, 纯函数设计
"""

from collections.abc import Sequence
from decimal import Decimal

from loguru import logger

from database.db_config import get_db_manager
from database.symbol_crud import get_symbol_info
from order_checker.common import (
    get_unmatched_buy_orders_by_timeframe,
    get_unmatched_value_by_timeframe,
)
from shared.types.order_builder import UnmatchedOrders


def reset_unmatched_qty_to_zero(
    symbol: str,
    timeframe: str,
    min_notional: Decimal,
    unmatched_orders: UnmatchedOrders,
    force: bool = False,
    candidates_override: Sequence[tuple[str, Decimal]] | None = None,
) -> None:
    """重置 BUY unmatched_qty, BNB 交易对放宽最小名义价值约束

    Args:
        symbol: 交易对符号
        timeframe: 时间框架
        min_notional: 最小名义价值
        unmatched_orders: 未匹配订单列表
        force: 强制重置, 忽略 min_notional 的限制, 重置所有 unmatched_qty > 0 的订单

    Returns:
        None
    """

    if candidates_override is not None:
        candidates = [
            (str(order_no), Decimal(str(qty))) for order_no, qty in candidates_override
        ]
    else:
        orders = unmatched_orders
        candidates = []
        trading_symbol = get_symbol_info(symbol)
        is_base_asset_bnb = trading_symbol.base_asset.upper() == "BNB"

        for order in orders:
            qty = Decimal(str(order.unmatched_qty))
            price = Decimal(str(order.average_price))
            if qty <= 0 or price <= 0:
                continue
            # 强制模式: 重置所有 unmatched_qty > 0 的订单
            # 普通模式: 只重置名义价值低于最小要求或 BNB 交易对的订单
            if force or (qty * price) < min_notional or is_base_asset_bnb:
                candidates.append((str(order.order_no), qty))

    if not candidates:
        error_msg = (
            f"未找到 {symbol} {timeframe} 任何 unmatched_qty > 0 的订单"
            if force
            else f"未找到 {symbol} {timeframe} 名义价值低于 {min_notional} 的残留订单需要重置"
        )
        logger.info(error_msg)
        return None

    db = get_db_manager()
    total_reset_qty = Decimal("0")

    with db.transaction() as conn:
        for order_no, qty in candidates:
            total_reset_qty += qty
            _ = conn.execute(
                "UPDATE filled_orders SET unmatched_qty = '0' WHERE order_no = ?",
                (order_no,),
            )

    mode = "强制" if force else "安全"
    logger.info(
        f"🔄 [{mode}模式] 已重置 {symbol} {timeframe} BUY订单 {len(candidates)} 条, 总数量 {total_reset_qty}"
    )
    return None


if __name__ == "__main__":
    """独立运行入口 - 检测和清理残留的 unmatched_qty"""
    import sys

    if len(sys.argv) == 3:
        symbol = sys.argv[1].upper()
        timeframe = sys.argv[2].lower()

        # 获取必要的参数用于测试
        unmatched_orders = get_unmatched_buy_orders_by_timeframe(symbol, timeframe)
        total_unmatched_value = get_unmatched_value_by_timeframe(symbol, timeframe)

        symbol_info = get_symbol_info(symbol)
        min_notional = Decimal(symbol_info.min_notional)

        # 如果实际价值低于最小要求,说明是无法下单的残留数量
        if total_unmatched_value != 0 and total_unmatched_value < min_notional:
            reset_unmatched_qty_to_zero(
                symbol, timeframe, min_notional, unmatched_orders
            )
    else:
        logger.info("用法: p unmatched_dust_handler.py SYMBOL TIMEFRAME")
        logger.info("示例: p unmatched_dust_handler.py ADAUSDC 15m")
