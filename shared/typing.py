"""
共享类型别名

集中维护跨模块使用的类型别名,避免重复定义.
"""

from decimal import Decimal
from typing import Literal, TypeAlias

# 数字或可转数字类型
NumberLike: TypeAlias = str | int | float | Decimal | None

# 订单方向字面量
SideLiteral: TypeAlias = Literal["BUY", "SELL"]

# 时间周期字面量
TimeframeLiteral: TypeAlias = Literal[
    "1m",
    "5m",
    "15m",
    "30m",
    "1h",
    "4h",
    "1d",
    "1W",
    "1M",
]
