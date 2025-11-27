"""订单计算公式模块

计算订单的价格和数量.
"""

from decimal import Decimal

from order_builder.reference_price_manager import (
    _get_highest_unmatched_price,
    _get_lowest_unmatched_price,
    get_locked_balance,
)
from order_filler.profit_lock import calculate_profit_lockable_quantity
from shared.constants import (
    ALWAYS_TRY_BUY_ORDER,
    SELL,
    USE_MIN_LAST_PRICE_FOR_BUY,
)
from shared.types import Kline
from shared.types.order_builder import UnmatchedOrders

# 价格下限除数,用于计算 floor_price
PRICE_FLOOR_DIVISOR = Decimal("2.4")
# 保底价格最小值
MINIMUM_FLOOR_PRICE = Decimal("0.3")


def calculate_order_price(
    side: str,
    demark_klines: list[Kline],
) -> Decimal:
    """计算订单价格

    Args:
        side: 买卖方向 (BUY/SELL)
        demark_klines: DeMark K 线数据

    Returns:
        订单价格
    """
    # 获取订单价格: BUY取高价, SELL取低价
    if side == SELL:
        # return Decimal(str(demark_klines[-1]["low"]))
        return Decimal(str(demark_klines[-1]["open"]))
    else:  # BUY
        # return Decimal(str(demark_klines[-1]["high"]))
        return Decimal(str(demark_klines[-1]["close"]))


def _get_top_price(
    unmatched_orders: UnmatchedOrders,
    demark_klines: list[Kline],
) -> Decimal:
    """获取 BUY 订单的最高参考价格 (top_price)

    优先使用未匹配订单最高价, 若无订单则回退到 K 线高点.

    Args:
        unmatched_orders: 未匹配订单列表
        demark_klines: DeMark K线数据

    Returns:
        Decimal: 最高参考价格
    """
    top_price = _get_highest_unmatched_price(unmatched_orders)
    if top_price is None:
        return Decimal(str(demark_klines[0]["high"]))
    return top_price


def _get_last_price(
    unmatched_orders: UnmatchedOrders,
    demark_klines: list[Kline],
) -> Decimal:
    """获取 BUY 订单的最低参考价格 (last_price)

    根据配置开关决定使用未匹配订单最低价或取其与K线高点的较小值.

    Args:
        unmatched_orders: 未匹配订单列表
        demark_klines: DeMark K线数据

    Returns:
        Decimal: 最低参考价格
    """
    unmatched_last_price = _get_lowest_unmatched_price(unmatched_orders)
    kline_high = Decimal(str(demark_klines[0]["high"]))

    if unmatched_last_price is None:
        return kline_high

    return (
        min(unmatched_last_price, kline_high)
        if USE_MIN_LAST_PRICE_FOR_BUY
        else unmatched_last_price
    )


def _calculate_buy_quantity(
    price: Decimal,
    user_balance: Decimal,
    demark_klines: list[Kline],
    unmatched_orders: UnmatchedOrders,
    symbol: str,
    timeframe: str,
) -> Decimal:
    """计算买入数量 (动态模式)

    根据价格下跌幅度动态调整投入资金.

    Args:
        price: 订单价格
        user_balance: 用户账户余额
        demark_klines: DeMark K线数据
        unmatched_orders: 未匹配订单列表
        symbol: 交易对符号
        timeframe: 时间框架

    Returns:
        Decimal: 计算得到的数量
    """
    # BUY 订单金额计算: 动态模式 - 根据价格下跌幅度动态调整投入资金
    top_price = _get_top_price(unmatched_orders, demark_klines)
    last_price = _get_last_price(unmatched_orders, demark_klines)
    # 预估价格最多跌到 1/PRICE_FLOOR_DIVISOR
    floor_price = max(top_price / PRICE_FLOOR_DIVISOR, MINIMUM_FLOOR_PRICE)

    # 查询被套住的余额,用于计算可用资金
    locked_balance = get_locked_balance(symbol, timeframe)
    all_balance = user_balance + locked_balance

    # 根据下跌幅度均匀分布投入资金
    price_drop = last_price - price
    # 始终尝试下 BUY 单时, 且空仓才能下单
    if ALWAYS_TRY_BUY_ORDER and not unmatched_orders:
        price_drop = abs(price_drop)
    if price_drop < 0:
        raise ValueError(
            f"上次买入价更低: last_price({last_price}) < price({price}) user_balance({user_balance})"
        )
    price_range = top_price - floor_price

    # 避免除以零
    drop_ratio = Decimal("0") if price_range == 0 else price_drop / price_range

    entry_amount = all_balance * drop_ratio

    return entry_amount / price


