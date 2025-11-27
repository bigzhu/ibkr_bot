"""order_builder 独立运行主程序

直接运行订单构建流程, 支持 DeMark 信号检查和交易日志记录.
遵循 fail-fast 原则, 异常直接向上传播.

使用方法:
  uv run python -m order_builder SYMBOL TIMEFRAME
  uv run python -m order_builder ADAUSDC 15m
  uv run python -m order_builder ADAUSDC 1m
"""

import sys

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m order_builder` 运行 CLI, 无需手动修改 sys.path"
    )

# 导入并配置统一的日志系统
from shared.logger_utils import setup_scheduler_logger

_ = setup_scheduler_logger()  # order_builder 作为调度任务使用 scheduler 日志


from loguru import logger

from order_builder.app import run_order_builder

VALID_TIMEFRAMES = ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d", "1W", "1M"]

USAGE_MESSAGE = """order_builder - 订单构建主程序

使用方法:
  uv run python -m order_builder SYMBOL TIMEFRAME  # 运行订单构建流程
  uv run python -m order_builder ADAUSDC 15m      # 分析ADAUSDC 15分钟
  uv run python -m order_builder ADAUSDC 1m       # 分析ADAUSDC 1分钟

支持的时间周期: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 1d, 1W, 1M"""


def _show_usage() -> None:
    """输出使用说明"""
    logger.info(USAGE_MESSAGE)


def main() -> None:
    """主函数"""
    if len(sys.argv) < 3:
        _show_usage()
        return

    symbol = sys.argv[1].strip()
    timeframe = sys.argv[2].strip()

    # 验证用户输入
    if not symbol:
        logger.error("❌ 交易对符号不能为空")
        _show_usage()
        return
    if not timeframe:
        logger.error("❌ 时间周期不能为空")
        _show_usage()
        return

    # 验证时间周期格式
    if timeframe.lower() not in VALID_TIMEFRAMES:
        logger.error(f"❌ 时间周期无效, 支持: {', '.join(VALID_TIMEFRAMES)}")
        _show_usage()
        return

    symbol = symbol.upper()
    timeframe = timeframe.lower()

    logger.info(f"🚀 {symbol} {timeframe}")

    # 执行流程 - 异常直接向上传播
    _ = run_order_builder(symbol, timeframe)


if __name__ == "__main__":
    main()
