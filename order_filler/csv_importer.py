"""
Binance CSV导入功能模块
从Binance导出的CSV文件导入订单数据到本地数据库
遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except
"""

import csv
import sys
from pathlib import Path
from typing import Any

from loguru import logger

# 处理相对导入问题
if __name__ == "__main__":
    # 直接运行时添加父目录到路径
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))

from database.models import BinanceFilledOrder, CSVImportStats
from order_filler.data_access import clear_all_orders, insert_order


class BinanceCSVImporter:
    """
    Binance CSV导入器
    负责解析Binance导出的CSV文件并导入到数据库
    支持标准的Binance CSV导出格式
    """

    def __init__(self) -> None:
        """初始化导入器"""
        pass

    def import_csv(self, csv_file_path: str, _: bool = True) -> CSVImportStats:
        """
        导入CSV文件

        Args:
            csv_file_path: CSV文件路径
            _: 是否重置未匹配数量为executed数量(已废弃,表会被清空)

        Returns:
            导入统计信息
        """
        csv_path = self._resolve_csv_path(csv_file_path)
        cleared_count = self._clear_existing_orders()
        stats_state = self._initialize_stats_state(cleared_count)
        self._process_csv_rows(csv_path, stats_state)

        stats = self._build_stats(csv_path, stats_state)
        logger.info(
            f"CSV导入完成: 新增{stats.imported_new}条, 跳过{stats.skipped_existing}条, 重置{stats.reset_count}条"
        )
        return stats

    def _parse_csv_row(
        self, row: dict[str, str], row_num: int
    ) -> BinanceFilledOrder | None:
        """
        解析CSV行数据为BinanceFilledOrder对象(基于实际Binance CSV格式)

        Args:
            row: CSV行数据
            row_num: 行号(用于错误报告)

        Returns:
            BinanceFilledOrder对象或None(解析失败)
        """
        # 检查必需字段
        required_fields = [
            "Date(UTC)",
            "OrderNo",
            "Pair",
            "Type",
            "Side",
            "Order Price",
            "Order Amount",
            "Time",
            "Executed",
            "Average Price",
            "Trading total",
            "Status",
        ]

        missing_fields = [field for field in required_fields if field not in row]
        if missing_fields:
            logger.warning(f"第{row_num}行缺少字段: {missing_fields}")
            return None

        # 使用模型的 from_csv_row 方法创建对象
        return BinanceFilledOrder.from_csv_row(row)

    def _resolve_csv_path(self, csv_file_path: str) -> Path:
        """解析并校验CSV文件路径"""
        csv_path = Path(csv_file_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV文件不存在: {csv_file_path}")
        return csv_path

    def _clear_existing_orders(self) -> int:
        """清空现有订单数据并记录数量"""
        cleared_count = clear_all_orders()
        logger.info(f"清空现有数据: {cleared_count} 条记录")
        return cleared_count

    def _initialize_stats_state(self, cleared_count: int) -> dict[str, Any]:
        """初始化导入状态统计"""
        return {
            "total_rows": 0,
            "imported_new": 0,
            "skipped_existing": 0,
            "order_filler": 0,
            "reset_count": 0,
            "errors": [],
            "cleared_count": cleared_count,
        }

    def _process_csv_rows(self, csv_path: Path, stats_state: dict[str, Any]) -> None:
        """遍历CSV行并更新统计信息"""
        with csv_path.open(encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)

            for row_num, row in enumerate(reader, 2):
                stats_state["total_rows"] += 1
                self._handle_csv_row(row, row_num, stats_state)

    def _handle_csv_row(
        self, row: dict[str, str], row_num: int, stats_state: dict[str, Any]
    ) -> None:
        """处理单行CSV记录"""
        order = self._parse_csv_row(row, row_num)
        if not order:
            return

        if order.status != "FILLED":
            logger.debug(f"跳过未完成订单: {order.order_no}, 状态: {order.status}")
            return

        if insert_order(order):
            stats_state["imported_new"] += 1
            stats_state["order_filler"] += 1
        else:
            stats_state["errors"].append(f"第{row_num}行: 插入数据库失败")

    def _build_stats(
        self, csv_path: Path, stats_state: dict[str, Any]
    ) -> CSVImportStats:
        """构建最终导入统计对象"""
        return CSVImportStats(
            file_path=str(csv_path),
            total_rows=stats_state["total_rows"],
            imported_new=stats_state["imported_new"],
            skipped_existing=stats_state["skipped_existing"],
            order_filler=stats_state["order_filler"],
            reset_count=stats_state["reset_count"],
            errors=stats_state["errors"],
        )


def import_binance_csv(csv_file_path: str, _: bool = True) -> CSVImportStats:
    """
    导入Binance CSV文件 - 便捷函数

    Args:
        csv_file_path: CSV文件路径
        _: 是否重置未匹配数量(已废弃,表会被清空)

    Returns:
        导入统计信息
    """
    importer = BinanceCSVImporter()
    return importer.import_csv(csv_file_path, _)


def main() -> None:
    """测试CSV导入功能"""
    import sys

    if len(sys.argv) < 2:
        logger.info("用法: p csv_importer.py CSV_FILE_PATH [--no-reset]")
        logger.info("示例: p csv_importer.py ./binance_trades.csv")
        logger.info("选项: --no-reset 不重置现有订单的未匹配数量")
        return

    csv_file_path = sys.argv[1]
    reset_unmatched = "--no-reset" not in sys.argv

    logger.info("📁 Binance CSV导入测试")
    logger.info("=" * 50)

    # 执行导入
    stats = import_binance_csv(csv_file_path, reset_unmatched)

    # 显示结果
    logger.info("✅ 导入完成!")
    logger.info(f"文件: {stats.file_path}")
    logger.info(f"总行数: {stats.total_rows}")
    logger.info(f"新增订单: {stats.imported_new}")
    logger.info(f"跳过现有: {stats.skipped_existing}")
    if reset_unmatched:
        logger.info(f"重置数量: {stats.reset_count}")
    logger.info(f"错误数: {len(stats.errors)}")

    if stats.errors:
        logger.info("错误详情:")
        for error in stats.errors:
            logger.info(f"  - {error}")


if __name__ == "__main__":
    main()
