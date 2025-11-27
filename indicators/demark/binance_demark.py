"""DeMark指标业务封装模块

提供包含币安API调用的业务封装函数,方便外部直接调用.
封装层负责数据获取,技术层负责指标计算,职责分离清晰.
遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except
"""

import sys

from loguru import logger

if __name__ == "__main__":
    try:
        from shared.path_utils import ensure_project_root_for_script
    except ImportError:
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from shared.path_utils import ensure_project_root_for_script

    ensure_project_root_for_script(__file__)

from binance_api.common import get_configured_client
from binance_api.get_klines import klines
from shared.constants import DEMARK_USE_CLOSE_PRICE_COMPARISON
from shared.types import Kline

# 根据配置选择实现方式
if DEMARK_USE_CLOSE_PRICE_COMPARISON:
    from indicators.demark.demark_traditional import demark
else:
    from indicators.demark.demark import demark


def demark_with_binance_api(
    symbol: str, timeframe: str, is_all: bool = False
) -> tuple[str, int, bool, list[Kline]]:
    """通过币安API获取数据并计算DeMark信号 - 业务封装函数

    这是业务封装函数,负责API调用和数据获取,然后调用纯技术函数计算指标.
    适合需要直接从币安获取数据的业务场景.

    使用的计算方式由 DEMARK_USE_CLOSE_PRICE_COMPARISON 常量决定:
    - True (传统方式): 基于收盘价严格比较,符合行业标准,噪声低
    - False (当前方式): 基于高低价比较,信号更快但噪声较高

    Args:
        symbol: 交易对符号,如 "ADAUSDC"
        timeframe: 时间周期格式,如 "1m", "5m", "1h", "1d"
        is_all: 是否包含未完成的K线,默认False(排除最新的未完成K线)

    Returns:
        tuple[str, int, bool, list[dict]]: (操作类型, 信号值, 是否反向突破, 序列K线)
        - 操作类型: "SELL" | "BUY" | "NONE"
        - 信号值: DeMark 计数值, 无有效信号时返回 0
        - 是否反向突破: 满足 close 突破上一根相反边界时为 True
        - 序列K线: 当前 DeMark 序列的 K 线数据

    Raises:
        ValueError: 当API配置或数据有问题时抛出异常
    """

    # 获取币安API客户端
    client = get_configured_client()

    # 获取K线数据(50根: 34根必要 + 16根冗余,支持完整Countdown分析)
    # Countdown算法需要: 9根Setup + 13根Countdown + 12根边界安全 = 34根最少
    binance_klines_data = klines(client, symbol, timeframe, 50)

    # 排除最新的未完成K线
    completed_klines = binance_klines_data if is_all else binance_klines_data[:-1]

    # 调用纯技术函数进行计算
    side, signal_value, is_break, sequence_klines = demark(completed_klines)

    return side, signal_value, is_break, sequence_klines


if __name__ == "__main__":
    """测试业务封装函数"""
    if len(sys.argv) >= 3:
        symbol = sys.argv[1].upper()
        timeframe = sys.argv[2].lower()

        signal_type, signal_value, is_break, sequence_klines = demark_with_binance_api(
            symbol, timeframe
        )
        logger.info(f"{signal_type} {signal_value} (break={is_break})")
    else:
        logger.info("DeMark指标业务封装模块")
        logger.info("=" * 40)
        logger.info("")
        logger.info("📋 功能说明:")
        logger.info("  - 业务封装函数,包含币安API调用")
        logger.info("  - 输入: 交易对符号和时间周期")
        logger.info("  - 输出: DeMark信号类型和值")
        logger.info("")
        logger.info("💡 使用方法:")
        logger.info("  from demark.binance_demark import demark_with_binance_api")
        logger.info(
            "  signal_type, signal_value, is_break, klines = demark_with_binance_api('ADAUSDC', '1m')"
        )
        logger.info("")
        logger.info("🔧 技术特点:")
        logger.info("  - 自动处理API调用和数据获取")
        logger.info("  - 调用纯技术函数进行计算")
        logger.info("  - 业务逻辑和技术逻辑分离")
        logger.info("")
        logger.info("🧪 测试用法:")
        logger.info("  p binance_demark.py SYMBOL TIMEFRAME")
        logger.info("  p binance_demark.py ADAUSDC 1m")
