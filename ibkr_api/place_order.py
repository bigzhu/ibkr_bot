"""IBKR 下单接口."""

from __future__ import annotations

import sys
from decimal import Decimal
from typing import Any

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m ibkr_api.place_order` 运行, 无需手动修改 sys.path"
    )

from ibapi.contract import Contract
from ibapi.order import Order as IBOrder
from loguru import logger

from ibkr_api.common import IBKRClient, get_api_config, get_configured_client
from shared.output_utils import print_json


def _build_contract(symbol: str, exchange: str, currency: str, sec_type: str) -> Contract:
    contract = Contract()
    contract.symbol = symbol.upper()
    contract.secType = sec_type.upper()
    contract.exchange = exchange.upper()
    contract.currency = currency.upper()
    return contract


def _build_order(
    action: str,
    order_type: str,
    quantity: Decimal,
    limit_price: Decimal | None,
    tif: str,
    outside_rth: bool,
) -> IBOrder:
    order = IBOrder()
    order.action = action.upper()
    order.orderType = order_type.upper()
    order.totalQuantity = int(quantity)
    order.tif = tif.upper()
    order.outsideRth = outside_rth
    if order.orderType == "LMT":
        if limit_price is None:
            raise ValueError("限价单需要提供 limit_price")
        order.lmtPrice = float(limit_price)
    return order


def place_order(
    client: IBKRClient,
    symbol: str,
    exchange: str = "SMART",
    currency: str | None = None,
    sec_type: str = "STK",
    side: str = "BUY",
    order_type: str = "MKT",
    quantity: Decimal | float | str = "0",
    limit_price: Decimal | float | str | None = None,
    tif: str = "DAY",
    outside_rth: bool = False,
) -> dict[str, Any]:
    """下单并返回订单基础信息."""
    qty_decimal = Decimal(str(quantity))
    limit_decimal = Decimal(str(limit_price)) if limit_price is not None else None

    cfg = get_api_config()
    use_currency = currency or cfg.base_currency

    contract = _build_contract(symbol, exchange, use_currency, sec_type)
    order = _build_order(side, order_type, qty_decimal, limit_decimal, tif, outside_rth)

    order_id = client.next_order_id()
    logger.info(
        f"📤 提交订单 id={order_id} {side.upper()} {qty_decimal} {symbol.upper()} "
        f"type={order_type.upper()} tif={tif} exch={exchange.upper()} cur={use_currency}"
    )
    client.placeOrder(order_id, contract, order)

    return {
        "order_id": order_id,
        "symbol": symbol.upper(),
        "exchange": exchange.upper(),
        "currency": use_currency.upper(),
        "sec_type": sec_type.upper(),
        "side": side.upper(),
        "order_type": order_type.upper(),
        "quantity": str(qty_decimal),
        "limit_price": str(limit_decimal) if limit_decimal is not None else None,
        "tif": tif.upper(),
        "outside_rth": outside_rth,
    }


def main() -> None:
    """命令行演示: 提交市价买单."""
    client = get_configured_client()

    if len(sys.argv) < 3:
        _print_usage()
        return

    symbol = sys.argv[1]
    qty_arg = sys.argv[2]
    exchange = sys.argv[3] if len(sys.argv) > 3 else "SMART"
    currency = sys.argv[4] if len(sys.argv) > 4 else None
    side = sys.argv[5] if len(sys.argv) > 5 else "BUY"
    order_type = sys.argv[6] if len(sys.argv) > 6 else "MKT"
    limit_price = sys.argv[7] if len(sys.argv) > 7 else None

    try:
        result = place_order(
            client=client,
            symbol=symbol,
            exchange=exchange,
            currency=currency,
            sec_type="STK",
            side=side,
            order_type=order_type,
            quantity=qty_arg,
            limit_price=limit_price,
        )
    except Exception as exc:  # - CLI 入口统一提示
        logger.error(f"❌ 下单失败: {exc}")
        return

    print_json(result)


def _print_usage() -> None:
    logger.info("用法: p -m ibkr_api.place_order SYMBOL QTY [EXCHANGE] [CURRENCY] [SIDE] [TYPE] [LIMIT_PRICE]")
    logger.info("示例: p -m ibkr_api.place_order AAPL 10 SMART USD BUY LMT 150")


if __name__ == "__main__":
    main()
