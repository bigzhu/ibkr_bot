"""
数字格式化工具模块

提供统一的数字格式化函数,用于日志输出的美化
遵循CLAUDE.md规范:简洁清晰的数字显示
"""

from decimal import ROUND_DOWN, Decimal, getcontext
from typing import cast

from loguru import logger

MAX_DECIMAL_PLACES = 8
_QUANTIZE_TARGET = Decimal(f"1.{'0' * MAX_DECIMAL_PLACES}")

# 确保上下文精度至少满足量化要求
context = getcontext()
if context.prec < 28:
    context.prec = 28


def format_decimal(value: Decimal | float | str) -> str:
    """
    格式化Decimal数字,去除小数点后多余的零

    Args:
        value: 要格式化的数字

    Returns:
        格式化后的字符串,去除多余的零

    Examples:
        0.78520000 -> "0.7852"
        54.50000000 -> "54.5"
        1.00000000 -> "1"
        0.00000000 -> "0"
    """
    if isinstance(value, str):
        dec: Decimal = Decimal(value)
    elif isinstance(value, float):
        dec = Decimal(str(value))
    else:
        dec = cast(Decimal, value)

    # 超过约定精度时统一量化,避免浮点残留
    exponent = dec.as_tuple().exponent
    if isinstance(exponent, int) and exponent < -MAX_DECIMAL_PLACES:
        dec = dec.quantize(_QUANTIZE_TARGET, rounding=ROUND_DOWN)

    # 规范化并使用定点格式,避免出现科学计数法(如 0E-8)
    dec = dec.normalize()
    formatted = format(dec, "f").rstrip("0").rstrip(".")

    # 归一化 0 的表现
    if formatted in {"", "-", "0", "-0"}:
        return "0"
    return formatted


def format_percentage(value: Decimal | float | int) -> str:
    """
    格式化百分比数字

    Args:
        value: 百分比值

    Returns:
        格式化后的百分比字符串

    Examples:
        0.522159959246052 -> "0.52%"
        1.40000000 -> "1.4%"
    """
    if isinstance(value, float | int):
        value = Decimal(str(value))

    # 保留2位小数,然后去除多余的零
    rounded = value.quantize(Decimal("0.01"))
    formatted = format_decimal(rounded)
    return f"{formatted}%"


if __name__ == "__main__":
    """测试数字格式化功能"""
    test_cases = [
        Decimal("0.78520000"),
        Decimal("54.50000000"),
        Decimal("1.00000000"),
        Decimal("0.00000000"),
        0.522159959246052,
        "1.40000000",
    ]

    logger.info("数字格式化测试:")
    for case in test_cases:
        formatted = format_decimal(case)
        logger.info(f"  {case} -> {formatted}")

    logger.info("\n百分比格式化测试:")
    percentage_cases = [0.522159959246052, 1.4, 0.0]
    for case in percentage_cases:
        formatted = format_percentage(case)
        logger.info(f"  {case} -> {formatted}")
