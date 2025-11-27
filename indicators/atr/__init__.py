"""ATR (Average True Range) 指标模块

提供ATR指标计算功能, 用于衡量价格波动性
遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except
"""

from .atr import calculate_atr

__all__ = ["calculate_atr"]
