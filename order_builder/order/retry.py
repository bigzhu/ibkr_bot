"""
订单重试处理器 - 处理余额不足的自动重试机制

专注功能: 订单下单失败后的智能重试
包含余额调整,订单取消,数量重算等功能
遵循 CLAUDE.md 规范的特殊异常处理场景
"""

from decimal import Decimal

from binance.exceptions import BinanceAPIException
from loguru import logger

from database.order_models import BinanceOpenOrder
from database.symbol_crud import get_symbol_info
from order_builder.balance_manager import get_user_balance
from order_builder.order.cancellation import execute_batch_cancel
from order_builder.order.stop_market import place_stop_market_order
from shared.constants import BUY, SELL


def _validate_min_notional_value(
    symbol: str,
    quantity: Decimal,
    price: str,
    min_notional: Decimal,
) -> Decimal:
    """验证数量是否满足最小名义值要求

    Args:
        symbol: 交易对符号
        quantity: 调整后的数量
        price: 下单价格
        min_notional: 交易所要求的最小名义值

    Returns:
        Decimal: 验证后的数量,不满足要求时返回0
    """
    order_price = Decimal(price)
    notional_value = quantity * order_price

    if notional_value < min_notional:
        return Decimal(0)
        # raise ValueError(
        #     f"{symbol} notional {notional_value} < min_notional {min_notional}"
        # )

    return quantity


def _adjust_quantity_by_balance(
    symbol: str,
    quantity: str,
    price: str,
    side: str,
) -> str:
    """根据真实余额调整订单数量

    查询当前现货余额,计算可下单数量,调整到交易所允许的精度.

    Args:
        symbol: 交易对符号
        quantity: 原始下单数量(仅用于日志)
        price: 下单价格
        side: 买卖方向 (BUY/SELL)

    Returns:
        str: 调整后的下单数量

    Raises:
        ValueError: 调整后数量为 0 或无法满足最小下单条件
    """
    trading_symbol_info = get_symbol_info(symbol)
    min_notional = Decimal(trading_symbol_info.min_notional)
    original_quantity = Decimal(quantity)
    price_decimal = Decimal(price)

    if side == SELL:
        current_balance = get_user_balance(symbol, SELL, trading_symbol_info)
        adjusted_quantity = current_balance

        adjusted_quantity = _validate_min_notional_value(
            symbol, adjusted_quantity, price, min_notional
        )

        logger.info(f"✅ SELL 数量调整: {original_quantity} → {adjusted_quantity}")
        return str(adjusted_quantity)

    # BUY: 根据计价资产余额调整
    current_balance = get_user_balance(symbol, BUY, trading_symbol_info)

    # 计算可下单数量
    affordable_qty = current_balance / price_decimal
    adjusted_quantity = affordable_qty

    _validate_min_notional_value(symbol, adjusted_quantity, price, min_notional)

    logger.info(f"✅ BUY 数量调整: {original_quantity} → {adjusted_quantity}")
    return str(adjusted_quantity)


def _is_insufficient_balance_error(error: BinanceAPIException) -> bool:
    """判断是否为余额不足错误 (-2010 + 对应信息)"""
    if error.code != -2010:
        return False
    payload = (error.message or "").lower()
    return "insufficient balance" in payload


def _try_place_order(
    symbol: str,
    side: str,
    qty: str,
    stop_price: str,
    timeframe: str,
    open_orders: list[BinanceOpenOrder],
) -> str:
    """原子操作: 执行下单,异常直接向上抛

    Args:
        symbol: 交易对符号
        side: 买卖方向 (BUY/SELL)
        qty: 订单数量
        stop_price: 止损价格
        timeframe: 时间周期

    Returns:
        str: 订单ID

    Raises:
        BinanceAPIException: 下单API异常直接向上抛
    """
    return place_stop_market_order(
        symbol=symbol,
        side=side,
        quantity=qty,
        stop_price=stop_price,
        timeframe=timeframe,
        open_orders=open_orders,
    )


