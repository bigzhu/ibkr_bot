"""获取 Binance 账户余额 - 纯函数实现."""

import sys
from decimal import Decimal
from typing import Any, TypedDict, cast

try:
    from binance.client import Client
except ImportError:  # pragma: no cover - fallback for optional dependency
    Client = None

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m ibkr_api.get_balance` 运行该模块, 无需手动修改 sys.path"
    )

from binance.exceptions import BinanceAPIException
from loguru import logger

from database.crud import get_symbol_info
from ibkr_api.common import (
    get_api_config_from_db,
    get_configured_client,
    get_current_price,
)


class BalanceBreakdown(TypedDict):
    asset: str
    spot: Decimal
    funding: Decimal
    flexible: Decimal
    total: Decimal


from shared.output_utils import print_json


def get_account_info(client: Any) -> dict[str, Any]:
    """获取账户信息"""
    logger.debug("🔍 获取Binance账户信息")
    return client.get_account()


def get_balance(asset: str) -> float:
    """获取指定资产在各账户的总余额(现货 + 资金 + 理财-flex)"""
    breakdown = get_balance_breakdown(asset)
    return float(breakdown["total"])


def get_balance_breakdown(asset: str) -> BalanceBreakdown:
    """返回资产在各账户的余额明细"""
    logger.debug(f"🔍 获取 {asset} 余额明细")

    client = get_configured_client()
    asset_upper = asset.upper()

    spot_balance, ld_hint = _get_spot_balances(client, asset_upper)
    funding_balance = _get_funding_balance(client, asset_upper)
    flexible_earn_balance = _get_flexible_earn_balance(client, asset_upper)
    if flexible_earn_balance == 0 and ld_hint > 0:
        logger.debug(f"INFO 理财接口无数据, 使用 LD 资产估算 {asset_upper} = {ld_hint}")
        flexible_earn_balance = ld_hint

    total_balance = spot_balance + funding_balance + flexible_earn_balance

    logger.debug(
        f"💡 余额明细 | 现货: {spot_balance} | 资金: {funding_balance} | 理财: {flexible_earn_balance} | 合计: {total_balance}"
    )

    return {
        "asset": asset_upper,
        "spot": spot_balance,
        "funding": funding_balance,
        "flexible": flexible_earn_balance,
        "total": total_balance,
    }


def _safe_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _get_spot_balances(client: Any, asset: str) -> tuple[Decimal, Decimal]:
    """获取现货账户余额, 包含 LD 资产提示"""
    account_data = get_account_info(client)
    spot_total = Decimal("0")
    ld_total = Decimal("0")
    ld_code = f"LD{asset}"

    for balance in account_data["balances"]:
        asset_code = balance.get("asset")
        amount = _safe_decimal(balance.get("free", "0"))
        if asset_code == asset:
            spot_total += amount
        elif asset_code == ld_code:
            ld_total += amount

    return spot_total, ld_total


def _get_funding_balance(client: Any, asset: str) -> Decimal:
    """获取资金账户余额"""
    try:
        response = client.funding_wallet(asset=asset)
    except BinanceAPIException as exc:
        logger.debug(f"⚠️ 获取资金账户余额失败({asset}): {exc}")
        return Decimal("0")

    total = Decimal("0")
    alias_assets = _expand_ld_asset(asset)
    for item in cast(list[dict[str, Any]], response or []):
        asset_code = item.get("asset")
        if asset_code in alias_assets:
            total += _safe_decimal(item.get("free", "0"))
    return total


def _get_flexible_earn_balance(client: Any, asset: str) -> Decimal:
    """获取理财-活期(保本赚币)持仓余额"""
    params = {
        "asset": asset,
        "current": 1,
        "size": 100,
    }
    try:
        response = client._request_margin_api(
            "get", "simple-earn/flexible/position", signed=True, data=params
        )
    except BinanceAPIException as exc:
        logger.debug(f"⚠️ 获取理财活期余额失败({asset}): {exc}")
        return Decimal("0")

    total = Decimal("0")
    alias_assets = _expand_ld_asset(asset)
    rows = cast(list[dict[str, Any]], response.get("rows", []))
    for row in rows:
        asset_code = row.get("asset")
        if asset_code in alias_assets:
            total += _safe_decimal(row.get("totalAmount", "0"))
    return total


def _expand_ld_asset(asset: str) -> set[str]:
    """返回同一币种的资产别名集合, 包含 LD 前缀版本"""
    asset_upper = asset.upper()
    candidates = {asset_upper}
    if not asset_upper.startswith("LD"):
        candidates.add(f"LD{asset_upper}")
    else:
        candidates.add(asset_upper[2:])
    return candidates


def _resolve_assets(asset_input: str) -> list[str]:
    """Expand a user provided asset to base/quote symbols if possible."""
    asset_upper = asset_input.upper()
    if asset_upper.startswith("LD"):
        asset_upper = asset_upper[2:]

    try:
        symbol = get_symbol_info(asset_upper)
        return [symbol.base_asset.upper(), symbol.quote_asset.upper()]
    except Exception:
        return [asset_upper]


def get_all_balances(client: Any) -> list[dict[str, Any]]:
    """获取所有资产余额"""
    logger.debug("🔍 获取所有资产余额")
    account_data = get_account_info(client)

    balances: list[dict[str, Any]] = []
    for balance in account_data["balances"]:
        free = Decimal(str(balance["free"]))
        locked = Decimal(str(balance["locked"]))
        total = free + locked

        if total > 0:  # 只返回有余额的资产
            balances.append(
                {
                    "asset": balance["asset"],
                    "free": free,
                    "locked": locked,
                    "total": total,
                }
            )

    # 按总余额降序排序
    return sorted(balances, key=lambda x: x["total"], reverse=True)


def get_balance_in_usdt(
    client: Any, asset: str, price_cache: dict[str, Decimal] | None = None
) -> Decimal:
    """获取资产的USDT价值"""
    if price_cache is None:
        price_cache = {}

    if asset == "USDT":
        return Decimal(str(get_balance(asset)))

    balance = Decimal(str(get_balance(asset)))
    if balance == 0:
        return Decimal("0")

    # 获取价格 - fail-fast原则: 价格获取失败立即抛出异常
    symbol = f"{asset}USDT"
    if symbol not in price_cache:
        price_cache[symbol] = get_current_price(client, symbol)

    price = price_cache[symbol]
    return balance * price


def calculate_total_balance_usdt(client: Any) -> dict[str, Any]:
    """计算总资产的USDT价值"""
    logger.debug("🔍 计算总资产USDT价值")

    balances = get_all_balances(client)
    price_cache: dict[str, Decimal] = {}

    total_usdt = Decimal("0")
    asset_values: list[dict[str, Any]] = []

    for balance in balances:
        asset = balance["asset"]
        usdt_value = get_balance_in_usdt(client, asset, price_cache)

        if usdt_value > 0:
            asset_values.append(
                {
                    "asset": asset,
                    "balance": balance["total"],
                    "usdt_value": usdt_value,
                    "percentage": Decimal("0"),  # 稍后计算
                }
            )
            total_usdt += usdt_value

    # 计算百分比
    for asset_value in asset_values:
        if total_usdt > 0:
            asset_value["percentage"] = (asset_value["usdt_value"] / total_usdt) * 100

    return {
        "total_usdt": total_usdt,
        "asset_values": sorted(
            asset_values, key=lambda x: x["usdt_value"], reverse=True
        ),
    }


def display_balance_info():
    """显示余额信息 - 纯原子函数, 不捕获任何异常"""
    logger.info("💰 Binance账户余额查询")
    logger.info("=" * 60)

    client, environment = _setup_binance_client()
    account_data = _display_account_info(client)
    balances = _display_asset_balances(client)
    _display_major_assets_info()
    _display_total_asset_value(client, account_data, balances, environment)


def _setup_binance_client() -> tuple[Any, str]:
    """设置Binance客户端"""
    logger.info("1. 获取API配置...")
    api_config = get_api_config_from_db()

    if not api_config:
        logger.error("❌ Binance API密钥未配置")
        logger.info("\n请检查数据库中API密钥配置")
        raise ValueError("API配置缺失")

    environment = api_config["environment"]
    logger.info(f"   ✅ 环境: {environment}")

    logger.info("\n2. 连接Binance API...")
    if not Client:
        raise ImportError("Binance 客户端库未安装")

    client = Client(
        api_key=api_config["api_key"],
        api_secret=api_config["secret_key"],
        testnet=api_config["testnet"],
    )
    logger.info("   ✅ 客户端连接成功")
    return client, environment


def _display_account_info(client: Any) -> dict[str, Any]:
    """显示账户基本信息"""
    logger.info("\n3. 账户基本信息:")
    account_data = get_account_info(client)
    logger.info(f"   - 账户类型: {account_data.get('accountType', 'SPOT')}")
    logger.info(f"   - 可交易: {account_data.get('canTrade', True)}")
    logger.info(f"   - 可提取: {account_data.get('canWithdraw', True)}")
    logger.info(f"   - 可存入: {account_data.get('canDeposit', True)}")
    return account_data


def _display_asset_balances(client: Any) -> list[dict[str, Any]]:
    """显示资产余额详情"""
    logger.info("\n4. 资产余额详情:")
    balances = get_all_balances(client)

    if balances:
        for balance in balances[:15]:  # 显示前15个
            asset = balance["asset"]
            free = balance["free"]
            locked = balance["locked"]
            total = balance["total"]

            if locked > 0:
                logger.info(f"   - {asset}: {free} (可用) + {locked} (冻结) = {total}")
            else:
                logger.info(f"   - {asset}: {total}")

        if len(balances) > 15:
            logger.info(f"   ... 还有 {len(balances) - 15} 个资产")
    else:
        logger.info("   - 暂无资产余额")

    return balances


def _display_major_assets_info():
    """显示主要资产余额信息"""
    logger.info("\n5. 主要资产余额:")
    major_assets = ["USDT", "BTC", "ETH", "BNB", "ADA", "DOT"]
    for asset in major_assets:
        balance = get_balance(asset)
        if balance > 0:
            logger.info(f"   - {asset}: {balance}")
        else:
            logger.info(f"   - {asset}: 0")


def _display_total_asset_value(
    client: Any,
    account_data: dict[str, Any],
    balances: list[dict[str, Any]],
    environment: str,
) -> None:
    """显示总资产价值和统计"""
    logger.info("\n6. 总资产价值 (USDT计价):")
    total_info = calculate_total_balance_usdt(client)
    total_usdt = total_info["total_usdt"]
    asset_values = total_info["asset_values"]

    logger.info(f"   💰 总价值: {total_usdt:.2f} USDT")

    if asset_values:
        logger.info("\n   资产分布 (前8个):")
        for asset_value in asset_values[:8]:
            asset = asset_value["asset"]
            value = asset_value["usdt_value"]
            percentage = asset_value["percentage"]
            logger.info(f"     - {asset}: {value:.2f} USDT ({percentage:.1f}%)")

        if len(asset_values) > 8:
            other_value = sum(av["usdt_value"] for av in asset_values[8:])
            other_percentage = (other_value / total_usdt) * 100 if total_usdt > 0 else 0
            logger.info(
                f"     - 其他: {other_value:.2f} USDT ({other_percentage:.1f}%)"
            )

    logger.info("\n7. 资产统计:")
    logger.info(f"   - 总资产种类: {len(account_data['balances'])}")
    logger.info(f"   - 有余额资产: {len(balances)}")
    frozen_count = len([b for b in balances if b["locked"] > 0])
    logger.info(f"   - 有冻结资产: {frozen_count}")

    logger.info("\n✅ 余额查询完成")
    logger.info(f"🔧 环境: {environment}")


def main():
    """演示获取余额信息"""
    client = get_configured_client()

    if len(sys.argv) > 1:
        asset_input = sys.argv[1]
        assets = _resolve_assets(asset_input)
        result = {}
        for asset in assets:
            breakdown = get_balance_breakdown(asset)
            result[asset] = {k: str(v) for k, v in breakdown.items() if k != "asset"}
        print_json({"input": asset_input.upper(), "balances": result})
    else:
        account_data = get_account_info(client)
        print_json(account_data)


if __name__ == "__main__":
    main()
