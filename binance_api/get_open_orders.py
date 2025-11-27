"""
获取 Binance 未成交订单 - 纯函数实现.

通过 `p -m binance_api.get_open_orders` 运行, 无需手动修改 sys.path.
"""

from typing import Any, cast

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m binance_api.get_open_orders` 运行该模块, 无需手动修改 sys.path"
    )


from binance_api.common import get_configured_client
from database.order_models import BinanceOpenOrder


def get_open_orders(symbol: str | None = None) -> list[BinanceOpenOrder]:
    """获取未成交订单

    Args:
        symbol: 交易对 (可选, 为None时获取所有未成交订单)

    Returns:
        list[BinanceOpenOrder]: 未成交订单列表

    Raises:
        RuntimeError: 当API返回错误时
    """
    client = get_configured_client()

    if symbol:
        result: Any = client.get_open_orders(symbol=symbol.upper())
    else:
        result = client.get_open_orders()

    # 检查返回结果是否为错误
    if isinstance(result, dict) and "code" in result:
        result_dict = cast(dict[str, Any], result)
        error_msg: str = str(result_dict.get("msg", "Unknown error"))
        raise RuntimeError(f"API错误: {error_msg}")

    # 构建 BinanceOpenOrder 对象列表
    orders_data = cast(list[dict[str, Any]], result)
    return [BinanceOpenOrder(**order) for order in orders_data]


def main():
    """演示获取未成交订单"""
    import sys

    from shared.output_utils import print_json

    if len(sys.argv) > 1:
        symbol = sys.argv[1]
        orders = get_open_orders(symbol)
        result = {
            "symbol": symbol.upper(),
            "count": len(orders),
            "orders": orders,
        }
    else:
        orders = get_open_orders()
        result = {
            "total_count": len(orders),
            "orders": orders,
        }

    print_json(result)


if __name__ == "__main__":
    main()