def calculate_quantity(
    side: str,
    price: Decimal,
    user_balance: Decimal,
    minimum_profit_percentage: Decimal,
    demark_klines: list[Kline],
    unmatched_orders: UnmatchedOrders,
    symbol: str = "",
    timeframe: str = "",
) -> Decimal:
    """计算订单数量 (BUY/SELL)

    Args:
        side: 买卖方向 (BUY/SELL)
        price: 订单价格
        user_balance: 用户账户余额
        minimum_profit_percentage: 最小利润百分比 (SELL 时需要)
        demark_klines: DeMark K线数据
        unmatched_orders: 未匹配订单列表
        symbol: 交易对符号 (SELL 时或 BUY 动态模式时需要)
        timeframe: 时间框架 (SELL 时需要)

    Returns:
        Decimal: 计算得到的数量

    Raises:
        ValueError: 如果 SELL 订单不满足盈利要求
    """
    if side == SELL:
        # 计算满足盈利要求的卖出数量
        qty = calculate_profit_lockable_quantity(
            pair=symbol,
            current_price=price,
            min_profit_percentage=minimum_profit_percentage,
            timeframe=timeframe,
        )
        if qty <= 0:
            raise ValueError(
                f"以价格 {price} 卖出不满足 {minimum_profit_percentage}% 的盈利要求"
            )
        return qty

    return _calculate_buy_quantity(
        price=price,
        user_balance=user_balance,
        demark_klines=demark_klines,
        unmatched_orders=unmatched_orders,
        symbol=symbol,
        timeframe=timeframe,
    )


def calculate_buy_quantity_standalone(
    price: Decimal,
    user_balance: Decimal,
    top_price: Decimal,
    last_price: Decimal,
    locked_balance: Decimal,
) -> tuple[Decimal, dict[str, Decimal]]:
    """独立计算 BUY 数量(用于测试和调试)

    Args:
        price: 当前订单价格
        user_balance: 用户可用余额
        top_price: 最高价格(持仓最高价)
        last_price: 最近价格(持仓最低价)
        locked_balance: 被套住的余额

    Returns:
        tuple[Decimal, dict]: (buy_quantity, 计算过程详情)
    """
    floor_price = max(top_price / PRICE_FLOOR_DIVISOR, MINIMUM_FLOOR_PRICE)
    all_balance = user_balance + locked_balance

    price_drop = last_price - price
    if price_drop < 0:
        raise ValueError(
            f"价格下跌计算错误: last_price ({last_price}) 小于 price ({price})"
        )
    price_range = top_price - floor_price

    # 避免除以零
    drop_ratio = Decimal("0") if price_range == 0 else price_drop / price_range

    entry_amount = all_balance * drop_ratio
    buy_quantity = entry_amount / price

    # 返回详细信息用于调试
    details = {
        "floor_price": floor_price,
        "all_balance": all_balance,
        "price_drop": price_drop,
        "price_range": price_range,
        "drop_ratio": drop_ratio,
        "entry_amount": entry_amount,
    }

    return buy_quantity, details


if __name__ == "__main__":
    print("=== BUY 数量计算器 ===\n")

    # 输入参数
    try:
        price = Decimal(input("当前订单价格 (price): "))
        user_balance = Decimal(input("用户可用余额 (user_balance): "))
        top_price = Decimal(input("最高价格 (top_price): "))
        last_price = Decimal(input("最近价格 (last_price): "))
        locked_balance = Decimal(input("被套余额 (locked_balance): "))

        print("\n--- 计算中 ---\n")

        qty, details = calculate_buy_quantity_standalone(
            price, user_balance, top_price, last_price, locked_balance
        )

        print("=== 计算结果 ===")
        print(f"BUY 数量: {qty}")
        print("\n=== 计算过程 ===")
        print(f"底部价格 (floor_price): {details['floor_price']}")
        print(f"总余额 (all_balance): {details['all_balance']}")
        print(f"价格下跌 (price_drop): {details['price_drop']}")
        print(f"价格区间 (price_range): {details['price_range']}")
        print(f"下跌比例 (drop_ratio): {details['drop_ratio']}")
        print(f"投入金额 (entry_amount): {details['entry_amount']}")

    except ValueError as e:
        print(f"\n❌ 输入错误: {e}")
    except Exception as e:
        print(f"\n❌ 计算错误: {e}")
