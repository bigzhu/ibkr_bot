"""order_builder 应用服务层

采用 orchestrator 模式:
- Orchestrator 函数: 编排业务流程,进行异常处理和结果转换

职责分离:
1. _sync_and_cleanup_orders() - 同步撮合和清理订单数据
2. run_order_builder() - 编排主流程: 获取信号,风险检查,执行订单,异常处理
"""

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m order_builder.app` 运行该模块, 无需手动修改 sys.path"
    )


import time
from decimal import Decimal

from loguru import logger

from database.crud import (
    get_symbol_info,
    get_symbol_timeframe_config,
    update_trading_log,
)
from database.models import (
    SymbolTimeframeConfig,
    TradingSymbol,
)
from database.trading_log_crud import (
    check_kline_already_processed,
)
from indicators.demark.binance_demark import demark_with_ibkr_api
from order_builder.balance_manager import get_user_balance
from order_builder.calculation import calculate_qty
from order_builder.opposite_order_handler import cancel_opposite_open_orders
from order_builder.order.execution import execute_order
from order_builder.order.query import get_open_orders_by_symbol_timeframe
from order_builder.trading_logger import TradingLogContext
from order_builder.unmatched_dust_handler import reset_unmatched_qty_to_zero
from order_builder.unmatched_orders import count_effective_unmatched_orders
from order_checker.__main__ import check
from order_checker.common import get_unmatched_buy_orders_by_timeframe
from order_filler.workflows import sync_and_match_orders
from shared import constants as shared_constants
from shared.constants import BUY, SELL
from shared.types import Kline
from shared.types.order_builder import (
    ErrorResult,
    KlineAlreadyProcessedResult,
    NoSignalResult,
    OrderPlacedResult,
    RunResult,
    UnmatchedOrders,
)


def _sync_and_cleanup_orders(
    symbol: str,
    timeframe: str,
    min_notional: Decimal,
) -> UnmatchedOrders:
    """同步和清理订单数据

    包括: 同步撮合,清理残留数量.

    Args:
        symbol: 交易对符号
        timeframe: 时间框架
        min_notional: 最小名义价值

    Returns:
        清理后的未匹配订单

    Raises:
        ValueError: 如果数据获取或计算失败
    """
    # 同步和撮合订单
    sync_and_match_orders(symbol, timeframe)

    # 获取未匹配订单
    unmatched_orders = get_unmatched_buy_orders_by_timeframe(symbol, timeframe)

    # 清理min_notional以下的残留数量
    dust_candidates = _collect_sub_minimal_unmatched(unmatched_orders, min_notional)
    if dust_candidates:
        reset_unmatched_qty_to_zero(
            symbol,
            timeframe,
            min_notional,
            unmatched_orders,
            candidates_override=dust_candidates,
        )
        # 重新获取清理后的未匹配订单
        unmatched_orders = get_unmatched_buy_orders_by_timeframe(symbol, timeframe)

    return unmatched_orders


def _get_symbol_context(
    symbol: str, timeframe: str
) -> tuple[SymbolTimeframeConfig, TradingSymbol, Decimal]:
    """获取配置和信息,并执行延迟等待"""
    symbol_config = get_symbol_timeframe_config(symbol, timeframe)
    symbol_info = get_symbol_info(symbol)
    min_notional = Decimal(symbol_info.min_notional)

    time.sleep(float(symbol_config.monitor_delay))
    return symbol_config, symbol_info, min_notional


def _check_signal_validity(
    symbol: str, timeframe: str, demark_value: int, signal_klines: list[Kline]
) -> KlineAlreadyProcessedResult | None:
    """检查信号K线是否已处理"""
    kline_time = int(signal_klines[-1]["open_time"])
    if check_kline_already_processed(symbol, timeframe, kline_time):
        return KlineAlreadyProcessedResult(
            action="KLINE_ALREADY_PROCESSED",
            symbol=symbol,
            timeframe=timeframe,
            signal_value=demark_value,
            reason="该 K线已处理过",
        )
    return None


def _prepare_order_context(
    symbol: str, timeframe: str, side: str, min_notional: Decimal
) -> tuple[UnmatchedOrders, int]:
    """准备订单上下文: 取消反向单,同步数据"""
    if shared_constants.CANCEL_OPPOSITE_OPEN_ORDERS_AFTER_SIGNAL:
        logger.info("取消反方向挂单: {}-{}, 当前方向={}", symbol, timeframe, side)
        cancel_opposite_open_orders(symbol, side)

    unmatched_orders = _sync_and_cleanup_orders(symbol, timeframe, min_notional)
    effective_unmatched_count = count_effective_unmatched_orders(
        unmatched_orders, min_notional
    )
    return unmatched_orders, effective_unmatched_count


def _process_trade_execution(
    symbol: str,
    timeframe: str,
    side: str,
    demark_value: int,
    signal_klines: list[Kline],
    symbol_config: SymbolTimeframeConfig,
    symbol_info: TradingSymbol,
    min_notional: Decimal,
    unmatched_orders: UnmatchedOrders,
) -> OrderPlacedResult | ErrorResult:
    """执行交易流程: 计算,检查,下单

    TradingLogContext 会消化业务异常(ValueError, BinanceAPIException),
    避免传播到调度器层级
    """
    context = TradingLogContext(symbol, timeframe, side, demark_value, signal_klines)
    with context as log_id:
        user_balance = get_user_balance(symbol, side, symbol_info)

        qty, price = calculate_qty(
            side,
            signal_klines,
            symbol_config,
            symbol_info,
            unmatched_orders,
            user_balance,
            symbol=symbol,
            timeframe=timeframe,
        )

        update_trading_log(
            log_id=log_id,
            qty=float(qty),
            price=float(price),
            user_balance=float(user_balance),
        )

        open_orders = get_open_orders_by_symbol_timeframe(symbol, timeframe)
        check(
            symbol,
            timeframe,
            side,
            demark_value,
            qty,
            price,
            symbol_info,
            min_notional,
            open_orders,
        )

        order_id = execute_order(
            symbol,
            side,
            qty,
            price,
            timeframe,
            log_id,
            open_orders,
        )

        return OrderPlacedResult(
            action="ORDER_PLACED",
            symbol=symbol,
            timeframe=timeframe,
            signal_value=demark_value,
            qty=float(qty),
            price=float(price),
            order_id=order_id,
        )

    # 执行到这里说明业务异常被 TradingLogContext 消化了
    return ErrorResult(
        action="ERROR",
        symbol=symbol,
        timeframe=timeframe,
        signal_value=demark_value,
        error=context.error or "Unknown error",
    )


def run_order_builder(symbol: str, timeframe: str) -> RunResult:
    """编排主流程(Orchestrator)

    协调各个use case函数,进行异常处理和结果转换.
    """
    symbol_config, symbol_info, min_notional = _get_symbol_context(symbol, timeframe)

    side, demark_value, _, signal_klines = demark_with_ibkr_api(symbol, timeframe)

    if side == "NONE":
        return NoSignalResult(
            action="NO_SIGNAL",
            symbol=symbol,
            timeframe=timeframe,
            signal_value=0,
        )

    if result := _check_signal_validity(symbol, timeframe, demark_value, signal_klines):
        return result

    unmatched_orders, effective_unmatched_count = _prepare_order_context(
        symbol, timeframe, side, min_notional
    )
    # SELL 信号额外下 BUY 单: 先下 BUY 单(无论是否有持仓)
    if side == SELL and shared_constants.ALWAYS_TRY_BUY_ORDER:
        try:
            _process_trade_execution(
                symbol,
                timeframe,
                BUY,
                demark_value,
                signal_klines,
                symbol_config,
                symbol_info,
                min_notional,
                unmatched_orders,
            )
        except Exception as e:
            logger.error(f"❌ BUY 单下单失败: {e}")

    if side == SELL and effective_unmatched_count == 0:
        return KlineAlreadyProcessedResult(
            action="KLINE_ALREADY_PROCESSED",
            symbol=symbol,
            timeframe=timeframe,
            signal_value=demark_value,
            reason="SELL 信号但无持仓可卖出",
        )

    result = _process_trade_execution(
        symbol,
        timeframe,
        side,
        demark_value,
        signal_klines,
        symbol_config,
        symbol_info,
        min_notional,
        unmatched_orders,
    )

    return result


def _collect_sub_minimal_unmatched(
    unmatched_orders: UnmatchedOrders, min_notional: Decimal
) -> list[tuple[str, Decimal]]:
    """Return list of (order_no, qty) whose notional falls below the minimum amount."""
    candidates: list[tuple[str, Decimal]] = []
    for order in unmatched_orders:
        qty = Decimal(str(getattr(order, "unmatched_qty", "0")))
        price = Decimal(str(getattr(order, "average_price", "0")))
        if qty <= 0 or price <= 0:
            continue
        notional = qty * price
        if 0 < notional < min_notional:
            candidates.append((str(getattr(order, "order_no", "")), qty))
    return [c for c in candidates if c[0]]


# 仅在脚本直跑时注入项目根路径
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="运行订单构建器 - 处理指定交易对的 DeMark 信号",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  p -m order_builder.app ADAUSDC 15m
  p -m order_builder.app BTCUSDC 1h
        """,
    )
    parser.add_argument("symbol", type=str, help="交易对符号 (例如: ADAUSDC, BTCUSDC)")
    parser.add_argument(
        "timeframe",
        type=str,
        help="时间框架 (例如: 15m, 1h, 4h)",
    )

    args = parser.parse_args()

    logger.info(f"🚀 开始运行订单构建器: {args.symbol} {args.timeframe}")
    result = run_order_builder(args.symbol, args.timeframe)
    logger.info(f"✅ 订单构建结果: {result}")
