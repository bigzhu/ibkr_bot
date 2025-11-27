"""订单检查器模块命令行入口"""

import sys

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m order_checker` 运行订单检查器 CLI, 无需手动修改 sys.path"
    )

from collections.abc import Sequence
from decimal import Decimal
from typing import cast

from loguru import logger

# 检查器依赖
from database.models import TradingSymbol
from database.order_models import BinanceOpenOrder
from order_builder.precision_handler import validate_order_limits

# from order_checker.max_trapped_percentage import check_max_trapped_percentage
from order_checker.existing_buy_order import check_buy_price_not_higher_than_open
from order_checker.existing_sell_order import (
    check_sell_price_not_lower_than_open,
)
from order_checker.oper_mode import check_oper_mode_allows_side
from order_checker.signal_validation import check_demark
from shared.constants import BUY, SELL
from shared.typing import SideLiteral

# from order_checker.buy_interval import check_buy_interval


def check(
    symbol: str,
    timeframe: str,
    side: str,
    demark: int,
    qty: Decimal,
    entry_price: Decimal,
    symbol_info: TradingSymbol,
    min_notional: Decimal,
    open_orders: Sequence[BinanceOpenOrder] | None = None,
) -> None:
    """执行所有订单前检查(严格顺序)"""
    literal_side = cast(SideLiteral, side)

    # 1) DeMark 强度检查
    check_demark(symbol, timeframe, side, demark)
    # 2) 交易所下单限制
    validate_order_limits(symbol, qty, entry_price, symbol_info, min_notional)

    # 3) 操作模式
    check_oper_mode_allows_side(symbol, timeframe, literal_side)

    # 4) 挂单价格检查
    if open_orders:
        if side == BUY:
            check_buy_price_not_higher_than_open(entry_price, open_orders)
        elif side == SELL:
            check_sell_price_not_lower_than_open(entry_price, open_orders)


def show_usage() -> None:
    """显示统一入口用法"""
    logger.info("订单检查器 - 统一入口")
    logger.info("=" * 40)
    logger.info("")
    logger.info("用法:")
    logger.info(
        "  p -m order_checker check <symbol> <timeframe> <side> <demark> <qty> <entry_price>"
    )
    logger.info("")
    logger.info("说明:")
    logger.info("  - 顺序执行: DeMark -> 交易所下单限制 -> 操作模式 -> 挂单价格检查")
    logger.info("")
    logger.info("示例:")
    logger.info("  p -m order_checker check ADAUSDC 15m BUY 9 0.5 1.2345")


if __name__ == "__main__":
    # CLI: p -m order_checker check <symbol> <timeframe> <side> <demark> <qty> <entry_price>
    if len(sys.argv) < 2 or sys.argv[1].lower() not in {
        "check",
        "help",
        "-h",
        "--help",
    }:
        show_usage()
        sys.exit(1)

    if sys.argv[1].lower() in {"help", "-h", "--help"}:
        show_usage()
        sys.exit(0)

    if len(sys.argv) != 8:
        show_usage()
        sys.exit(1)

    _, _, sym_arg, tf_arg, side_arg, demark_arg, qty_arg, price_arg = sys.argv
    try:
        # 获取交易对信息和最小名义价值用于测试
        from database.crud import get_symbol_info

        symbol_info = get_symbol_info(sym_arg.upper())
        min_notional = Decimal(symbol_info.min_notional)

        check(
            sym_arg.upper(),
            tf_arg.lower(),
            side_arg.upper(),
            int(demark_arg),
            Decimal(qty_arg),
            Decimal(price_arg),
            symbol_info,
            min_notional,
        )
        logger.info("✅ 全部检查通过 (严格顺序)")
    except Exception as e:
        logger.error(f"❌ 检查失败: {e}")
        sys.exit(1)
