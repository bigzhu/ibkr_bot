"""order_builder 信号检查逻辑

实现 DeMark 信号验证和交易日志记录.
遵循 fail-fast 原则, 异常直接向上传播.
"""

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m order_checker.signal_validation` 运行该模块, 无需手动修改 sys.path"
    )


from loguru import logger

from database.crud import get_symbol_timeframe_config
from shared.constants import BUY

__all__ = [
    "check_demark",
]


def main() -> None:
    """信号验证模块"""
    logger.info("信号验证检查器模块")
    logger.info("主要功能:")
    logger.info("- check_demark(): 检查交易信号是否满足条件")
    logger.info("请通过其他模块调用相关功能")


def check_demark(
    symbol: str, timeframe: str, signal_type: str, signal_value: int
) -> None:
    """检查信号是否满足交易条件 (遵循 fail-fast 原则)

    用于在计算完订单数量后, 最终确认是否执行交易
    信号不满足要求时直接抛出异常, 保护资金安全

    Args:
        symbol: 交易对符号
        timeframe: 时间周期
        signal_type: 信号类型
        signal_value: 信号值

    Raises:
        ValueError: 信号不满足交易条件时抛出异常
    """
    logger.debug(f"🔍 信号检查: {symbol} {timeframe} {signal_type}({signal_value})")

    # 获取配置
    config = get_symbol_timeframe_config(symbol, timeframe)

    # 根据信号类型选择对应的阈值
    min_signal_value = config.demark_buy if signal_type == BUY else config.demark_sell

    # 检查信号强度是否满足要求
    if signal_value < min_signal_value:
        # error_msg = f"{signal_type}信号不足: {signal_value} < {min_signal_value}"
        error_msg = f"{signal_value} < {min_signal_value}"
        # 业务性中断: 降为 INFO, 避免控制台噪声
        logger.info(f"业务中断: {error_msg}")
        raise ValueError(error_msg)

    logger.debug(
        f"✅ 信号检查通过: {symbol} {timeframe} {signal_type}({signal_value}) >= {min_signal_value}"
    )


if __name__ == "__main__":
    main()
