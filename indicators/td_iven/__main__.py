"""TD IVEN 命令行入口

提供 `p -m indicators.td_iven SYMBOL TIMEFRAME [MODE]` 形式的使用方式.
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from indicators.td_iven.binance_td_iven import td_iven_with_ibkr_api


def _display_usage() -> None:
    logger.info("TD IVEN 指标命令行工具")
    logger.info("用法: p -m indicators.td_iven SYMBOL TIMEFRAME")


def _parse_args(argv: list[str]) -> tuple[str, str]:
    if len(argv) < 3:
        _display_usage()
        raise SystemExit(0)

    symbol = argv[1].upper()
    timeframe = argv[2]
    return symbol, timeframe


def main() -> None:
    try:
        symbol, timeframe = _parse_args(sys.argv)
    except SystemExit as exc:
        if exc.code not in (0, None):
            logger.error(exc)
            sys.exit(1)
        return

    side, setup, countdown, _ = td_iven_with_ibkr_api(
        symbol, timeframe, include_unfinished=False
    )

    logger.info(f"TD IVEN 结果 ({symbol} {timeframe})")
    logger.info(f"side={side} setup={setup} countdown={countdown}")


if __name__ == "__main__":
    main()
