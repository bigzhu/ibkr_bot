"""
精确数学计算工具
解决浮点数精度问题
"""

from decimal import Decimal, getcontext

from shared.typing import NumberLike

# 设置精度为28位(足够金融计算使用)
getcontext().prec = 28


def precise_subtract(a: NumberLike, b: NumberLike) -> float:
    """
    精确减法:a - b

    Args:
        a: 被减数(字符串或数字)
        b: 减数(字符串或数字)

    Returns:
        float: 精确结果
    """
    try:
        decimal_a = Decimal(str(a)) if a is not None else Decimal("0")
        decimal_b = Decimal(str(b)) if b is not None else Decimal("0")
        result = decimal_a - decimal_b
        return float(result)
    except (ValueError, TypeError):
        return 0.0


def calculate_net_profit(profit: NumberLike, commission: NumberLike) -> float:
    """
    计算净利润:profit - commission

    Args:
        profit: 总利润(字符串或数字)
        commission: 手续费(字符串或数字)

    Returns:
        float: 精确的净利润
    """
    return precise_subtract(profit, commission)
