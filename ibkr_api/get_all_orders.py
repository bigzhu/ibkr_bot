"""获取 IBKR 历史成交(最小封装)."""

from __future__ import annotations

from typing import Any

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m ibkr_api.get_all_orders` 运行该模块, 无需手动修改 sys.path"
    )

from loguru import logger

from ibkr_api.common import IBKRClient, get_configured_client
from ibkr_api.get_executions import get_executions
from shared.output_utils import print_json


def get_all_orders(client: IBKRClient, symbol: str | None = None) -> dict[str, Any]:
    """获取成交明细(可选按 symbol 过滤)."""
    executions = get_executions(client)

    if symbol:
        symbol_upper = symbol.upper()
        executions = [e for e in executions if (e.get("symbol") or "").upper() == symbol_upper]

    return {
        "symbol": symbol.upper() if symbol else None,
        "executions": executions,
    }


def _print_usage() -> None:
    logger.info("用法: p -m ibkr_api.get_all_orders [SYMBOL]")
    logger.info("示例: p -m ibkr_api.get_all_orders")
    logger.info("示例: p -m ibkr_api.get_all_orders AAPL")


def main() -> None:
    import sys

    symbol = sys.argv[1] if len(sys.argv) > 1 else None

    client = get_configured_client()
    try:
        result = get_all_orders(client, symbol)
        print_json(result)
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
