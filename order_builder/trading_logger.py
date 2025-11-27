"""交易日志记录模块

专门处理交易日志的创建和记录.
遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except
"""

import time
from decimal import Decimal
from types import TracebackType
from typing import cast

from binance.exceptions import BinanceAPIException
from loguru import logger

from database import TradingLog
from database.crud import create_trading_log, update_trading_log
from shared.types import Kline


def _extract_kline_prices(
    kline: Kline | None,
) -> tuple[float | None, float | None, float | None, float | None]:
    """提取K线的开高低收价格并转换为float,异常时返回None"""

    if not kline:
        return None, None, None, None

    try:
        open_price = float(kline["open"])
        high_price = float(kline["high"])
        low_price = float(kline["low"])
        close_price = float(kline["close"])
        return open_price, high_price, low_price, close_price
    except (KeyError, TypeError, ValueError):
        return None, None, None, None


__all__ = [
    "TradingLogContext",
    "create_error_trading_log_record",
    "create_preliminary_trading_log_record",
    "create_trading_log_record",
]


class TradingLogContext:
    """交易日志上下文管理器

    负责交易日志的生命周期管理:
    1. 进入时创建初始日志记录
    2. 退出时如果有异常,记录错误信息
    3. 业务异常(ValueError, BinanceAPIException)被消化,不继续传播
    4. 系统异常继续传播,遵循 fail-fast 原则
    """

    def __init__(
        self,
        symbol: str,
        timeframe: str,
        side: str,
        demark_value: int,
        signal_klines: list[Kline],
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self.side = side
        self.demark_value = demark_value
        self.signal_klines = signal_klines
        self.log_id: int | None = None
        self.error: str | None = None

    def __enter__(self) -> int:
        self.log_id = create_preliminary_trading_log_record(
            self.symbol,
            self.timeframe,
            self.side,
            self.demark_value,
            self.signal_klines,
        )
        return self.log_id

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if exc_val and self.log_id:
            error_msg = str(exc_val)
            self.error = error_msg
            update_trading_log(log_id=self.log_id, error=error_msg)

            # 业务异常: 消化异常,不继续传播
            if isinstance(exc_val, ValueError | BinanceAPIException):
                return True

            # 系统异常: 记录日志,让异常继续传播
            logger.error(f"❌ 交易执行出错, 更新日志 ID {self.log_id}: {exc_val}")
            return False

        return False


def create_trading_log_record(
    symbol: str,
    timeframe: str,
    side: str,
    demark_value: int,
    demark_klines: list[Kline],
    from_price: Decimal,
    order_price: Decimal,
    user_balance: Decimal,
    qty: Decimal,
    price_change_percentage: Decimal,
) -> int:
    """创建交易日志记录

    创建包含完整计算结果的交易日志记录.

    Args:
        symbol: 交易对符号
        timeframe: 时间周期
        side: 信号类型(BUY/SELL)
        demark_value: DeMark信号值
        demark_klines: DeMark 序列 K 线数据
        demark_klines: DeMark 序列 K 线数据
        from_price: 基准价格
        order_price: 订单价格
        user_balance: 用户余额
        qty: 订单数量
        price_change_percentage: 价格变化百分比

    Returns:
        int: 创建的交易日志记录ID

    Raises:
        Exception: 创建失败时抛出异常
    """
    current_time = int(time.time() * 1000)  # Unix毫秒时间戳

    # 获取当前信号K线的时间 (使用最新的K线时间)
    latest_kline = demark_klines[-1]  # 最新的K线 (当前信号K线)
    kline_time = int(latest_kline["open_time"])
    open_price, high_price, low_price, close_price = _extract_kline_prices(latest_kline)

    trading_log = TradingLog(
        symbol=symbol,
        kline_timeframe=timeframe,
        demark=demark_value,
        side=side,
        from_price=float(from_price),
        price=float(order_price),
        user_balance=float(user_balance),
        qty=float(qty),
        price_change_percentage=float(price_change_percentage),
        open=open_price,
        high=high_price,
        low=low_price,
        close=close_price,
        kline_time=kline_time,
        run_time=current_time,
        error=None,
    )

    trading_log_id = create_trading_log(trading_log)
    return trading_log_id


def create_error_trading_log_record(
    symbol: str,
    timeframe: str,
    side: str,
    error_message: str,
    demark_value: int | None = None,
) -> int:
    """创建错误交易日志记录

    当交易计算过程中出现错误时,创建包含错误信息的日志记录.

    Args:
        symbol: 交易对符号
        timeframe: 时间周期
        side: 信号类型(BUY/SELL)
        error_message: 错误信息
        demark_value: DeMark信号值(可选)

    Returns:
        int: 创建的交易日志记录ID

    Raises:
        Exception: 创建失败时抛出异常
    """
    current_time = int(time.time() * 1000)  # Unix毫秒时间戳

    trading_log = TradingLog(
        symbol=symbol,
        kline_timeframe=timeframe,
        demark=demark_value or 0,
        side=side,
        from_price=0.0,
        price=0.0,
        user_balance=0.0,
        qty=0.0,
        price_change_percentage=0.0,
        kline_time=0,
        run_time=current_time,
        error=error_message,
    )

    trading_log_id = create_trading_log(trading_log)
    logger.warning(
        f"📝 已创建错误交易日志记录 ID: {trading_log_id}, 错误: {error_message}"
    )

    return trading_log_id


def create_preliminary_trading_log_record(
    symbol: str,
    timeframe: str,
    side: str,
    demark_value: int,
    demark_klines: list[Kline],
) -> int:
    """创建初始交易日志记录

    用于预生成日志记录,后续通过update_trading_log更新完整信息.
    初始记录不包含错误信息,所有计算字段设为0,但记录正确的kline_time.

    Args:
        symbol: 交易对符号
        timeframe: 时间周期
        side: 信号类型(BUY/SELL)
        demark_value: DeMark信号值
        demark_klines: DeMark 序列 K 线数据

    Returns:
        int: 创建的交易日志记录ID

    Raises:
        Exception: 创建失败时抛出异常
    """
    current_time = int(time.time() * 1000)  # Unix毫秒时间戳

    # 获取当前信号K线的时间 (使用最新的K线时间)
    latest_kline = demark_klines[-1]  # 最新的K线 (当前信号K线)
    kline_time = int(latest_kline["open_time"])
    open_price, high_price, low_price, close_price = _extract_kline_prices(latest_kline)

    trading_log = TradingLog(
        symbol=symbol,
        kline_timeframe=timeframe,
        demark=demark_value,
        side=side,
        open=open_price,
        high=high_price,
        low=low_price,
        close=close_price,
        kline_time=kline_time,  # 记录正确的K线时间
        run_time=current_time,
    )

    trading_log_id = create_trading_log(trading_log)
    logger.info(f"📝 已创建初始交易日志记录 ID: {trading_log_id}")

    return trading_log_id


if __name__ == "__main__":
    """测试交易日志记录功能"""
    from decimal import Decimal

    # 模拟测试数据
    test_symbol = "ADAUSDC"
    test_timeframe = "1m"
    test_side = "BUY"
    test_demark_value = 9
    test_demark_klines: list[Kline] = [
        cast(
            Kline,
            {
                "open_time": 1640995200000,
                "open": "47000",
                "high": "48000",
                "low": "46900",
                "close": "47800",
                "volume": "100.5",
                "close_time": 1640995260000,
                "quote_asset_volume": "100.5",
                "number_of_trades": 10,
                "taker_buy_base_asset_volume": "50.1",
                "taker_buy_quote_asset_volume": "50.1",
            },
        )
    ]
    test_from_price = Decimal("47000")
    test_order_price = Decimal("47800")
    test_balance = Decimal("1000")
    test_quantity = Decimal("0.021")
    test_price_change = Decimal("1.70")

    # 测试 Context Manager
    logger.info("🧪 测试 Context Manager (正常流程)")
    with TradingLogContext(
        test_symbol, test_timeframe, test_side, test_demark_value, test_demark_klines
    ) as log_id:
        logger.info(f"  Context Manager 创建了 ID: {log_id}")
        # 模拟正常更新
        update_trading_log(log_id=log_id, qty=1.0, price=100.0)

    logger.info("🧪 测试 Context Manager (异常流程)")
    try:
        with TradingLogContext(
            test_symbol,
            test_timeframe,
            test_side,
            test_demark_value,
            test_demark_klines,
        ) as log_id:
            logger.info(f"  Context Manager 创建了 ID: {log_id}")
            raise ValueError("模拟的业务异常")
    except ValueError:
        logger.info("  ✅ 捕获到了预期的异常")
