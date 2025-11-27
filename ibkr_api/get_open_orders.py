"""获取 IBKR 未完成订单列表."""

from __future__ import annotations

from typing import Any

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m ibkr_api.get_open_orders` 运行, 无需手动修改 sys.path"
    )

from loguru import logger

from ibkr_api.common import IBKRClient, get_configured_client
from shared.output_utils import print_json


def get_open_orders(client: IBKRClient) -> list[dict[str, Any]]:
    """同步获取未完成订单."""
    logger.debug("🔍 获取 IBKR 未完成订单")
    return client.open_orders()


def main() -> None:
    client = get_configured_client()
    orders = get_open_orders(client)
    print_json(orders)


if __name__ == "__main__":
    main()
