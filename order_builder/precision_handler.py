"""数值精度处理模块

处理交易所对数量和价格的精度要求, 避免 float 精度问题.
根据 trading_symbols 表中的字段进行精确的数值调整.
遵循 fail-fast 原则, 异常直接向上传播.
"""

from decimal import ROUND_DOWN, Decimal

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m order_builder.precision_handler` 运行该模块, 无需手动修改 sys.path"
    )

from loguru import logger

from database.models import TradingSymbol


def adjust_quantity_precision(quantity: Decimal, step_size: Decimal) -> Decimal:
    """调整数量精度 (仅精度调整, 不检查限制)

    Args:
        quantity: 原始数量
        step_size: 数量步长

    Returns:
        Decimal: 调整后的数量

    Raises:
        ValueError: 步长参数无效时抛出异常
    """
    if step_size <= 0:
        raise ValueError(f"数量步长必须大于0: {step_size}")

    # 根据步长调整数量 (向下取整到最接近的有效值)
    adjusted_qty = (quantity // step_size) * step_size

    return adjusted_qty


def adjust_price_precision(price: Decimal, tick_size: Decimal) -> Decimal:
    """调整价格精度 (仅精度调整, 不检查限制)

    Args:
        price: 原始价格
        tick_size: 价格步长

    Returns:
        Decimal: 调整后的价格

    Raises:
        ValueError: 步长参数无效时抛出异常
    """
    if tick_size <= 0:
        raise ValueError(f"价格步长必须大于0: {tick_size}")

    # 根据步长调整价格 (四舍五入到最接近的有效值)
    adjusted_price = (price / tick_size).quantize(
        Decimal("1"), rounding=ROUND_DOWN
    ) * tick_size

    return adjusted_price


def adjust_order_precision(
    quantity: Decimal, price: Decimal, symbol_info: TradingSymbol
) -> tuple[Decimal, Decimal]:
    """调整订单数值精度

    根据交易对的精度要求调整数量和价格, 确保符合交易所的数量和价格规范.

    Args:
        symbol: 交易对符号
        quantity: 原始数量
        price: 原始价格
        symbol_info: 交易对信息,避免重复查询

    Returns:
        tuple[Decimal, Decimal ]: (调整后数量, 调整后价格 )

    Raises:
        ValueError: 交易对不存在或数量价格超出限制时抛出异常
    """

    # 转换为 Decimal 类型进行精确计算
    step_size = Decimal(str(symbol_info.step_size))
    tick_size = Decimal(str(symbol_info.tick_size))

    # 调整价格和数量精度
    adjusted_price = adjust_price_precision(price, tick_size)
    adjusted_quantity = adjust_quantity_precision(quantity, step_size)

    return adjusted_quantity, adjusted_price


def validate_order_limits(
    symbol: str,
    quantity: Decimal,
    price: Decimal,
    symbol_info: TradingSymbol,
    min_notional: Decimal,
) -> None:
    """验证订单是否满足所有交易所限制 (用于下单前检查)

    检查数量限制,价格限制和名义价值限制.

    Args:
        symbol: 交易对符号
        quantity: 订单数量
        price: 订单价格
        symbol_info: 交易对信息,避免重复查询
        min_notional: 最小名义价值,避免重复查询

    Raises:
        ValueError: 任何限制不满足时抛出异常
    """
    logger.info(f"🔍 检查 {symbol} 订单限制: 数量={quantity}, 价格={price}")

    # 转换限制参数
    min_qty = Decimal(str(symbol_info.min_qty))
    max_qty = (
        Decimal(str(symbol_info.max_qty))
        if symbol_info.max_qty > 0
        else Decimal("999999999")
    )
    min_price = Decimal(str(symbol_info.min_price))
    max_price = (
        Decimal(str(symbol_info.max_price))
        if symbol_info.max_price > 0
        else Decimal("999999999")
    )
    # 使用传入的最小名义价值限制

    logger.debug(
        f"📊 限制参数 - 数量:[{min_qty}, {max_qty}], 价格:[{min_price}, {max_price}], 名义价值:{min_notional}"
    )

    # 检查数量限制
    if quantity < min_qty:
        raise ValueError(f"数量 {quantity} 低于最小限制 {min_qty}")
    if quantity > max_qty:
        raise ValueError(f"数量 {quantity} 超过最大限制 {max_qty}")

    # 检查价格限制
    if price < min_price:
        raise ValueError(f"价格 {price} 低于最小限制 {min_price}")
    if price > max_price:
        raise ValueError(f"价格 {price} 超过最大限制 {max_price}")

    # 检查名义价值限制
    actual_notional = quantity * price
    if actual_notional < min_notional:
        raise ValueError(
            f"名义价值 {actual_notional} 低于最小限制 {min_notional} (数量:{quantity} x 价格:{price})"
        )

    logger.info(
        f"✅ 所有限制检查通过 - 数量:{quantity}, 价格:{price}, 名义价值:{actual_notional}"
    )


def main() -> None:
    """测试数值精度处理功能"""
    import sys

    try:
        symbol, quantity, price = _parse_cli_args(sys.argv)
    except ValueError as exc:
        logger.error(exc)
        _print_usage()
        return

    try:
        from database.crud import get_symbol_info as _get_symbol_info

        symbol_info = _get_symbol_info(symbol)
        min_notional = Decimal(symbol_info.min_notional)

        adjusted_quantity, adjusted_price = adjust_order_precision(
            quantity, price, symbol_info
        )
        _display_precision_result(
            symbol,
            quantity,
            price,
            adjusted_quantity,
            adjusted_price,
        )
        logger.info("\n🔍 限制检查:")
        validate_order_limits(
            symbol, adjusted_quantity, adjusted_price, symbol_info, min_notional
        )
        logger.info("✅ 所有检查通过")

    except Exception as exc:
        logger.error(f"❌ 处理失败: {exc}")


if __name__ == "__main__":
    main()


def _parse_cli_args(argv: list[str]) -> tuple[str, Decimal, Decimal]:
    """Parse CLI arguments and convert numeric values to Decimal."""
    if len(argv) < 4:
        raise ValueError("参数不足")
    try:
        symbol = argv[1].upper()
        quantity = Decimal(argv[2])
        price = Decimal(argv[3])
        return symbol, quantity, price
    except (ValueError, ArithmeticError) as exc:
        raise ValueError(f"参数格式错误: {exc}") from exc


def _display_precision_result(
    symbol: str,
    quantity: Decimal,
    price: Decimal,
    adjusted_quantity: Decimal,
    adjusted_price: Decimal,
) -> None:
    """Log the before/after values for a precision adjustment demo."""
    logger.info("\n🎯 精度调整结果:")
    logger.info(f"  交易对: {symbol}")
    logger.info(f"  原始数量: {quantity}")
    logger.info(f"  调整数量: {adjusted_quantity}")
    logger.info(f"  原始价格: {price}")
    logger.info(f"  调整价格: {adjusted_price}")


def _print_usage() -> None:
    logger.info("用法:")
    logger.info("  p precision_handler.py SYMBOL QUANTITY PRICE")
    logger.info("  示例: p precision_handler.py ADAUSDC 0.001234 65432.789")
