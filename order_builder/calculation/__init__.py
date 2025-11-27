"""计算模块 - 订单量价计算相关功能

专注于基于 DeMark 信号的订单数量和价格计算.
提供纯计算接口: calculate_qty() - 无副作用,专注计算逻辑.
"""

from order_builder.calculation.core import calculate_qty

__all__ = ["calculate_qty"]
