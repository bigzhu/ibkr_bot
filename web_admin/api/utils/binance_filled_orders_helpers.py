"""
币安成交订单查询辅助函数
"""

from typing import Any

from loguru import logger


def build_where_clause_and_params(
    pair: str | None, status: str | None, side: str | None
) -> tuple[str, list[str]]:
    """构建WHERE子句和参数"""
    where_conditions: list[str] = []
    params: list[str] = []

    if pair:
        where_conditions.append("pair = ?")
        params.append(pair)

    if status:
        where_conditions.append("status = ?")
        params.append(status)

    if side:
        where_conditions.append("side = ?")
        params.append(side)

    where_clause = ""
    if where_conditions:
        where_clause = " WHERE " + " AND ".join(where_conditions)

    return where_clause, params


def validate_order_params(order_by: str, order_direction: str) -> tuple[str, str]:
    """验证排序参数"""
    valid_order_fields: list[str] = [
        "id",
        "date_utc",
        "order_no",
        "pair",
        "order_type",
        "side",
        "order_price",
        "order_amount",
        "time",
        "executed",
        "average_price",
        "trading_total",
        "status",
        "unmatched_qty",
        "client_order_id",
        "created_at",
        "updated_at",
    ]

    if order_by not in valid_order_fields:
        order_by = "time"

    if order_direction.upper() not in ["ASC", "DESC"]:
        order_direction = "DESC"

    return order_by, order_direction


def convert_row_to_response(row_dict: dict[str, Any]) -> dict[str, Any]:
    """将数据库行转换为响应字典"""
    return {
        "id": row_dict.get("id"),
        "date_utc": row_dict.get("date_utc"),
        "order_no": row_dict.get("order_no"),
        "pair": row_dict.get("pair"),
        "order_type": row_dict.get("order_type"),
        "side": row_dict.get("side"),
        "order_price": str(row_dict.get("order_price"))
        if row_dict.get("order_price")
        else None,
        "order_amount": str(row_dict.get("order_amount"))
        if row_dict.get("order_amount")
        else None,
        "time": row_dict.get("time"),
        "executed": str(row_dict.get("executed")) if row_dict.get("executed") else None,
        "average_price": str(row_dict.get("average_price"))
        if row_dict.get("average_price")
        else None,
        "trading_total": str(row_dict.get("trading_total"))
        if row_dict.get("trading_total")
        else None,
        "status": row_dict.get("status"),
        "unmatched_qty": str(row_dict.get("unmatched_qty"))
        if row_dict.get("unmatched_qty")
        else None,
        "client_order_id": row_dict.get("client_order_id"),
        "created_at": row_dict.get("created_at"),
        "updated_at": row_dict.get("updated_at"),
    }


def get_base_query() -> str:
    """获取基础查询SQL"""
    return """
    SELECT id, date_utc, order_no, pair, order_type, side, order_price, order_amount,
           time, executed, average_price, trading_total, status, unmatched_qty,
           client_order_id, created_at, updated_at
    FROM filled_orders
    """


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    logger.info("🔧 币安成交订单查询辅助函数")
    logger.info("提供币安成交订单查询的辅助工具函数")
    logger.info("- build_where_clause_and_params() - 构建WHERE子句")
    logger.info("- validate_order_params() - 验证排序参数")
    logger.info("- convert_row_to_response() - 转换响应模型")
    logger.info("- get_base_query() - 获取基础查询SQL")
