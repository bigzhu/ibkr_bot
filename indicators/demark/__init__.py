"""DeMark指标模块

提供DeMark技术指标的纯技术计算功能.
专注于单一职责: DeMark指标计算,完全独立于外部依赖.

主要功能:
- DeMark指标核心计算
- TDUp/TDDn信号识别
- 命令行接口支持

用法:
from loguru import logger

    from demark import demark, demark_with_binance_api

    # 方式一: 纯技术函数 (推荐用于测试和复杂业务场景)
    klines_data = get_klines_data_from_api()  # 由调用方获取K线数据
    signal_type, signal_value, is_break, klines = demark(klines_data)

    # 方式二: 业务封装函数 (推荐用于简单业务场景)
    signal_type, signal_value, is_break, klines = demark_with_binance_api("ADAUSDC", "1m")

    if signal_type == "SELL":
        logger.info(f"卖出信号: {signal_value}")
    elif signal_type == "BUY":
        logger.info(f"买入信号: {signal_value}")
    else:
        logger.info("无信号")

    if is_break:
        logger.info("已确认反向突破")
"""

# 导入核心函数
from .binance_demark import demark_with_binance_api
from .demark import demark

__all__ = [
    "demark",  # 纯技术函数 - 推荐用于测试和复杂业务场景
    "demark_with_binance_api",  # 业务封装函数 - 推荐用于简单业务场景
]

__version__ = "3.0.0"  # 彻底重构版本
