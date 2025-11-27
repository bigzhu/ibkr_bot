"""
Timeframe配置管理相关的 API 路由
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from loguru import logger

from database.db_config import get_db_manager

# 使用现有的数据库管理器
db_manager = get_db_manager()
from ..models.config import (
    BulkUpdatePercentagesRequest,
    BulkUpdatePercentagesResponse,
    TimeframeConfigListResponse,
    TimeframeConfigResponse,
    TimeframeConfigsBySymbolResponse,
    UpdateTimeframeConfigRequest,
)
from .auth import get_current_user

# 创建路由器
router = APIRouter(prefix="/timeframe-configs", tags=["Timeframe配置管理"])

# HTTP Bearer 认证
security = HTTPBearer()


@router.get(
    "/",
    response_model=TimeframeConfigListResponse,
    dependencies=[Depends(get_current_user)],
)
async def get_all_timeframe_configs():
    """
    获取所有timeframe配置

    返回所有timeframe配置的列表
    """
    # 使用数据库辅助函数获取时间周期配置数据
    from ..utils.database_helpers import get_all_timeframe_configs

    configs = get_all_timeframe_configs()

    return {
        "success": True,
        "message": f"获取到 {len(configs)} 个timeframe配置",
        "configs": configs,
    }


@router.get(
    "/{trading_symbol}",
    response_model=TimeframeConfigsBySymbolResponse,
    dependencies=[Depends(get_current_user)],
)
async def get_timeframe_configs_by_symbol(
    trading_symbol: str, kline_timeframe: str | None = None
):
    """
    根据交易对获取timeframe配置

    可以指定具体的时间周期进行过滤
    """
    from ..utils.database_helpers import get_timeframe_config_by_symbol

    configs = get_timeframe_config_by_symbol(trading_symbol, kline_timeframe)

    return {
        "success": True,
        "message": f"获取到交易对 {trading_symbol} 的 {len(configs)} 个配置",
        "configs": configs,
    }


@router.put(
    "/{config_id}",
    response_model=TimeframeConfigResponse,
    dependencies=[Depends(get_current_user)],
)
async def update_timeframe_config(
    config_id: int, request: UpdateTimeframeConfigRequest
):
    """
    更新timeframe配置

    可以更新指定配置的各项参数
    """
    logger.debug(
        f"🔍 收到更新请求: config_id={config_id}, request={request.model_dump()}"
    )

    update_data = _validate_and_build_update_data(request)
    _execute_update_sql(config_id, update_data)

    # 更新成功不再输出冗余日志

    return TimeframeConfigResponse(
        success=True, message=f"配置 {config_id} 更新成功", data=None
    )


def _validate_and_build_update_data(
    request: UpdateTimeframeConfigRequest,
) -> dict[str, Any]:
    """验证并构建更新数据"""
    update_data: dict[str, Any] = {}

    if request.kline_timeframe is not None:
        from shared.timeframes import SUPPORTED_TIMEFRAMES

        if request.kline_timeframe not in SUPPORTED_TIMEFRAMES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的时间周期,支持的周期:{', '.join(SUPPORTED_TIMEFRAMES)}",
            )
        update_data["kline_timeframe"] = request.kline_timeframe

    if request.demark_buy is not None:
        update_data["demark_buy"] = request.demark_buy

    if request.demark_sell is not None:
        update_data["demark_sell"] = request.demark_sell

    if request.daily_max_percentage is not None:
        update_data["daily_max_percentage"] = request.daily_max_percentage

    if request.minimum_profit_percentage is not None:
        update_data["minimum_profit_percentage"] = request.minimum_profit_percentage

    if request.monitor_delay is not None:
        update_data["monitor_delay"] = request.monitor_delay

    if request.oper_mode is not None:
        valid_oper_modes = ["all", "buy_only", "sell_only"]
        if request.oper_mode not in valid_oper_modes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的操作模式,支持的模式:{', '.join(valid_oper_modes)}",
            )
        update_data["oper_mode"] = request.oper_mode

    if request.is_active is not None:
        update_data["is_active"] = request.is_active

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="没有提供需要更新的字段"
        )

    return update_data


def _execute_update_sql(config_id: int, update_data: dict[str, Any]) -> None:
    """执行更新SQL操作"""
    set_clauses: list[str] = []
    params: list[Any] = []
    for field, value in update_data.items():
        set_clauses.append(f"{field} = ?")
        params.append(value)

    params.append(config_id)
    sql = f"UPDATE symbol_timeframe_configs SET {', '.join(set_clauses)} WHERE id = ?"

    try:
        rows_affected = db_manager.execute_update(sql, tuple(params))
    except Exception as e:  # 返回更友好的错误提示
        msg = str(e)
        # db_manager 会把 sqlite 异常包装为 ValueError, 这里通过错误信息判断
        if "no such column" in msg or "has no column" in msg:
            # 提示需要迁移数据库,以支持新字段
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "数据库缺少必要字段,请先运行迁移以更新表结构. "
                    "执行: p scripts/migrate_database.py --target-version 23"
                ),
            ) from e
        raise e
    if rows_affected == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"配置ID {config_id} 不存在"
        )


@router.post(
    "/minimum-profit/bulk-update",
    response_model=BulkUpdatePercentagesResponse,
    dependencies=[Depends(get_current_user)],
)
async def bulk_update_minimum_profit(
    request: BulkUpdatePercentagesRequest,
) -> BulkUpdatePercentagesResponse:
    """批量更新所有交易对的百分比配置"""

    set_clauses: list[str] = []
    params: list[float | int] = []

    if request.demark_buy is not None:
        set_clauses.append("demark_buy = ?")
        params.append(request.demark_buy)

    if request.demark_sell is not None:
        set_clauses.append("demark_sell = ?")
        params.append(request.demark_sell)

    if request.minimum_profit_percentage is not None:
        set_clauses.append("minimum_profit_percentage = ?")
        params.append(request.minimum_profit_percentage)

    if request.monitor_delay is not None:
        set_clauses.append("monitor_delay = ?")
        params.append(request.monitor_delay)

    sql = f"UPDATE symbol_timeframe_configs SET {', '.join(set_clauses)}"

    try:
        updated_count = db_manager.execute_update(sql, tuple(params))
    except ValueError as error:
        logger.error(f"批量更新百分比配置失败: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量更新百分比配置失败",
        ) from error

    updated_fields: list[str] = []
    if request.demark_buy is not None:
        updated_fields.append(f"买入信号值={request.demark_buy}")
    if request.demark_sell is not None:
        updated_fields.append(f"卖出信号值={request.demark_sell}")
    if request.minimum_profit_percentage is not None:
        updated_fields.append(f"利润百分比={request.minimum_profit_percentage}%")
    if request.monitor_delay is not None:
        updated_fields.append(f"监控延迟={request.monitor_delay}秒")

    return BulkUpdatePercentagesResponse(
        success=True,
        message=(f"已更新 {updated_count} 条配置的 " + ",".join(updated_fields)),
        updated_count=updated_count,
    )


@router.delete(
    "/{config_id}",
    response_model=TimeframeConfigResponse,
    dependencies=[Depends(get_current_user)],
)
async def delete_timeframe_config(config_id: int):
    """
    删除timeframe配置

    从数据库中删除指定的配置
    """
    rows_affected = db_manager.execute_update(
        "DELETE FROM symbol_timeframe_configs WHERE id = ?", (config_id,)
    )

    if rows_affected == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"配置ID {config_id} 不存在"
        )

    # 删除成功不再输出冗余日志

    return TimeframeConfigResponse(
        success=True, message=f"配置 {config_id} 删除成功", data=None
    )


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    logger.info("📊 时间周期配置路由模块")
    logger.info("提供时间周期配置管理相关的 API 端点")
    logger.info("- GET /api/v1/timeframe-configs - 获取时间周期配置列表")
    logger.info("- POST /api/v1/timeframe-configs - 创建时间周期配置")
    logger.info("- PUT /api/v1/timeframe-configs/{config_id} - 更新时间周期配置")
    logger.info("- DELETE /api/v1/timeframe-configs/{config_id} - 删除时间周期配置")
