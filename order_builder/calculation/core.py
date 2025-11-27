"""订单计算核心模块

编排价格指标和数量计算,作为主入口.
"""

from decimal import Decimal

from loguru import logger

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m order_builder.calculation.core` 运行该模块, 无需手动修改 sys.path"
    )

from database.models import SymbolTimeframeConfig, TradingSymbol
from order_builder.calculation.formulas import (
    calculate_order_price,
    calculate_quantity,
)
from order_builder.precision_handler import adjust_order_precision
from shared.types import Kline
from shared.types.order_builder import UnmatchedOrders


def calculate_qty(
    side: str,
    demark_klines: list[Kline],
    symbol_timeframe_config: SymbolTimeframeConfig,
    symbol_info: TradingSymbol,
    unmatched_orders: UnmatchedOrders,
    user_balance: Decimal,
    symbol: str = "",
    timeframe: str = "",
) -> tuple[Decimal, Decimal]:
    """计算订单数量和价格(纯计算,无副作用)

    根据 DeMark 信号计算订单的数量和入场价格.
    此函数是纯函数,无副作用,便于测试和组合.

    Args:
        side: 买卖方向 (BUY/SELL)
        demark_klines: DeMark K 线数据
        symbol_timeframe_config: 交易对配置
        symbol_info: 交易对信息
        unmatched_orders: 未匹配订单列表
        user_balance: 用户账户余额
        symbol: 交易对符号 (SELL 时需要)
        timeframe: 时间框架 (SELL 时需要)

    Returns:
        (订单数量, 订单价格)

    Raises:
        ValueError: 如果参数验证失败或计算异常
    """
    # 计算价格
    price = calculate_order_price(
        side=side,
        demark_klines=demark_klines,
    )

    # 计算数量
    qty = calculate_quantity(
        side,
        price,
        user_balance,
        Decimal(str(symbol_timeframe_config.minimum_profit_percentage)),
        demark_klines=demark_klines,
        unmatched_orders=unmatched_orders,
        symbol=symbol,
        timeframe=timeframe,
    )

    qty, price = adjust_order_precision(qty, price, symbol_info)

    return qty, price


if __name__ == "__main__":
    """测试订单计算功能"""
    if len(__import__("sys").argv) >= 3:
        import sys

        from database.crud import (
            get_symbol_info,
            get_symbol_timeframe_config,
        )
        from indicators.demark.binance_demark import demark_with_binance_api
        from order_builder.balance_manager import get_user_balance
        from order_checker.common import (
            get_unmatched_buy_orders_by_timeframe,
        )
        from shared.demark_utils import transform_demark_signal

        symbol = sys.argv[1].upper()
        timeframe = sys.argv[2].lower()

        logger.info(f"🧪 测试订单计算: {symbol} {timeframe}")

        try:
            unmatched_orders = get_unmatched_buy_orders_by_timeframe(symbol, timeframe)
            symbol_timeframe_config = get_symbol_timeframe_config(symbol, timeframe)
            symbol_info = get_symbol_info(symbol)

            side, demark_value, is_break, demark_klines = demark_with_binance_api(
                symbol, timeframe
            )
            side, demark_value = transform_demark_signal(
                side, demark_value, len(unmatched_orders)
            )
            logger.info(f"📊 DeMark 信号: {side}({demark_value}) break={is_break}")

            user_balance = get_user_balance(symbol, side, symbol_info)
            quantity, entry_price = calculate_qty(
                side,
                demark_klines,
                symbol_timeframe_config,
                symbol_info,
                unmatched_orders,
                user_balance,
                symbol=symbol,
                timeframe=timeframe,
            )

            logger.info(
                f"✅ 计算结果 - 信号: {side}, 订单数量: {quantity}, 入场价格: {entry_price}"
            )

        except Exception as e:
            logger.error(f"❌ 计算失败: {e}")
    else:
        logger.info("订单计算核心模块")
        logger.info("用法: p order_builder/calculation/core.py SYMBOL TIMEFRAME")
