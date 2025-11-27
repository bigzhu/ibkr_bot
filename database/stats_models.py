"""
统计信息相关数据模型

定义各种操作的统计信息Pydantic模型
"""

from loguru import logger
from pydantic import BaseModel, Field


class MatchingStats(BaseModel):
    """订单撮合统计信息"""

    success: bool = False
    symbol: str = ""
    processed_orders: int = 0
    buy_orders_pooled: int = 0
    sell_orders_processed: int = 0
    matched_transactions: int = 0
    total_matched_quantity: str = "0"
    remaining_buy_orders: int = 0
    errors: list[str] = Field(default_factory=list)


class CSVImportStats(BaseModel):
    """CSV导入统计信息"""

    success: bool = False
    file_path: str = ""
    total_rows: int = 0
    order_filler: int = 0
    skipped_existing: int = 0
    imported_new: int = 0
    reset_count: int = 0
    errors: list[str] = Field(default_factory=list)


if __name__ == "__main__":
    """统计模型测试"""
    logger.info("📊 统计信息数据模型")
    logger.info("定义各种操作的统计信息数据模型:")
    logger.info("- MatchingStats: 订单撮合统计信息")
    logger.info("- CSVImportStats: CSV导入统计信息")

    # 测试统计模型
    match_stats = MatchingStats(success=True, symbol="ADAUSDC", processed_orders=50)
    import_stats = CSVImportStats(success=True, file_path="test.csv", total_rows=200)

    logger.info(
        f"\n测试模型: MatchingStats(processed={match_stats.processed_orders}), CSVImportStats(rows={import_stats.total_rows})"
    )