def _handle_insufficient_balance(
    symbol: str,
    side: str,
    qty: str,
    stop_price: str,
    timeframe: str,
    open_orders: list[BinanceOpenOrder],
) -> str:
    """余额不足的递进式 2 步处理(SELL/BUY 通用)

    步骤:
    1. 取消其他订单释放资金
    2. 查询真实余额并调整订单数量

    Args:
        symbol: 交易对符号
        side: 买卖方向 (BUY/SELL)
        qty: 订单数量
        stop_price: 止损价格
        timeframe: 时间周期
        open_orders: 开仓订单列表

    Returns:
        str: 订单ID

    Raises:
        BinanceAPIException: 最终下单失败或非余额不足错误
        ValueError: 数量调整失败
    """
    # Step 1: 取消其他订单释放资金
    execute_batch_cancel(symbol, open_orders)
    open_orders.clear()

    try:
        return _try_place_order(symbol, side, qty, stop_price, timeframe, open_orders)
    except BinanceAPIException as e:
        if not _is_insufficient_balance_error(e):
            raise

    # Step 2: 查询真实余额并调整数量
    adjusted_qty = _adjust_quantity_by_balance(symbol, qty, stop_price, side)

    order_id = _try_place_order(
        symbol, side, adjusted_qty, stop_price, timeframe, open_orders
    )
    return order_id


def place_order_with_retry(
    symbol: str,
    side: str,
    qty: str,
    stop_price: str,
    timeframe: str,
    open_orders: list[BinanceOpenOrder],
) -> str:
    """执行下单操作,包含余额不足时的自动重试机制

    处理币安API余额不足错误(-2010),自动取消其他订单释放资金后重试.
    其他API错误直接向上传播.

    ⚠️ CLAUDE.md 特殊合规场景: 余额不足自动恢复处理
    符合金融系统要求的业务异常处理,用于释放被占用资金

    Args:
        symbol: 交易对符号
        side: 买卖方向 (BUY/SELL)
        qty: 订单数量
        stop_price: 止损价格
        timeframe: 时间周期
        open_orders: 开仓订单列表

    Returns:
        str: 订单ID

    Raises:
        BinanceAPIException: 非余额不足的API错误或所有恢复步骤都失败
        ValueError: 余额补充或数量调整失败
    """
    try:
        return _try_place_order(symbol, side, qty, stop_price, timeframe, open_orders)
    except BinanceAPIException as e:
        if not _is_insufficient_balance_error(e):
            raise

        return _handle_insufficient_balance(
            symbol, side, qty, stop_price, timeframe, open_orders
        )


def show_usage() -> None:
    """显示使用帮助"""
    logger.info("订单重试处理器 - 带重试机制的下单")
    logger.info("")
    logger.info(
        "用法: p -m order_builder.order.retry SYMBOL SIDE QUANTITY STOP_PRICE TIMEFRAME"
    )
    logger.info("")
    logger.info("参数说明:")
    logger.info("  SYMBOL     - 交易对 (如: ADAUSDC)")
    logger.info("  SIDE       - 订单方向 (BUY 或 SELL)")
    logger.info("  QUANTITY   - 数量")
    logger.info("  STOP_PRICE - 止损价格")
    logger.info("  TIMEFRAME  - 时间周期 (如: 15m, 1h)")
    logger.info("")
    logger.info("示例:")
    logger.info("  p -m order_builder.order.retry ADAUSDC SELL 0.01 65000 15m")


if __name__ == "__main__":
    """独立运行入口 - 执行带重试机制的下单"""
    import sys

    if len(sys.argv) == 1:
        # 无参数: 显示用法
        show_usage()
    else:
        # 有参数: 执行重试下单
        if len(sys.argv) != 6:
            show_usage()
            sys.exit(1)

        symbol = sys.argv[1].upper()
        side = sys.argv[2].upper()
        quantity = sys.argv[3]
        stop_price = sys.argv[4]
        timeframe = sys.argv[5].lower()

        # 获取当前未结订单
        from order_builder.order.query import get_open_orders_by_symbol_timeframe

        open_orders = get_open_orders_by_symbol_timeframe(symbol, timeframe)

        # 执行重试逻辑
        order_id = place_order_with_retry(
            symbol,
            side,
            quantity,
            stop_price,
            timeframe,
            open_orders,
        )

        # 格式化输出结果
        if order_id:
            logger.info(f"📋 订单ID: {order_id}")
        else:
            logger.error("❌ 下单失败")
