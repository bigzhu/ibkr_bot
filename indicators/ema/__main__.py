"""EMA模块命令行入口

提供EMA指标的命令行调用接口
遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except
"""

import sys

from loguru import logger

try:
    from shared.path_utils import ensure_project_root_for_script
except ImportError:
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from shared.path_utils import ensure_project_root_for_script

ensure_project_root_for_script(__file__)

from indicators.ema.binance_ema import ema_with_ibkr_api


def display_usage() -> None:
    logger.info("用法: python -m ema SYMBOL TIMEFRAME [PERIOD] [PRICE_FIELD]")
    logger.info("示例: python -m ema BTCUSDT 1h 20 close")


def parse_cli_args(argv: list[str]) -> tuple[str, str, int, str]:
    if len(argv) < 3:
        display_usage()
        raise SystemExit(1)
    symbol = argv[1].upper()
    timeframe = argv[2]
    period = int(argv[3]) if len(argv) >= 4 else 20
    price_field = argv[4] if len(argv) >= 5 else "close"
    return symbol, timeframe, period, price_field


def _display_result(
    symbol: str, timeframe: str, period: int, price_field: str, ema_value: float
) -> None:
    """Pretty-print EMA results and brief interpretation."""
    logger.info("=" * 50)
    logger.info(f"📊 {symbol} {timeframe} EMA({period})[{price_field}] 分析结果:")
    logger.info(f"💹 EMA值: {ema_value:.6f}")
    logger.info("")
    logger.info(
        "💡 解读: EMA向上且价格位于EMA上方 → 多头, 向下且价格位于下方 → 空头; 缠绕走平 → 震荡"
    )
    logger.info("=" * 50)


def main() -> None:
    symbol, timeframe, period, price_field = parse_cli_args(sys.argv)
    ema_value = ema_with_ibkr_api(symbol, timeframe, period, price_field)
    _display_result(symbol, timeframe, period, price_field, float(ema_value))


if __name__ == "__main__":
    main()
