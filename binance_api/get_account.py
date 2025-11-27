"""
获取 Binance 账户基本信息 - 纯函数实现

专注功能: 账户信息查询. 通过 `p -m binance_api.get_account` 直接运行即可查看账户信息.
"""

from typing import Any

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m binance_api.get_account` 运行该模块, 无需手动修改 sys.path"
    )

Client = Any

from loguru import logger


def account_info(client: Client) -> dict[str, Any]:
    """获取账户基本信息"""
    logger.debug("🔍 获取Binance账户信息")
    return client.get_account()


def main():
    """演示获取账户信息"""
    # 内部获取客户端
    from binance_api.common import get_configured_client
    from shared.output_utils import print_json

    client = get_configured_client()

    account_data = account_info(client)

    # 直接输出原始数据, 不做加工
    print_json(account_data)


if __name__ == "__main__":
    main()
