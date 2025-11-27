"""获取 IBKR 成交明细."""

from __future__ import annotations

from typing import Any

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m ibkr_api.get_executions` 运行, 无需手动修改 sys.path"
    )

from loguru import logger

from ibkr_api.common import IBKRClient, get_configured_client
from shared.output_utils import print_json


def get_executions(client: IBKRClient) -> list[dict[str, Any]]:
    """同步获取成交明细."""
    logger.debug("🔍 获取 IBKR 成交明细")
    return client.executions()


def main() -> None:
    client = get_configured_client()
    executions = get_executions(client)
    print_json(executions)


if __name__ == "__main__":
    main()
