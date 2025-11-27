"""
获取 Binance 交易所信息 - 纯函数实现.

通过 `p -m ibkr_api.get_exchange_info` 运行, 无需手动修改 sys.path.
"""

from typing import Any

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m ibkr_api.get_exchange_info` 运行该模块, 无需手动修改 sys.path"
    )

Client = Any

from loguru import logger


def exchange_info(client: Client) -> dict[str, Any]:
    """获取交易所信息"""
    logger.debug("🔍 获取Binance交易所信息")
    return client.get_exchange_info()


def get_symbol_info(client: Client, symbol: str) -> dict[str, Any]:
    """获取指定交易对信息"""
    logger.debug(f"🔍 获取 {symbol} 交易对信息")

    exchange_data = exchange_info(client)

    for symbol_info in exchange_data["symbols"]:
        if symbol_info["symbol"] == symbol.upper():
            return symbol_info

    raise ValueError(f"未找到交易对: {symbol}")


def get_symbol_precision(client: Client, symbol: str) -> dict[str, Any]:
    """获取交易对精度信息"""
    logger.debug(f"🔍 获取 {symbol} 精度信息")

    symbol_info = get_symbol_info(client, symbol)

    # 提取过滤器信息
    price_filter = None
    lot_size_filter = None
    notional_filter = None

    for filter_info in symbol_info["filters"]:
        if filter_info["filterType"] == "PRICE_FILTER":
            price_filter = filter_info
        elif filter_info["filterType"] == "LOT_SIZE":
            lot_size_filter = filter_info
        elif filter_info["filterType"] in ["MIN_NOTIONAL", "NOTIONAL"]:
            notional_filter = filter_info

    return {
        "symbol": symbol.upper(),
        "base_asset": symbol_info["baseAsset"],
        "quote_asset": symbol_info["quoteAsset"],
        "base_asset_precision": symbol_info["baseAssetPrecision"],
        "quote_asset_precision": symbol_info["quoteAssetPrecision"],
        "price_filter": price_filter,
        "lot_size_filter": lot_size_filter,
        "notional_filter": notional_filter,
    }


def get_complete_symbol_data(client: Client, symbol: str) -> dict[str, Any]:
    """
    获取用于插入trading_symbols表的完整交易对数据

    Args:
        client: Binance API客户端
        symbol: 交易对符号 (如: ADAUSDC)

    Returns:
        包含所有trading_symbols表字段的字典

    Raises:
        ValueError: 交易对不存在时抛出
    """
    logger.debug(f"🔍 获取 {symbol} 完整数据用于数据库插入")

    symbol_info = get_symbol_info(client, symbol)
    filters = _extract_filters(symbol_info)
    return {
        **_build_basic_symbol_payload(symbol_info),
        **_build_precision_payload(symbol_info),
        **_build_trading_limits_payload(filters),
        **_build_market_defaults(),
        **_build_system_defaults(),
    }


def get_symbol_info_safe(client: Client, symbol: str) -> dict[str, Any] | None:
    """获取指定交易对信息,不存在时返回None而不是抛出异常"""
    logger.debug(f"🔍 获取 {symbol} 交易对信息 (安全模式)")

    exchange_data = exchange_info(client)

    for symbol_info in exchange_data["symbols"]:
        if symbol_info["symbol"] == symbol.upper():
            return symbol_info

    logger.debug(f"未找到交易对: {symbol}")
    return None


def main():
    """演示获取交易所信息"""
    import sys

    from ibkr_api.common import get_configured_client
    from shared.output_utils import print_json

    client = get_configured_client()

    if len(sys.argv) > 1:
        # 获取指定交易对信息
        symbol = sys.argv[1]
        if len(sys.argv) > 2 and sys.argv[2] == "precision":
            # 获取精度信息
            precision_info = get_symbol_precision(client, symbol)
            print_json(precision_info)
        else:
            # 获取交易对基本信息
            symbol_info = get_symbol_info(client, symbol)
            print_json(symbol_info)
    else:
        # 获取交易所信息(原始数据)
        exchange_data = exchange_info(client)

        # 简化输出, 只显示基本信息和前10个交易对
        simplified_data = {
            "timezone": exchange_data["timezone"],
            "serverTime": exchange_data["serverTime"],
            "rateLimits": exchange_data["rateLimits"][:3],  # 前3个限制
            "symbols_count": len(exchange_data["symbols"]),
            "symbols_sample": exchange_data["symbols"][:10],  # 前10个交易对
        }

        print_json(simplified_data)


if __name__ == "__main__":
    main()


def _extract_filters(symbol_info: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """按过滤器类型整理交易对过滤器"""
    filters = {f["filterType"]: f for f in symbol_info["filters"]}
    price_filter = filters.get("PRICE_FILTER", {})
    lot_size_filter = filters.get("LOT_SIZE", {})
    notional_filter = filters.get("MIN_NOTIONAL") or filters.get("NOTIONAL", {})
    return {
        "price": price_filter,
        "lot_size": lot_size_filter,
        "notional": notional_filter or {},
    }


def _build_basic_symbol_payload(symbol_info: dict[str, Any]) -> dict[str, Any]:
    """构建交易对基础字段"""
    base_asset = symbol_info["baseAsset"]
    quote_asset = symbol_info["quoteAsset"]
    return {
        "symbol": symbol_info["symbol"],
        "base_asset": base_asset,
        "quote_asset": quote_asset,
        "is_active": True,
        "description": f"{base_asset}/{quote_asset} 交易对",
    }


def _build_precision_payload(symbol_info: dict[str, Any]) -> dict[str, Any]:
    """构建交易对精度字段"""
    return {
        "base_asset_precision": symbol_info["baseAssetPrecision"],
        "quote_asset_precision": symbol_info["quoteAssetPrecision"],
    }


def _build_trading_limits_payload(filters: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """基于过滤器构建交易限制字段"""
    lot_size = filters["lot_size"]
    price = filters["price"]
    notional = filters["notional"]
    return {
        "min_qty": float(lot_size.get("minQty", 0)),
        "max_qty": float(lot_size.get("maxQty", 0)),
        "step_size": float(lot_size.get("stepSize", 0)),
        "min_notional": float(notional.get("minNotional", 0)),
        "min_price": float(price.get("minPrice", 0)),
        "max_price": float(price.get("maxPrice", 0)),
        "tick_size": float(price.get("tickSize", 0)),
    }


def _build_market_defaults() -> dict[str, int]:
    """构建市场数据默认字段"""
    return {
        "current_price": 0,
        "volume_24h": 0,
        "volume_24h_quote": 0,
        "price_change_24h": 0,
        "high_24h": 0,
        "low_24h": 0,
    }


def _build_system_defaults() -> dict[str, Any]:
    """构建系统默认字段"""
    return {
        "last_updated_price": None,
        "max_fund": None,
    }
