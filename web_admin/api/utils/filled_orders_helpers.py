"""
成交订单查询辅助函数
"""

from datetime import UTC, datetime
from typing import Any

from loguru import logger


def build_where_clause_and_params(
    symbol: str | None,
    status: str | None,
    side: str | None,
    unmatched: str | None = None,
) -> tuple[str, list[str]]:
    """构建WHERE子句和参数"""
    where_conditions: list[str] = []
    params: list[str] = []

    if symbol:
        where_conditions.append("pair = ?")
        params.append(symbol)

    if status:
        where_conditions.append("status = ?")
        params.append(status)

    if side:
        where_conditions.append("side = ?")
        params.append(side)

    if unmatched and unmatched == "true":
        where_conditions.append("unmatched_qty > 0")

    where_clause = ""
    if where_conditions:
        where_clause = " WHERE " + " AND ".join(where_conditions)

    return where_clause, params


def validate_order_params(order_by: str, order_direction: str) -> tuple[str, str]:
    """验证排序参数"""
    valid_order_fields = [
        "id",
        "date_utc",
        "kline_time",
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
        "profit",
        "commission",
    ]

    if order_by not in valid_order_fields:
        order_by = "time"

    if order_direction.upper() not in ["ASC", "DESC"]:
        order_direction = "DESC"

    return order_by, order_direction


def _format_kline_time(raw_value: Any) -> str | None:
    """将k线时间戳(毫秒)转换为UTC字符串"""
    if raw_value in (None, ""):
        return None
    try:
        timestamp_ms = int(raw_value)
        if timestamp_ms <= 0:
            return None
        dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return str(raw_value) if raw_value is not None else None


def convert_row_to_response(row_dict: dict[str, Any]) -> dict[str, Any]:
    """将数据库行转换为响应字典,只返回数据库中实际存在的字段"""
    return {
        "id": row_dict.get("id"),
        "date_utc": row_dict.get("date_utc"),
        "kline_time": _format_kline_time(row_dict.get("kline_time")),
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
        "profit": str(row_dict.get("profit")) if row_dict.get("profit") else None,
        "commission": str(row_dict.get("commission"))
        if row_dict.get("commission")
        else None,
    }


def get_base_query() -> str:
    """获取基础查询SQL"""
    return """
    SELECT filled_orders.id,
           filled_orders.date_utc,
           filled_orders.order_no,
           filled_orders.pair,
           filled_orders.order_type,
           filled_orders.side,
           filled_orders.order_price,
           filled_orders.order_amount,
           filled_orders.time,
           filled_orders.executed,
           filled_orders.average_price,
           filled_orders.trading_total,
           filled_orders.status,
           filled_orders.unmatched_qty,
           filled_orders.client_order_id,
           filled_orders.created_at,
           filled_orders.updated_at,
           filled_orders.profit,
           filled_orders.commission,
           tl.kline_time AS kline_time
    FROM filled_orders
    LEFT JOIN (
        SELECT order_id, MAX(kline_time) AS kline_time
        FROM trading_logs
        WHERE order_id IS NOT NULL
        GROUP BY order_id
    ) AS tl ON tl.order_id = filled_orders.order_no
    """


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    logger.info("🔧 成交订单查询辅助函数")
    logger.info("提供成交订单查询的辅助工具函数")
    logger.info("- build_where_clause_and_params() - 构建WHERE子句")
    logger.info("- validate_order_params() - 验证排序参数")
    logger.info("- convert_row_to_response() - 转换响应模型")
    logger.info("- get_base_query() - 获取基础查询SQL")
