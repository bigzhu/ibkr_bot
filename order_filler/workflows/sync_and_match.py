"""
Binance订单同步和撮合一体化工作流程

整合同步和撮合操作,提供一键式解决方案.
遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except.
"""

import sys
from pathlib import Path

from loguru import logger

from shared.timing import time_block

if __name__ == "__main__":
    try:
        from shared.path_utils import ensure_project_root_for_script
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from shared.path_utils import ensure_project_root_for_script

    ensure_project_root_for_script(__file__)

from order_filler.matching import match_orders, proxy_match_other_timeframes
from order_filler.sync import sync_orders_for_pair


def sync_and_match_orders(pair: str, timeframe: str) -> None:
    """
    一键同步和撮合订单,1m时间周期支持代理撮合

    Args:
        pair: 交易对符号
        timeframe: 时间周期,用于获取配置信息
    """
    # 1. 同步订单(计时)
    with time_block("同步订单"):
        sync_orders_for_pair(pair)

    # 2. 撮合当前时间周期的订单(计时)
    with time_block("主撮合"):
        _ = match_orders(pair, timeframe)

    # 3. 只有1m时间周期时才执行代理撮合
    if timeframe == "1m":
        with time_block("代理撮合"):
            proxy_match_other_timeframes(pair)


def main() -> None:
    """一键同步和撮合命令行入口"""
    if len(sys.argv) < 3:
        logger.info("用法: p -m order_filler.workflows PAIR TIMEFRAME")
        logger.info("示例: p -m order_filler.workflows ADAUSDC 15m")
        return

    pair = sys.argv[1].upper()
    timeframe = sys.argv[2]

    logger.info(f"🚀 Binance一键同步和撮合 - {pair} {timeframe}")
    logger.info("=" * 50)

    # 执行一键操作
    sync_and_match_orders(pair, timeframe)

    logger.info("✅ 同步和撮合操作完成")


if __name__ == "__main__":
    main()
