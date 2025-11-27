"""Binance 取消订单功能 - 纯函数实现."""

from collections.abc import Callable, Sequence
from typing import Any, cast

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m ibkr_api.cancel_order` 运行该模块, 无需手动修改 sys.path"
    )

from loguru import logger


def cancel_order(symbol: str, order_id: int) -> dict[str, Any]:
    """取消订单

    Args:
        symbol: 交易对
        order_id: 订单ID

    Returns:
        dict: 取消订单响应信息
    """
    from ibkr_api.common import get_configured_client

    client = get_configured_client()

    logger.debug(f"❌ 取消订单: {symbol} ID:{order_id}")
    return client.cancel_order(symbol=symbol.upper(), orderId=order_id)


def cancel_order_by_client_id(symbol: str, client_order_id: str) -> dict[str, Any]:
    """通过客户端订单ID取消订单

    Args:
        symbol: 交易对
        client_order_id: 客户端订单ID

    Returns:
        dict: 取消订单响应信息
    """
    from ibkr_api.common import get_configured_client

    client = get_configured_client()

    logger.debug(f"❌ 取消订单(客户端ID): {symbol} ClientID:{client_order_id}")
    return client.cancel_order(symbol=symbol.upper(), origClientOrderId=client_order_id)


def cancel_all_orders(symbol: str) -> dict[str, Any]:
    """取消指定交易对的所有订单

    Args:
        symbol: 交易对

    Returns:
        list: 取消订单响应信息列表
    """
    from ibkr_api.common import get_configured_client

    client = get_configured_client()

    logger.warning(f"⚠️ 取消所有订单: {symbol}")
    return client.cancel_all_open_orders(symbol=symbol.upper())


def get_order_status(symbol: str, order_id: int) -> dict[str, Any]:
    """查询订单状态

    Args:
        symbol: 交易对
        order_id: 订单ID

    Returns:
        dict: 订单状态信息
    """
    from ibkr_api.common import get_configured_client

    client = get_configured_client()

    logger.debug(f"🔍 查询订单状态: {symbol} ID:{order_id}")
    return client.get_order(symbol=symbol.upper(), orderId=order_id)


def format_cancel_response(cancel_data: dict[str, Any]) -> dict[str, Any]:
    """格式化取消订单响应信息"""
    return {
        "orderId": cancel_data.get("orderId"),
        "symbol": cancel_data.get("symbol"),
        "side": cancel_data.get("side"),
        "type": cancel_data.get("type"),
        "status": cancel_data.get("status"),
        "quantity": cancel_data.get("origQty"),
        "price": cancel_data.get("price"),
        "client_order_id": cancel_data.get("origClientOrderId"),
        "time": cancel_data.get("transactTime"),
    }


def main() -> None:
    """演示取消订单功能"""
    import sys

    try:
        command, args = _parse_cli_args(sys.argv)
        _command_handlers()[command](args)
    except ValueError as exc:
        logger.error(exc)
        _print_usage()
    except KeyError:
        logger.error("❌ 无效的命令或参数")
        _print_usage()


if __name__ == "__main__":
    main()


Handler = Callable[[Sequence[str]], None]


def _parse_cli_args(argv: list[str]) -> tuple[str, list[str]]:
    if len(argv) < 2:
        raise ValueError("参数不足")
    command = argv[1].lower().strip()
    extras = argv[2:]
    return command, extras


def _command_handlers() -> dict[str, Handler]:
    return {
        "cancel": _handle_cancel,
        "cancel_client": _handle_cancel_client,
        "cancel_all": _handle_cancel_all,
        "status": _handle_status,
    }


def _handle_cancel(args: Sequence[str]) -> None:
    if len(args) < 2:
        raise ValueError("cancel 需要提供 SYMBOL 和 ORDER_ID")
    symbol, order_id_str = args[0], args[1]
    order_id = int(order_id_str)
    from shared.output_utils import print_json

    logger.warning(f"⚠️ 即将取消订单: {symbol} ID:{order_id}")
    cancel_result = cancel_order(symbol, order_id)
    print_json(format_cancel_response(cancel_result))


def _handle_cancel_client(args: Sequence[str]) -> None:
    if len(args) < 2:
        raise ValueError("cancel_client 需要提供 SYMBOL 和 CLIENT_ORDER_ID")
    symbol, client_order_id = args[0], args[1]
    from shared.output_utils import print_json

    logger.warning(f"⚠️ 即将取消订单(客户端ID): {symbol} ClientID:{client_order_id}")
    cancel_result = cancel_order_by_client_id(symbol, client_order_id)
    print_json(format_cancel_response(cancel_result))


def _handle_cancel_all(args: Sequence[str]) -> None:
    if len(args) < 1:
        raise ValueError("cancel_all 需要提供 SYMBOL")
    symbol = args[0]
    from shared.output_utils import print_json

    logger.warning(f"⚠️ 即将取消所有订单: {symbol}")
    cancel_result = cancel_all_orders(symbol)
    print_json(_format_cancel_all(cancel_result))


def _handle_status(args: Sequence[str]) -> None:
    if len(args) < 2:
        raise ValueError("status 需要提供 SYMBOL 和 ORDER_ID")
    symbol, order_id_str = args[0], args[1]
    order_id = int(order_id_str)
    from shared.output_utils import print_json

    order_info = get_order_status(symbol, order_id)
    print_json(format_cancel_response(order_info))


def _format_cancel_all(payload: Any) -> Any:
    if isinstance(payload, list):
        return [format_cancel_response(cast(dict[str, Any], item)) for item in payload]
    if isinstance(payload, dict):
        return format_cancel_response(payload)
    return payload


def _print_usage() -> None:
    logger.info("用法:")
    logger.info("  p cancel_order.py cancel SYMBOL ORDER_ID")
    logger.info("  p cancel_order.py cancel_client SYMBOL CLIENT_ORDER_ID")
    logger.info("  p cancel_order.py cancel_all SYMBOL")
    logger.info("  p cancel_order.py status SYMBOL ORDER_ID")
    logger.info("示例:")
    logger.info("  p cancel_order.py cancel ADAUSDC 12345")
    logger.info("  p cancel_order.py cancel_all ADAUSDC")
