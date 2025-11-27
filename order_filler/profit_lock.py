"""
Binance利润锁定功能模块
计算可安全卖出的数量以保证利润,确保每笔交易都有预期收益
遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except
"""

import sys
from decimal import Decimal
from pathlib import Path
from typing import TypedDict

from loguru import logger

# 导入交易方向常量和工具函数
try:
    from shared.constants import BUY
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from shared.constants import BUY

# 处理相对导入问题
if __name__ == "__main__":
    # 直接运行时添加父目录到路径
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))

from order_filler.data_access import get_unmatched_orders


def calculate_profit_lockable_quantity(
    pair: str,
    current_price: Decimal,
    min_profit_percentage: Decimal,
    timeframe: str,
) -> Decimal:
    """
    计算可安全卖出的数量以保证利润

    Args:
        pair: 交易对符号
        current_price: 当前价格
        min_profit_percentage: 最小利润百分比 (1 = 1%, 0.4 = 0.4%, 必须明确提供)
        timeframe: 时间周期,用于获取配置信息

    Returns:
        可安全卖出的数量
    """
    # 获取未撮合的买单(按价格升序排序)
    buy_orders = get_unmatched_orders(pair, timeframe, side=BUY)

    if not buy_orders:
        return Decimal("0")

    # 计算可用总数量
    available_qty = sum(
        (Decimal(order.unmatched_qty) for order in buy_orders), Decimal("0")
    )

    adjusted_profit_percentage = min_profit_percentage

    # 将百分比转换为小数 (1% -> 0.01)
    min_profit_decimal = adjusted_profit_percentage / Decimal("100")

    # 按价格升序排序(最便宜在前)
    buy_orders.sort(key=lambda x: Decimal(x.average_price))

    # 计算可安全卖出的数量
    lockable_qty = Decimal("0")
    remaining_qty = available_qty

    for buy_order in buy_orders:
        if remaining_qty <= 0:
            break

        buy_price = Decimal(buy_order.average_price)
        unmatched_qty = Decimal(buy_order.unmatched_qty)

        # 计算最小卖出价格(保证利润)
        min_sell_price = buy_price * (1 + min_profit_decimal)

        # 如果当前价格能保证利润
        if current_price >= min_sell_price:
            # 计算这笔买单可锁定的数量
            qty_from_this_order = min(remaining_qty, unmatched_qty)
            lockable_qty += qty_from_this_order
            remaining_qty -= qty_from_this_order
        else:
            break

    return lockable_qty


def main() -> None:
    """CLI helper to preview profit lockable quantity."""
    try:
        args = _parse_cli_args(sys.argv)
    except ValueError as exc:
        logger.error(exc)
        _print_usage()
        return

    lockable_qty = calculate_profit_lockable_quantity(
        pair=args["pair"],
        current_price=args["current_price"],
        min_profit_percentage=args["min_profit_percentage"],
        timeframe=args["timeframe"],
    )
    _display_cli_result(lockable_qty, args)


if __name__ == "__main__":
    main()


class _CLIArgs(TypedDict):
    pair: str
    current_price: Decimal
    min_profit_percentage: Decimal
    timeframe: str


def _parse_cli_args(argv: list[str]) -> _CLIArgs:
    """Convert CLI arguments into keyword arguments for calculation."""
    if len(argv) < 5:
        raise ValueError("参数不足")
    try:
        return _CLIArgs(
            pair=argv[1].upper(),
            current_price=Decimal(argv[2]),
            min_profit_percentage=Decimal(argv[3]),
            timeframe=argv[4],
        )
    except (ValueError, ArithmeticError) as exc:
        raise ValueError(f"参数格式错误: {exc}") from exc


def _display_cli_result(lockable_qty: Decimal, args: _CLIArgs) -> None:
    """Log the calculation input and result for CLI demonstration."""
    logger.info(f"💰 Binance利润锁定分析 - {args['pair']} {args['timeframe']}")
    logger.info("=" * 50)
    logger.info(f"交易对: {args['pair']}")
    logger.info(f"售价: {args['current_price']}")
    logger.info(f"最小利润要求: {args['min_profit_percentage']}%")
    logger.info("")
    logger.info(f"💎 可锁定利润数量: {lockable_qty:.6f}")


def _print_usage() -> None:
    logger.info("用法: p profit_lock.py PAIR CURRENT_PRICE MIN_PROFIT_% TIMEFRAME")
    logger.info("示例: p profit_lock.py ADAUSDC 50000 2 15m")
