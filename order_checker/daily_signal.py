"""order_builder 天级信号方向检查器

检查天级DeMark信号方向是否与当前订单方向一致,防止逆势交易.
遵循 fail-fast 原则, 异常直接向上传播.
"""

import sys

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m order_checker.daily_signal` 运行该模块, 无需手动修改 sys.path"
    )

from typing import cast

from loguru import logger

from indicators.demark.binance_demark import demark_with_binance_api as demark_checker
from shared.typing import SideLiteral


def check_daily_signal_direction(symbol: str, side: SideLiteral) -> None:
    """检查天级DeMark信号方向是否与当前订单方向一致

    Args:
        symbol: 交易对符号
        side: 当前订单方向 (BUY/SELL)

    Raises:
        ValueError: 天级信号方向与当前订单方向不一致时抛出异常
        Exception: DeMark信号检查失败时抛出异常
    """

    daily_side, daily_demark, _, _ = demark_checker(symbol, "1d")

    from database.crud import get_symbol_timeframe_config

    min_signal_value = get_symbol_timeframe_config(symbol, "1m").demark_buy

    if daily_side == "NONE" or daily_demark < min_signal_value:
        return

    if daily_side != side:
        error_msg = f"天级信号方向不一致: 天级={daily_side}, 当前={side}, 取消下单"
        logger.info(f"业务中断: {error_msg}")
        raise ValueError(error_msg)


def main() -> None:
    """测试天级信号方向检查功能"""
    if len(sys.argv) < 3:
        logger.info("用法: p daily_signal_checker.py SYMBOL SIDE")
        logger.info("示例: p daily_signal_checker.py ADAUSDC BUY")
        logger.info("      p daily_signal_checker.py ADAUSDC SELL")
        return

    symbol = sys.argv[1].upper()
    current_side = sys.argv[2].upper()

    if current_side not in ["BUY", "SELL"]:
        logger.error("❌ SIDE 参数必须是 BUY 或 SELL")
        return

    logger.info(f"🧪 测试天级信号方向检查: {symbol} {current_side}")

    # 按照CLAUDE.md fail-fast原则,让异常自然向上传播
    check_daily_signal_direction(symbol, cast(SideLiteral, current_side))
    logger.info("✅ 天级信号检查通过, 可以继续下单")


if __name__ == "__main__":
    main()
