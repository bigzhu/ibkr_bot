"""
操作模式检查器 - 验证订单方向是否符合配置要求

功能:
1. 根据 symbol_timeframe_configs.oper_mode 检查订单方向是否允许
2. 支持 all/buy_only/sell_only 三种模式
3. 违规时抛出异常, 遵循 fail-fast 原则

用法:
    p oper_mode_checker.py ADAUSDC 15m BUY    # 检查是否允许BUY订单
"""

import sys

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m order_checker.oper_mode` 运行该模块, 无需手动修改 sys.path"
    )

from loguru import logger

from database.crud import get_symbol_timeframe_config
from database.models import OperMode
from shared.constants import BUY, SELL
from shared.typing import SideLiteral


def check_oper_mode_allows_side(symbol: str, timeframe: str, side: SideLiteral) -> None:
    """
    检查操作模式是否允许指定的订单方向

    Args:
        symbol: 交易对符号
        timeframe: 时间周期
        side: 订单方向 (BUY/SELL)

    Raises:
        ValueError: 当操作模式不允许该订单方向时抛出异常
    """
    config = get_symbol_timeframe_config(symbol, timeframe)
    oper_mode = config.oper_mode

    logger.debug(f"检查操作模式: {symbol}-{timeframe}, mode={oper_mode}, side={side}")

    # 检查操作模式限制
    if oper_mode == OperMode.ALL:
        # "all" 模式允许所有方向
        return
    elif oper_mode == OperMode.BUY_ONLY and side != BUY:
        # "buy_only" 模式只允许BUY
        raise ValueError(f"操作模式限制: {oper_mode} 不允许 {side} 订单")
    elif oper_mode == OperMode.SELL_ONLY and side != SELL:
        # "sell_only" 模式只允许SELL
        raise ValueError(f"操作模式限制: {oper_mode} 不允许 {side} 订单")

    logger.debug(f"✅ 操作模式检查通过: {oper_mode} 允许 {side}")


def show_usage() -> None:
    """显示使用方法"""
    logger.info("oper_mode_checker - 操作模式检查器")
    logger.info("\n使用方法:")
    logger.info("  p oper_mode_checker.py SYMBOL TIMEFRAME SIDE")
    logger.info("  p oper_mode_checker.py ADAUSDC 15m BUY")
    logger.info("  p oper_mode_checker.py ADAUSDC 1m SELL")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        if len(sys.argv) == 2 and sys.argv[1] in ["--help", "-h", "help"]:
            show_usage()
        else:
            logger.error("❌ 参数不足")
            show_usage()
        sys.exit(1)

    symbol = sys.argv[1].strip().upper()
    timeframe = sys.argv[2].strip().lower()
    side_str = sys.argv[3].strip().upper()

    if side_str not in ["BUY", "SELL"]:
        logger.error("❌ 订单方向必须是 BUY 或 SELL")
        show_usage()
        sys.exit(1)

    side = BUY if side_str == "BUY" else SELL

    try:
        check_oper_mode_allows_side(symbol, timeframe, side)
        logger.info(f"✅ 操作模式检查通过: {symbol}-{timeframe} 允许 {side} 订单")
    except Exception as e:
        logger.error(f"❌ 操作模式检查失败: {e}")
        sys.exit(1)
