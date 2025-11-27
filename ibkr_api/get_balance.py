"""获取 IBKR 账户余额 - 纯函数实现."""

from decimal import Decimal
from typing import Any, TypedDict

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m ibkr_api.get_balance` 运行该模块, 无需手动修改 sys.path"
    )

from loguru import logger

from ibkr_api.common import get_configured_client
from ibkr_api.get_account import account_info
from shared.output_utils import print_json


class BalanceBreakdown(TypedDict):
    asset: str
    net_liquidation: Decimal
    available_funds: Decimal
    buying_power: Decimal
    total: Decimal


def _to_decimal(value: Any) -> Decimal:
    return Decimal(str(value)) if value is not None else Decimal("0")


def get_account_info(client: Any) -> dict[str, Any]:
    """获取 IBKR 账户概要信息."""
    return account_info(client)


def get_balance(asset: str) -> float:
    """获取指定资产的净值(仅支持账户基础货币)."""
    breakdown = get_balance_breakdown(asset)
    return float(breakdown["total"])


def get_balance_breakdown(asset: str) -> BalanceBreakdown:
    """返回资产余额明细(基于 IBKR account summary)."""
    client = get_configured_client()
    summary = get_account_info(client)

    asset_upper = asset.upper()
    currency = summary.get("currency", "")
    if asset_upper != currency:
        raise ValueError(f"账户基础货币为 {currency}, 不支持查询 {asset_upper}")

    net_liquidation = _to_decimal(summary.get("net_liquidation"))
    available_funds = _to_decimal(summary.get("available_funds"))
    buying_power = _to_decimal(summary.get("buying_power"))

    return {
        "asset": asset_upper,
        "net_liquidation": net_liquidation,
        "available_funds": available_funds,
        "buying_power": buying_power,
        "total": net_liquidation,
    }


def get_all_balances(client: Any | None = None) -> list[dict[str, Any]]:
    """获取账户基础货币的余额列表."""
    if client is None:
        client = get_configured_client()

    summary = get_account_info(client)
    currency = summary.get("currency", "")
    breakdown = get_balance_breakdown(currency)

    return [
        {
            "asset": breakdown["asset"],
            "balance": breakdown["total"],
            "available_funds": breakdown["available_funds"],
            "buying_power": breakdown["buying_power"],
        }
    ]


def calculate_total_balance_usd(client: Any | None = None) -> dict[str, Any]:
    """计算总资产(基础货币)的价值."""
    balances = get_all_balances(client)
    total = balances[0]["balance"] if balances else Decimal("0")
    return {"total": total, "currency": balances[0]["asset"] if balances else ""}


def display_balance_info() -> None:
    """显示 IBKR 账户余额信息."""
    logger.info("💰 IBKR 账户余额查询")
    logger.info("=" * 60)

    client = get_configured_client()
    summary = account_info(client)
    breakdown = get_balance_breakdown(asset=summary.get("currency", ""))
    print_json(_to_json_safe(breakdown))


def _to_json_safe(data: Any) -> Any:
    if isinstance(data, Decimal):
        return str(data)
    if isinstance(data, dict):
        return {k: _to_json_safe(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_to_json_safe(v) for v in data]
    return data


def main() -> None:
    """命令行入口: 查询并打印余额."""
    display_balance_info()


if __name__ == "__main__":
    main()
