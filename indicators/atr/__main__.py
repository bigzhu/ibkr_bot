"""ATR模块命令行入口

提供ATR指标的命令行调用接口
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

from indicators.atr.binance_atr import atr_with_ibkr_api


def display_usage() -> None:
    """输出命令行使用说明"""
    logger.info("ATR (Average True Range) 指标计算工具")
    logger.info("")
    logger.info("用法: p -m atr SYMBOL TIMEFRAME [PERIOD]")
    logger.info("")
    logger.info("参数:")
    logger.info("  SYMBOL    交易对符号 (如: ADAUSDC, BTCUSDT)")
    logger.info("  TIMEFRAME 时间周期 (如: 1m, 5m, 15m, 1h, 4h, 1d)")
    logger.info("  PERIOD    ATR周期 (可选, 默认14)")
    logger.info("")
    logger.info("示例:")
    logger.info("  p -m atr ADAUSDC 15m")
    logger.info("  p -m atr BTCUSDT 1h 20")
    logger.info("")
    logger.info("说明:")
    logger.info("  ATR衡量价格波动性,数值越大表示波动越剧烈")
    logger.info("  常用于设置止损位和评估市场风险")


def parse_cli_args(argv: list[str]) -> tuple[str, str, int]:
    """解析命令行参数并返回规范化结果"""
    if len(argv) < 3:
        display_usage()
        raise SystemExit(0)

    symbol = argv[1].upper()
    timeframe = argv[2]
    try:
        period = int(argv[3]) if len(argv) > 3 else 14
    except ValueError as exc:
        raise SystemExit("PERIOD 需为整数") from exc
    return symbol, timeframe, period


def main() -> None:
    """ATR模块主入口函数"""
    try:
        symbol, timeframe, period = parse_cli_args(sys.argv)
    except SystemExit as exc:
        # 参数解析失败时, 已输出提示, 此处仅确保非零 code 显式退出
        if exc.code:
            logger.error(exc)
            sys.exit(1)
        return

    logger.info(f"🚀 开始计算 {symbol} {timeframe} 的ATR({period})指标")

    try:
        atr_value, atr_percentage = atr_with_ibkr_api(symbol, timeframe, period)
    except Exception as exc:
        logger.error(f"❌ ATR计算失败: {exc}")
        sys.exit(1)

    _display_result(symbol, timeframe, period, atr_value, atr_percentage)


if __name__ == "__main__":
    main()


def _display_result(
    symbol: str,
    timeframe: str,
    period: int,
    atr_value: float,
    atr_percentage: float,
) -> None:
    """Pretty-print ATR results and provide a brief interpretation."""
    logger.info("=" * 50)
    logger.info(f"📊 {symbol} {timeframe} ATR({period}) 分析结果:")
    logger.info(f"💹 ATR值: {atr_value:.6f}")
    logger.info(f"📈 ATR百分比: {atr_percentage:.2f}%")
    logger.info("")
    logger.info("💡 解读:")
    if atr_percentage < 1:
        logger.info("  📉 波动性较低,市场相对平静")
    elif atr_percentage < 3:
        logger.info("  📊 波动性适中,正常市场状态")
    else:
        logger.info("  📈 波动性较高,市场活跃或不稳定")
    logger.info("=" * 50)
