"""Backtester K-line Synchronization Tool."""

import argparse
import time
from collections.abc import Sequence
from datetime import datetime
from typing import Any

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m backtester.klines_syncer` 运行该模块, 无需手动修改 sys.path"
    )

from loguru import logger

from binance_api.common import get_configured_client
from database.db_config import get_db_manager

_INSERT_QUERY = """
    INSERT OR IGNORE INTO backtest_klines (
        symbol, timeframe, open_time, open_price, high_price, low_price,
        close_price, volume, close_time, quote_asset_volume, number_of_trades,
        taker_buy_base_asset_volume, taker_buy_quote_asset_volume
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def get_latest_kline_timestamp(symbol: str, timeframe: str) -> int | None:
    """Retrieves the timestamp of the most recent K-line."""
    query = """
        SELECT MAX(open_time) as last_ts
        FROM backtest_klines
        WHERE symbol = ? AND timeframe = ?
    """
    try:
        result = get_db_manager().execute_query(query, (symbol, timeframe))
    except Exception as exc:
        logger.warning(f"Could not retrieve latest kline timestamp: {exc}")
        return None
    if result and result[0]["last_ts"] is not None:
        logger.debug(f"Latest kline for {symbol} {timeframe} at {result[0]['last_ts']}")
        return int(result[0]["last_ts"])
    logger.debug(f"No existing klines found for {symbol} {timeframe}.")
    return None


def save_klines_to_db(klines: Sequence[Sequence[Any]], symbol: str, timeframe: str):
    """Saves a list of K-lines to the `backtest_klines` table."""
    if not klines:
        return
    rows_to_insert = [_build_row(symbol, timeframe, kline) for kline in klines]
    try:
        with get_db_manager().transaction() as conn:
            conn.executemany(_INSERT_QUERY, rows_to_insert)
        logger.debug(
            f"Saved/updated {len(rows_to_insert)} klines for {symbol} {timeframe}."
        )
    except Exception as exc:
        logger.error(f"Failed to save klines to database: {exc}")
        raise


def sync_klines(symbol: str, timeframe: str, start_ts: int):
    """Fetches historical data from Binance and stores it for backtesting."""
    logger.debug(f"Starting backtest kline sync for {symbol} {timeframe}...")
    client = get_configured_client()
    start_time = _determine_start_time(symbol, timeframe, start_ts)
    logger.debug(f"Syncing from timestamp: {start_time}")

    while True:
        try:
            klines = client.get_klines(
                symbol=symbol, interval=timeframe, limit=1000, startTime=start_time
            )
        except Exception as exc:
            logger.error(f"An error occurred during kline sync: {exc}")
            break

        if not klines:
            logger.debug("No more new klines to fetch. Sync complete.")
            break

        save_klines_to_db(klines, symbol, timeframe)
        start_time = _advance_start_time(klines, start_time)
        if start_time is None:
            logger.debug("Start time did not advance. Sync complete.")
            break
        time.sleep(0.5)

    logger.debug(f"Finished backtest kline sync for {symbol} {timeframe}.")


def _build_row(symbol: str, timeframe: str, kline: Sequence[Any]) -> tuple[Any, ...]:
    return (
        symbol,
        timeframe,
        kline[0],
        kline[1],
        kline[2],
        kline[3],
        kline[4],
        kline[5],
        kline[6],
        kline[7],
        kline[8],
        kline[9],
        kline[10],
    )


def _determine_start_time(symbol: str, timeframe: str, requested_start: int) -> int:
    latest_ts_in_db = get_latest_kline_timestamp(symbol, timeframe)
    return max(requested_start, latest_ts_in_db or 0)


def _advance_start_time(
    klines: Sequence[Sequence[Any]],
    previous_start: int,
) -> int | None:
    new_start_time = klines[-1][0]
    if new_start_time == previous_start:
        return None
    return new_start_time


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Backtester K-line Synchronization Tool"
    )
    parser.add_argument("symbol", help="The trading symbol (e.g., ADAUSDC)")
    parser.add_argument("timeframe", help="The K-line interval (e.g., 1m, 1h)")
    parser.add_argument(
        "--months",
        type=int,
        default=12,
        help="Number of past months to sync (default: 12)",
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Start date in ISO format (e.g., 2024-11-01). Overrides --months.",
    )
    args = parser.parse_args()

    # Calculate start timestamp
    if args.start:
        # Use provided start date
        try:
            start_date = datetime.fromisoformat(args.start)
            start_timestamp = int(start_date.timestamp() * 1000)
            logger.info(f"Using provided start date: {args.start}")
        except ValueError as exc:
            logger.error(
                f"Invalid date format: {args.start}. Expected ISO format (e.g., 2024-11-01)"
            )
            raise ValueError(f"Invalid date format: {exc}") from exc
    else:
        # Calculate based on --months argument
        today = datetime.utcnow()
        year = today.year
        month = today.month - args.months
        while month <= 0:
            month += 12
            year -= 1

        # To handle cases like month=2, day=30, we simply start from day 1
        start_date = datetime(year, month, 1)
        start_timestamp = int(start_date.timestamp() * 1000)
        logger.info(f"Syncing {args.months} months from {start_date.date()}")

    sync_klines(args.symbol.upper(), args.timeframe.lower(), start_timestamp)
