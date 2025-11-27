"""
DeMark指标计算 - 命令行接口

用途: 获取币安数据并计算 DeMark 指标

说明:
    DeMark模块包含两部分:
    1. 纯技术指标计算函数 (demark.demark)
    2. 业务封装函数 (demark.binance_demark)

    命令行接口支持直接调用业务封装函数,方便快速查看指标结果.
"""

import sys
from pathlib import Path

# 统一双重用途模块导入处理(仅处理 ImportError)
try:
    from shared.path_utils import add_project_root_to_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from shared.path_utils import add_project_root_to_path

add_project_root_to_path()

from loguru import logger

from indicators.demark.binance_demark import demark_with_binance_api


def _show_help() -> None:
    """显示帮助信息"""
    logger.info("DeMark技术指标计算模块")
    logger.info("=" * 40)
    logger.info("")
    logger.info("支持两种使用方式:")
    logger.info("")
    logger.info("1. 命令行直接调用 (包含币安API)")
    logger.info("")
    logger.info("2. 代码中导入使用:")
    logger.info("   纯技术计算: from indicators.demark import demark")
    logger.info(
        "   带API调用: from indicators.demark.binance_demark import demark_with_binance_api"
    )
    logger.info("")
    logger.info("输入格式:")
    logger.info("  SYMBOL: 交易对符号 (如 BTCUSDC, ARBUSDC)")
    logger.info("  TIMEFRAME: 时间周期 (如 1m, 5m, 1h, 1d)")
    logger.info("")
    logger.info("输出格式:")
    logger.info("  BUY/SELL/NONE 信号值")
    logger.info("  例如: BUY 9, SELL 8, NONE 0")


def main() -> None:
    """命令行主入口"""
    # 处理帮助参数
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        _show_help()
        return

    # 处理 SYMBOL TIMEFRAME 参数 - 直接执行功能
    if len(sys.argv) >= 3:
        symbol = sys.argv[1].upper()
        timeframe = sys.argv[2].lower()

        # 禁用日志输出,只显示结果
        from loguru import logger

        signal_type, signal_value, is_break, _ = demark_with_binance_api(
            symbol, timeframe
        )
        logger.info(f"{signal_type} {signal_value} (break={is_break})")
        return

    # 无参数时显示帮助信息
    _show_help()


if __name__ == "__main__":
    main()
