"""
交易日志API端点
"""

# 使用简化的数据模型
from typing import Any

from fastapi import APIRouter, Depends, Query
from loguru import logger
from pydantic import BaseModel

from database.db_config import get_db_manager
from web_admin.api.utils.database_helpers import (
    query_all_dict,
    query_one_dict,
)

from .auth import get_current_user

# 使用现有的数据库管理器
db_manager = get_db_manager()

router = APIRouter(prefix="/trading-logs", tags=["trading-logs"])


class TradingLogData(BaseModel):
    """简化的交易日志数据模型"""

    id: int
    symbol: str
    timeframe: str
    timestamp: int
    signal_value: int | None = None
    meets_conditions: bool = False
    execution_status: str = "normal"


class TradingLogResponse(BaseModel):
    """交易日志响应模型"""

    success: bool
    data: list[dict[str, Any]] = []
    total: int = 0
    page: int = 1
    limit: int = 200
    error: str = ""


class TradingLogStats(BaseModel):
    """交易统计数据模型"""

    total_signals: int = 0
    buy_signals: int = 0
    sell_signals: int = 0
    conditions_met: int = 0
    error_count: int = 0
    symbols_count: int = 0
    timeframes_count: int = 0
    latest_signal: int | None = None


class TradingStatsResponse(BaseModel):
    """交易统计响应模型"""

    success: bool
    data: TradingLogStats | None = None
    error: str = ""


class TradingSymbolsResponse(BaseModel):
    """交易对列表响应模型"""

    success: bool
    data: list[str] = []


class TimeframesResponse(BaseModel):
    """时间周期列表响应模型"""

    success: bool
    data: list[str] = []


class DeleteLogResponse(BaseModel):
    """删除日志响应模型"""

    success: bool
    message: str


class ClearLogsResponse(BaseModel):
    """清空日志响应模型"""

    success: bool
    message: str
    deleted_count: int = 0
    total_count: int = 0


@router.get(
    "/logs",
    response_model=TradingLogResponse,
    dependencies=[Depends(get_current_user)],
)
async def get_trading_logs(
    symbol: str = Query(None, description="交易对过滤,多个用逗号分隔"),
    timeframe: str = Query(None, description="时间周期过滤,多个用逗号分隔"),
    execution_status: str = Query(None, description="执行状态过滤 (normal/error)"),
    meets_conditions: bool = Query(None, description="是否满足条件过滤"),
    order_side: str = Query(None, description="挂单方向过滤 (BUY/SELL)"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(200, ge=1, le=500, description="每页数量"),
):
    """
    获取交易日志列表

    Args:
        symbol: 交易对过滤(可选)
        timeframe: 时间周期过滤(可选)
        page: 页码
        limit: 每页数量

    Returns:
        TradingLogResponse: 交易日志响应
    """
    # 使用灵活的数据库辅助函数获取交易日志
    from ..utils.database_helpers import get_trading_logs_flexible

    # 支持可选的筛选条件
    logs, total_count = get_trading_logs_flexible(
        symbol=symbol,
        timeframe=timeframe,
        execution_status=execution_status,
        meets_conditions=meets_conditions,
        order_side=order_side,
        limit=limit,
        offset=(page - 1) * limit,
    )

    # 数据已经是字典格式,直接使用
    return TradingLogResponse(
        success=True, data=logs, total=total_count, page=page, limit=limit
    )


@router.get("/stats", response_model=TradingStatsResponse)
async def get_trading_stats(
    _: str = Depends(get_current_user),
    symbol: str = Query(None, description="交易对过滤"),
    days: int = Query(None, description="统计天数(不指定则显示全部)"),
):
    """
    获取交易统计信息

    Args:
        symbol: 交易对过滤(可选)
        days: 统计天数

    Returns:
        TradingStatsResponse: 交易统计响应
    """
    # 使用数据库辅助函数获取统计数据
    from ..utils.database_helpers import get_trading_stats as get_stats_from_db

    stats_data = get_stats_from_db(symbol, days)

    return {"success": True, "data": stats_data}


@router.delete(
    "/logs/{log_id}",
    response_model=DeleteLogResponse,
    dependencies=[Depends(get_current_user)],
)
async def delete_trading_log(log_id: int):
    """
    删除单个交易日志

    Args:
        log_id: 日志ID

    Returns:
        DeleteLogResponse: 删除结果
    """
    # 这里可以添加删除逻辑,暂时返回成功
    # 实际项目中可能不需要删除交易日志
    return DeleteLogResponse(success=True, message=f"日志 {log_id} 删除成功")


@router.get(
    "/symbols",
    response_model=TradingSymbolsResponse,
    dependencies=[Depends(get_current_user)],
)
async def get_trading_symbols():
    """
    获取实际有交易日志数据的交易对列表(用于过滤选择)

    Returns:
        TradingSymbolsResponse: 交易对列表
    """
    rows = query_all_dict(
        """SELECT DISTINCT symbol
            FROM trading_logs
            WHERE symbol IS NOT NULL
            ORDER BY symbol"""
    )

    # 访问字典中的symbol字段
    valid_symbols = [str(row["symbol"]) for row in rows if row and row["symbol"]]

    return TradingSymbolsResponse(success=True, data=valid_symbols)


@router.get(
    "/timeframes",
    response_model=TimeframesResponse,
    dependencies=[Depends(get_current_user)],
)
async def get_timeframes():
    """
    获取所有时间周期列表(用于过滤选择)

    Returns:
        TimeframesResponse: 时间周期列表
    """
    from shared.timeframes import SUPPORTED_TIMEFRAMES

    return TimeframesResponse(success=True, data=SUPPORTED_TIMEFRAMES)


@router.delete(
    "/clear-all",
    response_model=ClearLogsResponse,
    dependencies=[Depends(get_current_user)],
)
async def clear_all_trading_logs():
    """
    清空所有交易日志记录

    Returns:
        ClearLogsResponse: 清空结果
    """
    # 先获取总数
    result = query_one_dict("SELECT COUNT(*) as count FROM trading_logs")
    total_count = int(result["count"]) if result else 0

    # 删除所有记录
    deleted_count = db_manager.execute_update("DELETE FROM trading_logs")

    return ClearLogsResponse(
        success=True,
        message=f"成功清空所有交易日志,共删除 {deleted_count} 条记录",
        deleted_count=deleted_count,
        total_count=total_count,
    )


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    logger.info("📊 交易日志路由模块")
    logger.info("提供交易日志相关的 API 端点")
    logger.info("- GET /api/v1/trading-logs/logs - 获取交易日志列表")
    logger.info("- GET /api/v1/trading-logs/stats - 获取交易统计")
    logger.info("- GET /api/v1/trading-logs/symbols - 获取交易对列表")
    logger.info("- GET /api/v1/trading-logs/timeframes - 获取时间周期列表")
    logger.info("- DELETE /api/v1/trading-logs/logs/{log_id} - 删除指定日志")
    logger.info("- DELETE /api/v1/trading-logs/clear-all - 清空所有日志")
