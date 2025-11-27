"""
订单撮合工具函数模块

提供撮合过程中需要的通用工具函数和计算逻辑
"""

from decimal import Decimal

from loguru import logger

# 手续费率常量
COMMISSION_RATE = Decimal("0.001")  # 0.1%

# 手续费率常量和通用模块已导入,BUY/SELL常量在此模块中不需要

if __name__ == "__main__":
    try:
        from shared.path_utils import ensure_project_root_for_script
    except ImportError:
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from shared.path_utils import ensure_project_root_for_script

    ensure_project_root_for_script(__file__)

# 导入数据模型
from database.models import BinanceFilledOrder


def normalize_decimal_string(value: Decimal) -> str:
    """
    将Decimal值规范化为字符串,避免科学计数法格式

    Args:
        value: Decimal值

    Returns:
        规范化的字符串,科学计数法会被转换为普通格式
    """
    if value == 0:
        return "0"
    # 直接转为字符串,然后检查是否包含科学计数法
    str_value = str(value)
    if "E" in str_value or "e" in str_value:
        # 如果包含科学计数法,使用format格式化为普通格式
        return format(value, "f")
    return str_value


def add_to_buy_pool(
    buy_pool: list[BinanceFilledOrder], buy_order: BinanceFilledOrder
) -> None:
    """
    将BUY订单添加到买单池,按实际成交价格升序排序

    Args:
        buy_pool: 买单池
        buy_order: 买单
    """
    # 插入排序,按实际成交价格升序(最便宜在前)
    buy_price = Decimal(buy_order.average_price)
    insert_index = 0

    for i, pool_order in enumerate(buy_pool):
        pool_price = Decimal(pool_order.average_price)
        if buy_price < pool_price:
            insert_index = i
            break
        insert_index = i + 1

    buy_pool.insert(insert_index, buy_order)


def calculate_match_profit(
    buy_price: Decimal, sell_price: Decimal, match_qty: Decimal
) -> Decimal:
    """计算撮合利润

    Args:
        buy_price: 买入价格
        sell_price: 卖出价格
        match_qty: 撮合数量

    Returns:
        撮合利润
    """
    return (sell_price - buy_price) * match_qty


def update_order_after_match(
    buy_order: BinanceFilledOrder,
    sell_order: BinanceFilledOrder,
    match_qty: Decimal,
    match_profit: Decimal,
) -> None:
    """更新撮合后的订单信息

    Args:
        buy_order: 买单
        sell_order: 卖单
        match_qty: 撮合数量
        match_profit: 撮合利润
    """
    # 更新未撮合数量
    buy_order.unmatched_qty = normalize_decimal_string(
        Decimal(buy_order.unmatched_qty) - match_qty
    )
    sell_order.unmatched_qty = normalize_decimal_string(
        Decimal(sell_order.unmatched_qty) - match_qty
    )

    # 更新SELL订单的利润(交易闭环完成时记录)
    sell_order.profit = normalize_decimal_string(
        Decimal(sell_order.profit) + match_profit
    )

    logger.debug(
        f"📊 撮合完成 - BUY剩余:{buy_order.unmatched_qty}, SELL剩余:{sell_order.unmatched_qty}, 利润:{match_profit}"
    )


if __name__ == "__main__":
    """工具函数测试"""
    logger.info("🔧 订单撮合工具函数模块")
    logger.info("提供撮合过程中的通用工具函数:")
    logger.info("- normalize_decimal_string: Decimal字符串规范化")
    logger.info("- add_to_buy_pool: 买单池管理")
    logger.info("- calculate_match_profit: 撮合利润计算")
    logger.info("- update_order_after_match: 订单状态更新")
