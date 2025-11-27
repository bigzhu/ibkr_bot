"""TD IVEN 指标业务封装模块

负责从币安获取 K 线数据并调用纯计算函数, 使用方式与 indicators.demark 对齐.
"""

from __future__ import annotations

import sys

from loguru import logger

if __name__ == "__main__":
    try:
        from shared.path_utils import ensure_project_root_for_script
    except ImportError:
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from shared.path_utils import ensure_project_root_for_script

    ensure_project_root_for_script(__file__)

from binance_api.common import get_configured_client
from binance_api.get_klines import klines
from indicators.td_iven.td_iven import MIN_REQUIRED_KLINES, td_iven
from shared.types import Kline


def td_iven_with_binance_api(
    symbol: str,
    timeframe: str,
    *,
    limit: int = 60,
    include_unfinished: bool = False,
) -> tuple[str, int, int, list[Kline]]:
    """通过币安 API 获取 K 线并计算 TD IVEN 信号."""

    required_limit = (
        MIN_REQUIRED_KLINES if include_unfinished else MIN_REQUIRED_KLINES + 1
    )
    effective_limit = max(limit, required_limit)

    client = get_configured_client()
    klines_raw = klines(client, symbol, timeframe, limit=effective_limit)

    if not klines_raw:
        raise ValueError(f"无法获取 {symbol} {timeframe} 的K线数据")

    klines_ready = klines_raw if include_unfinished else klines_raw[:-1]
    if len(klines_ready) < MIN_REQUIRED_KLINES:
        raise ValueError(
            f"K线数量不足, 需要至少{MIN_REQUIRED_KLINES}根完成K线, 实际{len(klines_ready)}根"
        )

    side, setup, countdown = td_iven(klines_ready)
    logger.info(
        f"TD IVEN {symbol} {timeframe} -> side={side} setup={setup} countdown={countdown}"
    )
    return side, setup, countdown, klines_ready


if __name__ == "__main__":
    logger.info("请通过 `p -m indicators.td_iven SYMBOL TIMEFRAME` 调用该模块")
