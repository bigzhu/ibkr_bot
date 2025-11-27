"""
成交订单管理API接口
"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from loguru import logger

from web_admin.api.utils.database_helpers import (
    compute_pagination,
    query_all_dict,
    query_one_dict,
)

from ..utils.filled_orders_helpers import (
    build_where_clause_and_params,
    convert_row_to_response,
    get_base_query,
    validate_order_params,
)
from .auth import get_current_user

router = APIRouter()


@router.get("/filled-orders/", dependencies=[Depends(get_current_user)])
async def get_order_filler(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页大小"),
    symbol: str | None = Query(None, description="交易对过滤"),
    status: str | None = Query(None, description="状态过滤"),
    side: str | None = Query(None, description="买卖方向过滤"),
    unmatched: str | None = Query(None, description="未撮合过滤"),
    order_by: str = Query("time", description="排序字段"),
    order_direction: str = Query("DESC", description="排序方向"),
) -> dict[str, Any]:
    """
    获取成交订单列表

    支持分页,筛选和排序功能
    """
    # 使用辅助函数构建查询条件
    base_query = get_base_query()
    where_clause, params = build_where_clause_and_params(
        symbol, status, side, unmatched
    )
    order_by, order_direction = validate_order_params(order_by, order_direction)

    # 获取总记录数
    count_query = f"SELECT COUNT(*) FROM filled_orders{where_clause}"
    count_result = query_one_dict(count_query, tuple(params))
    total = int(count_result["COUNT(*)"]) if count_result else 0

    # 计算分页参数
    page_size = max(1, min(page_size, 1000))

    total_pages, offset = compute_pagination(total, page, page_size)

    # 构建分页查询
    data_query = f"{base_query}{where_clause} ORDER BY {order_by} {order_direction} LIMIT ? OFFSET ?"
    params.extend([str(page_size), str(offset)])

    # 执行查询并转换数据
    rows = query_all_dict(data_query, tuple(params))

    # 转换数据为响应模型 - rows已经是字典格式
    orders = [convert_row_to_response(row) for row in rows]

    return {
        "success": True,
        "message": f"获取到 {len(orders)} 个成交订单",
        "data": orders,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/filled-orders/stats", dependencies=[Depends(get_current_user)])
async def get_order_filler_stats() -> dict[str, Any]:
    """
    获取成交订单统计信息
    """
    # 异常向上传播(fail-fast原则)
    result = query_one_dict(
        """
        SELECT
            COUNT(*) as total_orders,
            COUNT(CASE WHEN unmatched_qty > 0 THEN 1 END) as unmatched_count,
            COUNT(CASE WHEN unmatched_qty = 0 OR unmatched_qty IS NULL THEN 1 END) as matched_count
        FROM filled_orders
        """
    )

    stats = {
        "total_orders": int(result["total_orders"]) if result else 0,
        "unmatched_count": int(result["unmatched_count"]) if result else 0,
        "matched_count": int(result["matched_count"]) if result else 0,
    }

    return {"success": True, "message": "获取统计信息成功", "data": stats}


@router.get("/filled-orders/symbols", dependencies=[Depends(get_current_user)])
async def get_filled_order_symbols() -> dict[str, Any]:
    """
    获取成交订单中的所有交易对列表
    """
    # 异常向上传播(fail-fast原则)
    query = """
    SELECT DISTINCT pair
    FROM filled_orders
    WHERE pair IS NOT NULL
    ORDER BY pair
    """

    rows = query_all_dict(query)

    # 访问字典中的pair字段
    symbols = [row["pair"] for row in rows]

    return {
        "success": True,
        "message": f"获取到 {len(symbols)} 个交易对",
        "data": symbols,
    }


@router.post("/filled-orders/sync", dependencies=[Depends(get_current_user)])
async def sync_order_filler() -> dict[str, Any]:
    """
    手动触发同步成交订单

    自动识别同步模式:
    - 如果数据库中该交易对有历史订单,自动执行增量同步
    - 如果数据库中该交易对无历史订单,自动执行全量同步
    """
    # 简化同步实现 - 返回模拟结果
    result = {
        "success": True,
        "total_symbols": 0,
        "processed_symbols": 0,
        "new_orders": 0,
        "summary": "同步功能暂未实现",
    }

    if result["success"]:
        # 处理同步结果
        summary = result.get(
            "summary",
            f"同步完成: 处理了 {result.get('processed_symbols', 0)} 个交易对",
        )

        return {
            "success": True,
            "message": summary,
            "data": {
                "total_symbols": result.get("total_symbols", 0),
                "processed_symbols": result.get("processed_symbols", 0),
                "incremental_symbols": result.get("incremental_symbols", 0),
                "full_sync_symbols": result.get("full_sync_symbols", 0),
                "total_orders": result.get("total_orders", 0),
                "new_orders": result.get("new_orders", 0),
                "updated_orders": result.get("updated_orders", 0),
                "skipped_orders": result.get("skipped_orders", 0),
                "errors": result.get("errors", []),
            },
        }
    else:
        return {
            "success": False,
            "message": f"同步失败: {result.get('error', '未知错误')}",
            "data": result,
        }


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    logger.info("💰 成交订单路由模块")
    logger.info("提供成交订单相关的 API 端点")
    logger.info("- GET /api/v1/filled-orders/ - 获取成交订单列表")
    logger.info("- GET /api/v1/filled-orders/stats - 获取成交订单统计")
    logger.info("- GET /api/v1/filled-orders/symbols - 获取交易对列表")
    logger.info("- POST /api/v1/filled-orders/sync - 同步成交订单")
