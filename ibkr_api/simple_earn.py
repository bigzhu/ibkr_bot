"""
Simple Earn Flexible product helpers.

Provides utility functions for querying and redeeming flexible Simple Earn
positions so that funds can be moved back to the spot account before placing
orders.

遵循 CLAUDE.md 规范: fail-fast 原则, 类型注解, 禁用 try-except.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal
from typing import Any, cast

from binance.exceptions import BinanceAPIException
from loguru import logger

from ibkr_api.common import get_configured_client

FLEXIBLE_QUERY_PAGE_SIZE = 100
DECIMAL_PRECISION = Decimal("0.00000001")


def redeem_flexible_asset(asset: str, amount: Decimal) -> Decimal:
    """
    赎回指定资产的活期理财份额.

    Args:
        asset: 资产符号 (如 USDC).
        amount: 需要赎回的数量.

    Returns:
        Decimal: 实际提交赎回的数量.
    """
    asset_upper = asset.upper()
    if amount <= 0:
        return Decimal("0")

    client = get_configured_client()
    positions = _get_flexible_positions(client, asset_upper)
    if not positions:
        logger.info(f"无 {asset_upper} 活期理财持仓, 跳过赎回")
        return Decimal("0")

    redeem_func = _get_redeem_callable(client)
    if redeem_func is None:
        logger.warning("当前客户端缺少 redeem_simple_earn_flexible_product 接口")
        return Decimal("0")

    context = _RedeemContext(
        asset=asset_upper,
        remaining=amount,
        redeemed=Decimal("0"),
        redeem_func=redeem_func,
    )
    _redeem_from_positions(positions, context)

    if context.redeemed <= 0:
        logger.info(f"{asset_upper} 活期赎回未成功或无可赎回额度")
    return context.redeemed


def _get_flexible_positions(client: Any, asset: str) -> list[dict[str, Any]]:
    params = {
        "asset": asset,
        "current": 1,
        "size": FLEXIBLE_QUERY_PAGE_SIZE,
    }
    try:
        response = client._request_margin_api(
            "get", "simple-earn/flexible/position", signed=True, data=params
        )
    except BinanceAPIException as exc:
        logger.warning(f"获取 {asset} 活期理财持仓失败: {exc}")
        return []

    rows_raw = response.get("rows", [])
    if not isinstance(rows_raw, list):
        return []

    rows: list[dict[str, Any]] = cast(list[dict[str, Any]], rows_raw)

    filtered: list[dict[str, Any]] = []
    for row in rows:
        if row.get("asset") == asset:
            filtered.append(row)
    return filtered


@dataclass
class _RedeemContext:
    asset: str
    remaining: Decimal
    redeemed: Decimal
    redeem_func: Callable[..., Any]


def _redeem_from_positions(
    positions: list[dict[str, Any]], context: _RedeemContext
) -> None:
    for position in positions:
        available = _extract_available_amount(position)
        product_id = position.get("productId")
        if available <= 0 or not product_id:
            continue

        redeem_amount = _determine_redeem_amount(context.remaining, available)
        if redeem_amount <= 0:
            continue

        params = _build_redeem_params(product_id, redeem_amount, available)
        if _submit_redeem(context, params, redeem_amount, str(product_id)):
            context.redeemed += redeem_amount
            context.remaining -= redeem_amount
        if context.remaining <= 0:
            break


def _extract_available_amount(position: dict[str, Any]) -> Decimal:
    raw_value = (
        position.get("availableAmount")
        or position.get("totalAmount")
        or position.get("amount")
        or "0"
    )
    return _safe_decimal(raw_value)


def _determine_redeem_amount(remaining: Decimal, available: Decimal) -> Decimal:
    return _normalize_amount(min(available, remaining))


def _build_redeem_params(
    product_id: str, redeem_amount: Decimal, available: Decimal
) -> dict[str, Any]:
    params: dict[str, Any] = {"productId": product_id}
    if redeem_amount == available:
        params["redeemAll"] = True
    else:
        params["amount"] = str(redeem_amount)
    return params


def _submit_redeem(
    context: _RedeemContext,
    params: dict[str, Any],
    redeem_amount: Decimal,
    product_id: str,
) -> bool:
    try:
        context.redeem_func(**params)
        logger.info(
            f"已提交活期赎回 {redeem_amount} {context.asset} (productId={product_id})"
        )
        return True
    except BinanceAPIException as exc:
        logger.warning(
            f"赎回 {context.asset} 活期失败, productId={product_id}, error={exc}"
        )
        return False


def _get_redeem_callable(client: Any) -> Callable[..., Any] | None:
    redeem_raw = getattr(client, "redeem_simple_earn_flexible_product", None)
    if redeem_raw is None:
        return None
    return cast(Callable[..., Any], redeem_raw)


def _safe_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _normalize_amount(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_PRECISION, rounding=ROUND_DOWN)
