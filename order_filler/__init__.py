"""
币安已成交订单模块
提供CSV导入,订单同步,订单撮合,利润计算等完整功能
遵循CLAUDE.md规范
"""

from loguru import logger

from database.models import BinanceFilledOrder, CSVImportStats, MatchingStats
from order_filler.csv_importer import BinanceCSVImporter, import_binance_csv
from order_filler.data_access import get_today_unmatched_buy_orders_total
from order_filler.matching import match_orders
from order_filler.profit_lock import calculate_profit_lockable_quantity
from order_filler.sync import sync_orders_for_pair
from order_filler.workflows import sync_and_match_orders

__all__ = [
    "BinanceCSVImporter",
    "BinanceFilledOrder",
    "CSVImportStats",
    "MatchingStats",
    "calculate_profit_lockable_quantity",
    "get_today_unmatched_buy_orders_total",
    "import_binance_csv",
    "match_orders",
    "sync_and_match_orders",
    "sync_orders_for_pair",
]


def main() -> None:
    """演示模块功能"""
    logger.info("币安已成交订单模块 (order_filler)")
    logger.info("支持CSV导入,API同步,订单撮合,利润锁定等功能")
    logger.info("详细用法请查看模块文档")


if __name__ == "__main__":
    main()
