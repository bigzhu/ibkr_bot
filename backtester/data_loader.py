"""Backtester Data Loader."""

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m backtester.data_loader` 运行该模块, 无需手动修改 sys.path"
    )

import pandas as pd
from loguru import logger

from database.db_config import get_db_manager


def load_klines_to_dataframe(
    symbol: str,
    timeframe: str,
    start_ts: int | None = None,
    end_ts: int | None = None,
) -> pd.DataFrame:
    """
    Loads K-line data for a given symbol and timeframe from the database
    into a pandas DataFrame.

    Args:
        symbol: The trading symbol (e.g., 'BTCUSDT').
        timeframe: The K-line interval (e.g., '1h').
        start_ts: Optional start timestamp (Unix milliseconds).
        end_ts: Optional end timestamp (Unix milliseconds).

    Returns:
        A pandas DataFrame containing the K-line data, with a DatetimeIndex.
        Returns an empty DataFrame if no data is found.
    """
    logger.info(f"Loading klines for {symbol} {timeframe} from database...")
    db_manager = get_db_manager()

    query = "SELECT * FROM backtest_klines WHERE symbol = ? AND timeframe = ?"
    params = [symbol, timeframe]

    if start_ts:
        query += " AND open_time >= ?"
        params.append(start_ts)
    if end_ts:
        query += " AND open_time <= ?"
        params.append(end_ts)

    query += " ORDER BY open_time ASC"

    with db_manager.get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if df.empty:
        logger.warning(f"No data found for {symbol} {timeframe} in the database.")
        return df

    # --- Data Cleaning and Preparation ---
    # Convert timestamp columns to datetime objects (UTC)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)

    # Convert price and volume columns to numeric types
    numeric_cols = [
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "quote_asset_volume",
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume",
    ]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

    # Set the datetime index
    df.set_index("open_time", inplace=True)

    # Rename columns for better access, e.g., df.open
    df.rename(
        columns={
            "open_price": "open",
            "high_price": "high",
            "low_price": "low",
            "close_price": "close",
        },
        inplace=True,
    )

    logger.success(f"Successfully loaded {len(df)} klines for {symbol} {timeframe}.")
    return df


if __name__ == "__main__":
    # Example of how to use the data loader
    # Ensure you have synced data first by running klines_syncer.py
    ada_1h_df = load_klines_to_dataframe("ADAUSDC", "1m")

    if not ada_1h_df.empty:
        logger.info("Successfully loaded ADAUSDC 1m data:")
        logger.info(f"Data range: {ada_1h_df.index.min()} to {ada_1h_df.index.max()}")
        logger.info("Last 5 rows:")
        print(ada_1h_df.tail())
        logger.info("\nDataFrame Info:")
        ada_1h_df.info()
