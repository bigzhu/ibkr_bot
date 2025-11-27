"""
Backtester - Main Executable

This is the main entry point for running backtests.
It parses command-line arguments and kicks off the BacktestEngine.

Usage:
  uv run python -m backtester SYMBOL TIMEFRAME --cash 10000
  uv run python -m backtester ADAUSDC 1h --cash 5000 --start 2024-01-01 --end 2024-03-01
"""

import argparse
import sys
from collections.abc import Callable
from datetime import UTC, datetime

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m backtester` 运行该模块, 无需手动修改 sys.path"
    )

# Import and configure the logger
from loguru import logger

from shared.logger_utils import setup_scheduler_logger

setup_scheduler_logger()

logger.remove()
logger.add(sys.stdout, level="ERROR")

from backtester.engine import BacktestEngine
from backtester.strategy import DemarkStrategy

FALLBACK_PATTERNS: tuple[str, ...] = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y%m%d",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
)


def _parse_time_value(raw_value: str) -> int:
    """Convert CLI time strings into epoch milliseconds."""
    normalized = raw_value.strip()
    if not normalized:
        raise ValueError("empty value")

    epoch_candidate = _parse_epoch_timestamp(normalized)
    if epoch_candidate is not None:
        return epoch_candidate

    iso_candidate = _normalize_iso_candidate(normalized)
    dt = _parse_iso_datetime(iso_candidate)
    if dt is None:
        dt = _parse_fallback_datetime(normalized)
    if dt is None:
        raise ValueError(f"Unsupported datetime format: {raw_value}")

    dt_utc = dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    return int(dt_utc.astimezone(UTC).timestamp() * 1000)


def _parse_epoch_timestamp(value: str) -> int | None:
    """将纯数字字符串解释为秒或毫秒时间戳."""
    if not value.isdigit():
        return None
    timestamp = int(value)
    return timestamp * 1000 if len(value) <= 10 else timestamp


def _normalize_iso_candidate(value: str) -> str:
    """把结尾为Z的 ISO 文本统一转为显式 UTC 偏移."""
    return value[:-1] + "+00:00" if value.endswith("Z") else value


def _parse_iso_datetime(value: str) -> datetime | None:
    """尝试直接解析 ISO8601 字符串."""
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _parse_fallback_datetime(value: str) -> datetime | None:
    """使用常见格式集合尝试解析日期/时间."""
    for pattern in FALLBACK_PATTERNS:
        try:
            dt = datetime.strptime(value, pattern)
            return dt.replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def _build_time_parser(flag_name: str) -> Callable[[str], int | None]:
    """Factory that returns an argparse-compatible parser for time options."""

    def _parser(value: str) -> int | None:
        cleaned = value.strip()
        if not cleaned:
            return None
        try:
            return _parse_time_value(cleaned)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                f"{flag_name} expects ISO-8601, date-only or epoch timestamp (received: {value})."
            ) from exc

    return _parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a backtest for a given strategy.")
    parser.add_argument(
        "symbol",
        help="The trading symbol to backtest (e.g., ADAUSDC).",
    )
    parser.add_argument(
        "timeframe",
        help="The timeframe to backtest (e.g., 1h, 4h).",
    )
    parser.add_argument(
        "--cash",
        type=float,
        default=10_000.0,
        help="Initial cash for the backtest.",
    )
    parser.add_argument(
        "--start",
        type=_build_time_parser("--start"),
        default=None,
        help=(
            "Optional backtest start time. Accepts ISO-8601 (e.g. 2024-01-01T00:00:00Z), "
            "date-only (2024-01-01) or epoch seconds/milliseconds."
        ),
    )
    parser.add_argument(
        "--end",
        type=_build_time_parser("--end"),
        default=None,
        help=(
            "Optional backtest end time. Accepts ISO-8601, date-only or epoch seconds/milliseconds."
        ),
    )
    parser.add_argument(
        "--disable-trading-logs",
        action="store_true",
        help="Skip trading log persistence during backtest (faster, but no log records)",
    )
    return parser


def main() -> None:
    """Parses arguments and runs the backtest."""
    parser = build_parser()
    args = parser.parse_args()

    _validate_time_window(args, parser)
    _log_configuration(args)

    engine = BacktestEngine(
        symbol=args.symbol.upper(),
        timeframe=args.timeframe.lower(),
        strategy_class=DemarkStrategy,
        initial_cash=args.cash,
        start_ts=args.start,
        end_ts=args.end,
        disable_trading_logs=args.disable_trading_logs,
    )
    engine.run()


def _validate_time_window(
    args: argparse.Namespace, parser: argparse.ArgumentParser
) -> None:
    """确保起止时间合法."""
    if args.start and args.end and args.start > args.end:
        parser.error("--start must be earlier than or equal to --end")


def _log_configuration(args: argparse.Namespace) -> None:
    """输出当前回测配置,便于排查."""
    logger.info(
        "Configuring backtest for %s on %s with $%s",
        args.symbol,
        args.timeframe,
        f"{args.cash:,.2f}",
    )
    if args.start or args.end:
        logger.info(
            "Backtest window: start=%s end=%s",
            args.start or "<default>",
            args.end or "<default>",
        )
    if args.disable_trading_logs:
        logger.info("Trading logs: disabled")


if __name__ == "__main__":
    main()
