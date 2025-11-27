"""获取 IBKR 持仓列表."""

from __future__ import annotations

from typing import Any

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m ibkr_api.get_positions` 运行, 无需手动修改 sys.path"
    )

from loguru import logger

from ibkr_api.common import IBKRClient, get_configured_client
from shared.output_utils import print_json


def get_positions(client: IBKRClient) -> list[dict[str, Any]]:
    """同步获取持仓."""
    logger.debug("🔍 获取 IBKR 持仓列表")
    return client.positions()


def main() -> None:
    client = get_configured_client()
    positions = get_positions(client)
    print_json(positions)


if __name__ == "__main__":
    main()
