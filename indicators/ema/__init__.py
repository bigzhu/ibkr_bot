"""EMA (Exponential Moving Average) 指标模块

提供EMA指标的计算与命令行入口封装.
遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except
"""

from .ema import calculate_ema

__all__ = ["calculate_ema"]
