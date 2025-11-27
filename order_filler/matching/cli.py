"""
Binance订单撮合功能模块 - 主入口

处理BUY/SELL订单的撮合逻辑,确保交易闭环准确计算
遵循CLAUDE.md规范:fail-fast原则,类型注解,禁用try-except,纯函数优先

撮合规则:
1. 按订单完成时间(time)排序处理
2. BUY订单放入买单池
3. SELL订单与买单池中最便宜的BUY订单撮合
4. 相互冲抵unmatched_qty,冲抵为0时立即更新数据库

1m代理撮合规则:
1. 1m时间周期负责代理其他时间周期的撮合
2. 距离下次触发≥2分钟时执行代理撮合
3. 自动发现需要代理撮合的时间周期
"""

if __name__ == "__main__":
    try:
        from shared.path_utils import ensure_project_root_for_script
    except ImportError:
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from shared.path_utils import ensure_project_root_for_script

    ensure_project_root_for_script(__file__)

# 导入并配置统一的日志系统
from shared.logger_utils import setup_scheduler_logger

setup_scheduler_logger()  # order_filler作为调度任务使用scheduler日志

from loguru import logger

# 导入拆分后的模块
from order_filler.matching.engine import match_orders
from order_filler.matching.proxy import proxy_match_other_timeframes


def main() -> None:
    """测试订单撮合功能"""
    import sys

    if len(sys.argv) < 3:
        logger.info("用法: p matching/cli.py PAIR TIMEFRAME")
        logger.info("示例: p matching/cli.py ADAUSDC 15m")
        return

    pair = sys.argv[1].upper()
    timeframe = sys.argv[2]

    logger.info(f"🔄 Binance订单撮合测试 - {pair} {timeframe}")
    logger.info("=" * 50)

    # 执行主撮合
    main_stats = match_orders(pair, timeframe)

    # 执行代理撮合(仅1m时间周期)
    if timeframe == "1m":
        proxy_match_other_timeframes(pair)

    # 显示主撮合结果
    logger.info("✅ 撮合完成!")
    logger.info(f"交易对: {main_stats.symbol}")
    logger.info(f"处理订单数: {main_stats.processed_orders}")
    logger.info(f"撮合交易数: {main_stats.matched_transactions}")
    logger.info(f"买单池大小: {main_stats.buy_orders_pooled}")
    logger.info(f"剩余买单: {main_stats.remaining_buy_orders}")


if __name__ == "__main__":
    main()
