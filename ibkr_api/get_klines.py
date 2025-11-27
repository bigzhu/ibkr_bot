"""获取 Binance K 线数据 - 纯函数实现."""

from typing import cast

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m ibkr_api.get_klines` 运行该模块, 无需手动修改 sys.path"
    )

from loguru import logger

from shared.types import BinanceKlinesClient, Kline


def klines(
    client: BinanceKlinesClient, symbol: str, interval: str = "1h", limit: int = 100
) -> list[Kline]:
    """获取K线数据

    Args:
        client: Binance客户端
        symbol: 交易对
        interval: 时间间隔 (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
        limit: 获取数量 (最大1000)

    Returns:
        list[dict]: K线数据列表
    """

    raw_klines: list[list[object]] = client.get_klines(
        symbol=symbol.upper(), interval=interval, limit=limit
    )

    # 转换为标准格式
    klines_data: list[Kline] = []
    for kline in raw_klines:
        row = cast(list[int | str], kline)
        klines_data.append(
            cast(
                Kline,
                {
                    "open_time": int(row[0]),
                    "open": str(row[1]),
                    "high": str(row[2]),
                    "low": str(row[3]),
                    "close": str(row[4]),
                    "volume": str(row[5]),
                    "close_time": int(row[6]),
                    "quote_asset_volume": str(row[7]),
                    "number_of_trades": int(row[8]),
                    "taker_buy_base_asset_volume": str(row[9]),
                    "taker_buy_quote_asset_volume": str(row[10]),
                },
            )
        )

    return klines_data


def main() -> None:
    """CLI entry to demonstrate fetching klines from the configured client."""
    import sys

    from ibkr_api.common import get_configured_client
    from shared.output_utils import print_json

    client = get_configured_client()
    symbol, interval, limit = _parse_cli_args(sys.argv)

    if limit > 1000:
        logger.warning("⚠️ 限制数量超过1000, 调整为1000")
        limit = 1000

    klines_data = klines(client, symbol, interval, limit)
    result = {
        "symbol": symbol.upper(),
        "interval": interval,
        "count": len(klines_data),
        "data": klines_data[-5:] if len(klines_data) > 5 else klines_data,
    }

    print_json(result)


if __name__ == "__main__":
    main()


def _parse_cli_args(argv: list[str]) -> tuple[str, str, int]:
    """Parse CLI arguments for the demo CLI and provide defaults."""
    if len(argv) < 2:
        logger.info("用法: p get_klines.py SYMBOL [INTERVAL] [LIMIT]")
        logger.info("示例: p get_klines.py ADAUSDC 1h 50")
        raise SystemExit(0)

    symbol = argv[1]
    interval = argv[2] if len(argv) > 2 else "1h"
    limit = int(argv[3]) if len(argv) > 3 else 20
    return symbol, interval, limit
