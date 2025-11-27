"""
获取 Binance 所有订单历史 - 纯函数实现.

通过 `p -m ibkr_api.get_all_orders` 运行, 无需手动修改 sys.path.
"""

from typing import Any

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m ibkr_api.get_all_orders` 运行该模块, 无需手动修改 sys.path"
    )

from loguru import logger

from ibkr_api.common import get_configured_client
from shared.output_utils import print_json


def get_all_orders(symbol: str, limit: int = 1000, order_id: int | None = None) -> Any:
    """获取所有订单历史

    Args:
        symbol: 交易对
        limit: 返回订单数量限制 (默认500, 最大1000)
        order_id: 从此订单ID开始获取

    Returns:
        Any: 订单历史数据(币安API原始返回)
    """
    client = get_configured_client()

    return client.get_all_orders(
        symbol=symbol.upper(), limit=min(limit, 1000), orderId=order_id
    )


def _print_usage() -> None:
    logger.info("用法: p get_all_orders.py <交易对> [限制数量] [订单ID]")
    logger.info("示例:")
    logger.info("  p get_all_orders.py ADAUSDC")
    logger.info("  p get_all_orders.py ADAUSDC 100")
    logger.info("  p get_all_orders.py ADAUSDC 100 12345678  # 增量查询必须指定limit")


def _parse_cli_args(args: list[str]) -> tuple[str, int, int | None]:
    symbol = args[0]
    limit = int(args[1]) if len(args) > 1 else 1000
    order_id = int(args[2]) if len(args) > 2 else None
    return symbol, limit, order_id


def _build_result(
    symbol: str, limit: int, order_id: int | None, orders: Any
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "symbol": symbol.upper(),
        "limit": limit,
        "count": len(orders),
        "orders": orders,
    }
    if order_id is not None:
        result["from_order_id"] = order_id
    return result


def main():
    """演示获取所有订单历史"""
    import sys

    if len(sys.argv) < 2:
        _print_usage()
        return

    symbol, limit, order_id = _parse_cli_args(sys.argv[1:])
    orders = get_all_orders(symbol, limit, order_id)
    print_json(_build_result(symbol, limit, order_id, orders))


if __name__ == "__main__":
    main()
