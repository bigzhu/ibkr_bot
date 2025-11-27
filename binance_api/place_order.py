"""
Binance下单功能 - 纯函数实现

专注功能: 订单创建和管理
直接运行即可测试下单功能
"""

import sys
from typing import Any

from loguru import logger

# 双重用途模块导入处理 - 唯一允许的 try-except
try:
    from shared.output_utils import print_json

    from .common import get_configured_client
except ImportError:
    try:
        from shared.path_utils import ensure_project_root_for_script
    except ImportError:
        from shared.path_utils import add_project_root_to_path

        add_project_root_to_path()
    else:
        ensure_project_root_for_script(__file__)
    from common import get_configured_client

    from shared.output_utils import print_json


def place_order(
    client: Any,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str | None = None,
    stop_price: str | None = None,
    time_in_force: str = "GTC",
    client_order_id: str | None = None,
) -> str:
    """下订单

    Args:
        client: Binance客户端
        symbol: 交易对
        side: 订单方向 ("BUY" 或 "SELL")
        order_type: 订单类型 ("LIMIT", "MARKET", "STOP_LOSS_LIMIT" 等)
        quantity: 数量
        price: 价格 (限价单必须)
        stop_price: 止损价格 (止损单必须)
        time_in_force: 时间有效性 ("GTC", "IOC", "FOK")
        client_order_id: 客户端订单ID (可选)

    Returns:
        str: 订单ID

    Raises:
        ValueError: 下单失败或响应中未找到订单ID时抛出异常
    """

    # 准备基础参数
    symbol_upper = symbol.upper()
    side_upper = side.upper()
    type_upper = order_type.upper()

    # 验证和准备参数
    if type_upper in ["LIMIT", "STOP_LOSS_LIMIT"] and not price:
        raise ValueError(f"{order_type}订单需要指定价格")

    if type_upper in ["STOP_LOSS", "STOP_LOSS_LIMIT"] and not stop_price:
        raise ValueError(f"{order_type}订单需要指定止损价格")

    # 根据订单类型设置参数
    final_price = price if type_upper in ["LIMIT", "STOP_LOSS_LIMIT"] else None
    final_time_in_force = (
        time_in_force.upper() if type_upper in ["LIMIT", "STOP_LOSS_LIMIT"] else None
    )

    order_response = client.create_order(
        symbol=symbol_upper,
        side=side_upper,
        type=type_upper,
        quantity=quantity,
        price=final_price,
        timeInForce=final_time_in_force,
        stopPrice=stop_price,
        newClientOrderId=client_order_id,
    )

    order_id = order_response.get("orderId")
    if not order_id:
        raise ValueError(f"下单响应中未找到订单ID, 完整响应: {order_response}")

    return order_id


def place_order_test(
    client: Any,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str | None = None,
    stop_price: str | None = None,
    time_in_force: str = "GTC",
    client_order_id: str | None = None,
) -> str:
    """测试下单 (不会实际成交)

    Args:
        client: Binance客户端
        symbol: 交易对
        side: 订单方向
        order_type: 订单类型
        quantity: 数量
        price: 价格
        stop_price: 止损价格
        time_in_force: 时间有效性
        client_order_id: 客户端订单ID (可选)

    Returns:
        str: 订单ID

    Raises:
        ValueError: 测试下单失败或响应中未找到订单ID时抛出异常
    """

    # 准备基础参数
    symbol_upper = symbol.upper()
    side_upper = side.upper()
    type_upper = order_type.upper()

    # 验证和准备参数
    if type_upper in ["LIMIT", "STOP_LOSS_LIMIT"] and not price:
        raise ValueError(f"{order_type}订单需要指定价格")

    if type_upper in ["STOP_LOSS", "STOP_LOSS_LIMIT"] and not stop_price:
        raise ValueError(f"{order_type}订单需要指定止损价格")

    # 根据订单类型设置参数
    final_price = price if type_upper in ["LIMIT", "STOP_LOSS_LIMIT"] else None
    final_time_in_force = (
        time_in_force.upper() if type_upper in ["LIMIT", "STOP_LOSS_LIMIT"] else None
    )

    order_response = client.create_test_order(
        symbol=symbol_upper,
        side=side_upper,
        type=type_upper,
        quantity=quantity,
        price=final_price,
        timeInForce=final_time_in_force,
        stopPrice=stop_price,
        newClientOrderId=client_order_id,
    )

    # 测试订单成功时返回空字典, 这是正常的
    if order_response == {}:
        return "test_order_success"

    order_id = order_response.get("orderId")
    if not order_id:
        raise ValueError(f"测试下单响应中未找到订单ID, 完整响应: {order_response}")

    return order_id


def main() -> None:
    """演示下单功能"""
    client = get_configured_client()

    if len(sys.argv) < 2:
        _print_usage()
        return

    command = sys.argv[1].lower()

    if command == "test":
        try:
            params = _parse_test_args(sys.argv[2:])
        except ValueError as exc:
            logger.error(f"❌ 参数错误: {exc}")
            _print_usage()
            return
        _handle_test_command(client, params)
        return

    logger.error("❌ 无效的命令或参数")


if __name__ == "__main__":
    main()


def _print_usage() -> None:
    logger.info(
        "用法: p place_order.py test SYMBOL SIDE TYPE QUANTITY [PRICE] [STOP_PRICE]"
    )
    logger.info("示例: p place_order.py test ADAUSDC BUY LIMIT 0.001 50000")
    logger.info(
        "示例: p place_order.py test ADAUSDC SELL STOP_LOSS_LIMIT 0.001 45000 46000"
    )


def _parse_test_args(args: list[str]) -> dict[str, str | None]:
    if len(args) < 4:
        raise ValueError("test 命令至少需要 SYMBOL SIDE TYPE QUANTITY 四个参数")

    symbol, side, order_type, quantity = args[:4]
    price = args[4] if len(args) > 4 else None
    stop_price = args[5] if len(args) > 5 else None
    return {
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "price": price,
        "stop_price": stop_price,
    }


def _handle_test_command(client: Any, params: dict[str, str | None]) -> None:
    symbol = str(params["symbol"])
    side = str(params["side"])
    order_type = str(params["order_type"])
    quantity = str(params["quantity"])
    price = params.get("price")
    stop_price = params.get("stop_price")

    logger.info(f"🧪 测试下单: {symbol} {side} {order_type}")
    test_result = place_order_test(
        client,
        symbol,
        side,
        order_type,
        quantity,
        price,
        stop_price,
    )

    result = {
        "test_status": "SUCCESS",
        "message": "测试订单验证通过",
        "order_id": test_result,
        "symbol": symbol.upper(),
        "side": side.upper(),
        "type": order_type.upper(),
        "quantity": quantity,
        "price": price,
        "stop_price": stop_price,
    }
    print_json(result)
