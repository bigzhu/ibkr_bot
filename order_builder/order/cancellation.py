"""订单取消模块 - 专注于订单取消功能

实现订单取消,批量取消等服务功能
"""

import sys
from collections.abc import Callable, Sequence
from typing import Any

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m order_builder.order.cancellation` 运行该模块, 无需手动修改 sys.path"
    )

from loguru import logger

from binance_api.cancel_order import cancel_order
from binance_api.get_open_orders import get_open_orders
from database.order_models import BinanceOpenOrder
from order_builder.models import CancelOperationResult, CancelOrderResult
from shared.timeframe_utils import is_timeframe_match


def cancel_all_open_orders_except(
    symbol: str, except_order_id: str | None = None, timeframe_filter: str | None = None
) -> dict[str, Any]:
    """取消除指定订单外的所有未成交挂单

    当挂单完成后, 取消除了当前交易对及时间周期之外, 并非当前挂单之外的订单

    Args:
        symbol: 交易对符号
        except_order_id: 要排除的订单ID, 该订单不会被取消
        timeframe_filter: 可选的时间维度过滤器, 只取消匹配此clientOrderId的订单

    Returns:
        dict: 操作结果
    """

    open_orders = get_open_orders(symbol)
    if not open_orders:
        return CancelOperationResult(
            success=True, message=f"交易对 {symbol} 没有未成交订单"
        ).model_dump()

    filtered_orders = _apply_filters(open_orders, timeframe_filter, except_order_id)
    if not filtered_orders:
        return CancelOperationResult(
            success=True, message="没有需要取消的订单"
        ).model_dump()

    cancelled_orders, failed_count = execute_batch_cancel(symbol, filtered_orders)
    return _create_cancel_result(cancelled_orders, failed_count, len(filtered_orders))


def _apply_filters(
    open_orders: Sequence[BinanceOpenOrder],
    timeframe_filter: str | None,
    except_order_id: str | None,
) -> Sequence[BinanceOpenOrder]:
    """应用过滤器对订单进行筛选"""
    filtered_orders = open_orders

    # 应用时间周期过滤器
    if timeframe_filter:
        filtered_orders = [
            order
            for order in filtered_orders
            if is_timeframe_match(order.client_order_id, timeframe_filter)
        ]
        logger.debug(f"Timeframe filtered orders: {len(filtered_orders)}")

    # 排除指定订单
    if except_order_id:
        except_order_id_int = int(except_order_id)
        filtered_orders = [
            order for order in filtered_orders if order.order_id != except_order_id_int
        ]
        logger.debug(f"Excluded orderId filtered orders: {len(filtered_orders)}")

    return filtered_orders


def execute_batch_cancel(
    symbol: str, filtered_orders: Sequence[BinanceOpenOrder]
) -> tuple[list[CancelOrderResult], int]:
    """执行批量取消操作"""
    cancelled_orders: list[CancelOrderResult] = []
    failed_count = 0

    for order in filtered_orders:
        order_id = order.order_id
        if not order_id:
            logger.warning(f"⚠️ 订单缺少ID信息: {order}")
            failed_count += 1
            continue

        logger.debug(f"🗑️ 正在取消订单: {order_id}")
        _ = cancel_order(symbol, int(order_id))

        cancel_record = CancelOrderResult(
            order_id=str(order_id),
            client_order_id=order.client_order_id,
            side=order.side,
            quantity=order.orig_qty,
            symbol=symbol,
        )
        cancelled_orders.append(cancel_record)
        logger.debug(f"Cancelled order: {order_id}")

    return cancelled_orders, failed_count


def _create_cancel_result(
    cancelled_orders: list[CancelOrderResult],
    failed_count: int,
    total_orders: int,
) -> dict[str, Any]:
    """创建取消操作结果"""
    cancelled_count = len(cancelled_orders)

    result = CancelOperationResult(
        success=True,
        cancelled_count=cancelled_count,
        failed_count=failed_count,
        total_orders=total_orders,
        cancelled_orders=cancelled_orders,
        message=f"成功取消 {cancelled_count} 个订单, 失败 {failed_count} 个",
    )

    return result.model_dump()


def show_usage() -> None:
    """显示使用帮助"""
    logger.info("订单取消处理器")
    logger.info("")
    logger.info("用法:")
    logger.info("  p -m order_builder.order.cancellation cancel_all SYMBOL")
    logger.info("  p -m order_builder.order.cancellation cancel_except SYMBOL ORDER_ID")
    logger.info(
        "  p -m order_builder.order.cancellation cancel_timeframe SYMBOL TIMEFRAME"
    )
    logger.info(
        "  p -m order_builder.order.cancellation cancel_except_timeframe SYMBOL ORDER_ID TIMEFRAME"
    )
    logger.info("")
    logger.info("示例:")
    logger.info("  p -m order_builder.order.cancellation cancel_all ADAUSDC")
    logger.info("  p -m order_builder.order.cancellation cancel_except ADAUSDC 12345")
    logger.info("  p -m order_builder.order.cancellation cancel_timeframe ADAUSDC 15m")


def main() -> None:
    """演示订单取消功能"""
    try:
        command, symbol, extras = _parse_cli_args(sys.argv)
        result = _execute_command(command, symbol, extras)
    except ValueError as exc:
        logger.error(exc)
        show_usage()
        return

    from shared.output_utils import print_json

    print_json(result)


if __name__ == "__main__":
    main()


Handler = Callable[[str, list[str]], dict[str, Any]]


def _parse_cli_args(argv: list[str]) -> tuple[str, str, list[str]]:
    """Validate CLI arguments and return command, symbol and additional args."""
    if len(argv) < 3:
        raise ValueError("参数不足")
    command = argv[1].lower().strip()
    symbol = argv[2].upper()
    extras = list(argv[3:])
    return command, symbol, extras


def _execute_command(command: str, symbol: str, extras: list[str]) -> dict[str, Any]:
    """Execute CLI command using registered handlers."""
    handler = _command_handlers().get(command)
    if handler is None:
        raise ValueError("❌ 无效的命令或参数")
    return handler(symbol, extras)


def _command_handlers() -> dict[str, Handler]:
    """Return the mapping of supported CLI commands to handlers."""
    return {
        "cancel_all": _handle_cancel_all,
        "cancel_except": _handle_cancel_except,
        "cancel_timeframe": _handle_cancel_timeframe,
        "cancel_except_timeframe": _handle_cancel_except_timeframe,
    }


def _handle_cancel_all(symbol: str, extras: list[str]) -> dict[str, Any]:
    """Cancel all open orders for a symbol."""
    if extras:
        raise ValueError("cancel_all 不需要额外参数")
    return cancel_all_open_orders_except(symbol)


def _handle_cancel_except(symbol: str, extras: list[str]) -> dict[str, Any]:
    """Cancel all orders except the given order id."""
    if len(extras) < 1:
        raise ValueError("cancel_except 需要提供 ORDER_ID")
    return cancel_all_open_orders_except(symbol, extras[0])


def _handle_cancel_timeframe(symbol: str, extras: list[str]) -> dict[str, Any]:
    """Cancel orders filtered by timeframe."""
    if len(extras) < 1:
        raise ValueError("cancel_timeframe 需要提供 TIMEFRAME")
    return cancel_all_open_orders_except(symbol, timeframe_filter=extras[0])


def _handle_cancel_except_timeframe(symbol: str, extras: list[str]) -> dict[str, Any]:
    """Cancel orders excluding a specific ID and filtered by timeframe."""
    if len(extras) < 2:
        raise ValueError("cancel_except_timeframe 需要提供 ORDER_ID 和 TIMEFRAME")
    return cancel_all_open_orders_except(symbol, extras[0], extras[1])
