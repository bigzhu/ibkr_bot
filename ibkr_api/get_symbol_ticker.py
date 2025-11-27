"""
获取 Binance 交易对价格信息 - 纯函数实现.

通过 `p -m ibkr_api.get_symbol_ticker` 运行, 无需手动修改 sys.path.
"""

from collections.abc import Callable
from typing import Any, TypedDict

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m ibkr_api.get_symbol_ticker` 运行该模块, 无需手动修改 sys.path"
    )

Client = Any

from loguru import logger


def ticker_price(client: Client, symbol: str) -> dict[str, Any]:
    """获取交易对当前价格

    Args:
        client: Binance客户端
        symbol: 交易对

    Returns:
        dict: 价格信息
    """
    logger.debug(f"🔍 获取 {symbol} 当前价格")
    return client.get_symbol_ticker(symbol=symbol.upper())


def ticker_24hr(client: Client, symbol: str) -> dict[str, Any]:
    """获取24小时价格统计

    Args:
        client: Binance客户端
        symbol: 交易对

    Returns:
        dict: 24小时统计信息
    """
    logger.debug(f"🔍 获取 {symbol} 24小时统计")
    return client.get_ticker(symbol=symbol.upper())


def all_tickers(client: Client) -> list[dict[str, Any]]:
    """获取所有交易对价格"""
    logger.debug("🔍 获取所有交易对价格")
    return client.get_all_tickers()


def get_orderbook_ticker(client: Client, symbol: str) -> dict[str, Any]:
    """获取交易对订单簿最优买卖价

    Args:
        client: Binance客户端
        symbol: 交易对

    Returns:
        dict: 最优买卖价信息
    """
    logger.debug(f"🔍 获取 {symbol} 订单簿最优价格")
    return client.get_orderbook_ticker(symbol=symbol.upper())


def get_price_change_stats(symbol_data: dict[str, Any]) -> dict[str, Any]:
    """计算价格变化统计信息"""
    if "priceChange" not in symbol_data or "priceChangePercent" not in symbol_data:
        return {"trend": "unknown", "change": "0", "change_percent": "0"}

    price_change = float(symbol_data["priceChange"])
    price_change_percent = float(symbol_data["priceChangePercent"])

    if price_change > 0:
        trend = "up"
    elif price_change < 0:
        trend = "down"
    else:
        trend = "flat"

    return {
        "trend": trend,
        "change": str(price_change),
        "change_percent": f"{price_change_percent:.2f}%",
    }


def format_ticker_info(ticker_data: dict[str, Any]) -> dict[str, Any]:
    """格式化行情信息用于显示"""
    formatted = {
        "symbol": ticker_data["symbol"],
        "price": ticker_data.get("lastPrice", ticker_data.get("price", "0")),
    }

    # 如果有24小时统计数据
    if "priceChange" in ticker_data:
        stats = get_price_change_stats(ticker_data)
        formatted.update(
            {
                "change": stats["change"],
                "change_percent": stats["change_percent"],
                "trend": stats["trend"],
                "high_24h": ticker_data.get("highPrice", "0"),
                "low_24h": ticker_data.get("lowPrice", "0"),
                "volume_24h": ticker_data.get("volume", "0"),
            }
        )

    # 如果有订单簿数据
    if "bidPrice" in ticker_data:
        formatted.update(
            {
                "bid_price": ticker_data["bidPrice"],
                "ask_price": ticker_data["askPrice"],
                "spread": str(
                    float(ticker_data["askPrice"]) - float(ticker_data["bidPrice"])
                ),
            }
        )

    return formatted


def main() -> None:
    """演示获取价格信息"""
    import sys

    from ibkr_api.common import get_configured_client
    from shared.output_utils import print_json

    try:
        command = _parse_cli_args(sys.argv)
    except ValueError as exc:
        logger.error(exc)
        _print_usage()
        return

    client = get_configured_client()
    handlers = _command_handlers(client)
    handler = handlers.get(command["type"])
    if handler is None:
        logger.error("❌ 无效的命令或参数")
        _print_usage()
        return

    result = handler(command["symbol"])
    print_json(result)


if __name__ == "__main__":
    main()


class _TickerCommand(TypedDict):
    symbol: str
    type: str


def _parse_cli_args(argv: list[str]) -> _TickerCommand:
    if len(argv) < 2:
        raise ValueError("参数不足")
    symbol = argv[1]
    ticker_type = argv[2].lower() if len(argv) > 2 else "price"
    return _TickerCommand(symbol=symbol, type=ticker_type)


def _command_handlers(client: Client) -> dict[str, Callable[[str], Any]]:
    return {
        "price": lambda symbol: format_ticker_info(ticker_price(client, symbol)),
        "24hr": lambda symbol: format_ticker_info(ticker_24hr(client, symbol)),
        "orderbook": lambda symbol: format_ticker_info(
            get_orderbook_ticker(client, symbol)
        ),
        "all": lambda _: _format_all_tickers(all_tickers(client)),
    }


def _format_all_tickers(tickers: list[dict[str, Any]]) -> dict[str, Any]:
    sample = tickers[:20]
    return {
        "total_count": len(tickers),
        "sample_tickers": [format_ticker_info(t) for t in sample],
    }


def _print_usage() -> None:
    logger.info("用法: p get_symbol_ticker.py SYMBOL [TYPE]")
    logger.info("TYPE选项: price(默认), 24hr, orderbook, all")
    logger.info("示例: p get_symbol_ticker.py ADAUSDC 24hr")
