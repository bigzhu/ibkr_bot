"""
获取 IBKR 账户基本信息 - 纯函数实现

专注功能: 账户信息查询. 通过 `p -m ibkr_api.get_account` 直接运行即可查看账户信息.
"""

from collections.abc import Iterable
from decimal import Decimal
from typing import Any

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m ibkr_api.get_account` 运行该模块, 无需手动修改 sys.path"
    )

from loguru import logger

Client = Any


def _parse_account_summary(raw: dict[str, Any]) -> dict[str, Any]:
    """提取 IBKR 账户概要信息."""

    lowered = {k.lower(): v for k, v in raw.items()}

    currency = lowered.get("currency")
    net_liquidation = lowered.get("netliquidation")
    available_funds = lowered.get("availablefunds")
    buying_power = lowered.get("buyingpower")

    return {
        "account": raw.get("account") or lowered.get("account"),
        "currency": currency,
        "net_liquidation": Decimal(str(net_liquidation)) if net_liquidation else None,
        "available_funds": Decimal(str(available_funds)) if available_funds else None,
        "buying_power": Decimal(str(buying_power)) if buying_power else None,
        "raw": raw,
    }


def _to_json_safe(data: Any) -> Any:
    """将返回结果转换为可 JSON 序列化的类型."""
    if isinstance(data, Decimal):
        return str(data)
    if isinstance(data, dict):
        return {k: _to_json_safe(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_to_json_safe(v) for v in data]
    return data


def account_info(client: Client) -> dict[str, Any]:
    """获取 IBKR 账户基本信息."""

    logger.debug("🔍 获取 IBKR 账户信息")

    if hasattr(client, "account_summary") and callable(client.account_summary):
        summary = client.account_summary()
        if not summary:
            raise ValueError("未能获取 IBKR 账户信息")
        if not isinstance(summary, dict):
            raise TypeError("account_summary 返回值应为 dict")
        return _to_json_safe(_parse_account_summary(summary))

    if hasattr(client, "reqAccountSummary") and callable(client.reqAccountSummary):
        # 适配 ib_insync.IB.reqAccountSummary
        values = client.reqAccountSummary(
            "All", ["NetLiquidation", "AvailableFunds", "BuyingPower", "Currency"]
        )
        summary_dict: dict[str, Any] = {}
        for item in values if isinstance(values, Iterable) else []:
            tag = getattr(item, "tag", None)
            val = getattr(item, "value", None)
            if not tag:
                continue
            summary_dict[tag] = val
            summary_dict.setdefault("currency", getattr(item, "currency", None))
            summary_dict.setdefault("account", getattr(item, "account", None))
        if not summary_dict:
            raise ValueError("未能获取 IBKR 账户信息(reqAccountSummary)")
        return _to_json_safe(_parse_account_summary(summary_dict))

    if hasattr(client, "accountValues"):
        # 适配 ib_insync.IB.accountValues 列表
        values = getattr(client, "accountValues", None)
        summary_dict: dict[str, Any] = {}
        iterable_values = values if isinstance(values, Iterable) else []
        for item in iterable_values:
            tag = getattr(item, "tag", None)
            val = getattr(item, "value", None)
            if not tag:
                continue
            summary_dict[tag] = val
            summary_dict.setdefault("currency", getattr(item, "currency", None))
            summary_dict.setdefault("account", getattr(item, "account", None))
        if not summary_dict:
            raise ValueError("未能获取 IBKR 账户信息(accountValues)")
        return _to_json_safe(_parse_account_summary(summary_dict))

    raise AttributeError("IBKR 客户端未实现 account_summary/reqAccountSummary/accountValues")


def main():
    """演示获取账户信息"""
    # 内部获取客户端
    from ibkr_api.common import get_configured_client
    from shared.output_utils import print_json

    client = get_configured_client()

    account_data = account_info(client)

    # 直接输出原始数据, 不做加工
    print_json(account_data)


if __name__ == "__main__":
    main()
