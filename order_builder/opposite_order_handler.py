"""
取消反方向挂单功能 - 纯函数实现

专注功能: 当有有效信号时, 取消反方向的未成交订单
遵循 CLAUDE.md 规范: fail-fast 原则, 无 try-except, 纯函数设计
"""

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m order_builder.opposite_order_handler` 运行该模块, 无需手动修改 sys.path"
    )

from loguru import logger

from ibkr_api.cancel_order import cancel_order
from ibkr_api.get_open_orders import get_open_orders
from shared.constants import BUY, SELL


def cancel_opposite_open_orders(symbol: str, current_side: str) -> None:
    """取消指定交易对的反方向未成交订单"""
    opposite_side = SELL if current_side == BUY else BUY
    open_orders = get_open_orders(symbol)

    opposite_orders = [order for order in open_orders if order.side == opposite_side]

    if not opposite_orders:
        logger.debug(f"✅ 无需取消: {symbol} 没有 {opposite_side} 方向的未成交订单")
        return

    cancelled_count = 0
    for order in opposite_orders:
        if order_id := order.order_id:
            logger.warning(f"❌ 取消反方向订单: {symbol} {opposite_side} ID:{order_id}")
            _ = cancel_order(symbol, order_id)
            cancelled_count += 1

    logger.info(f"🔄 已取消 {symbol} {opposite_side} 方向订单 {cancelled_count} 个")


if __name__ == "__main__":
    """独立运行入口 - 测试取消反方向订单功能"""
    import sys

    if len(sys.argv) == 3:
        symbol = sys.argv[1].upper()
        side = sys.argv[2].upper()

        if side not in ["BUY", "SELL"]:
            logger.error("方向必须是 BUY 或 SELL")
            sys.exit(1)

        cancel_opposite_open_orders(symbol, side)
        logger.info("反方向订单取消完成")
    else:
        logger.info("用法: p cancel_opposite_orders.py SYMBOL SIDE")
        logger.info("示例: p cancel_opposite_orders.py ADAUSDC BUY")
        logger.info("说明: 当信号为BUY时, 会取消所有SELL方向的未成交订单")
