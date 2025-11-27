"""
成交订单数据模型
"""

from typing import Any

from loguru import logger
from pydantic import BaseModel, Field


class FilledOrderResponse(BaseModel):
    """成交订单响应模型"""

    id: int = Field(..., description="订单数据库ID")
    symbol: str = Field(..., description="交易对")
    order_id: int = Field(..., description="币安订单ID")
    order_list_id: int | None = Field(None, description="订单列表ID")
    client_order_id: str | None = Field(None, description="客户端订单ID")
    price: str | None = Field(None, description="订单价格")
    orig_qty: str | None = Field(None, description="原始数量")
    executed_qty: str | None = Field(None, description="已执行数量")
    unmatched_qty: str | None = Field(None, description="未撮合数量")
    cumulative_quote_qty: str | None = Field(None, description="累计成交金额")
    status: str | None = Field(None, description="订单状态")
    time_in_force: str | None = Field(None, description="有效时间类型")
    type: str | None = Field(None, description="订单类型")
    side: str | None = Field(None, description="买卖方向")
    stop_price: str | None = Field(None, description="止损价格")
    iceberg_qty: str | None = Field(None, description="冰山数量")
    time: int | None = Field(None, description="订单时间戳")
    update_time: int | None = Field(None, description="更新时间戳")
    is_working: bool | None = Field(None, description="是否工作中")
    orig_quote_order_qty: str | None = Field(None, description="原始报价订单数量")
    working_time: int | None = Field(None, description="工作时间")
    self_trade_prevention_mode: str | None = Field(None, description="自成交防护模式")
    created_at: str | None = Field(None, description="创建时间")
    updated_at: str | None = Field(None, description="更新时间")


class FilledOrdersListResponse(BaseModel):
    """成交订单列表响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: list[FilledOrderResponse] = Field(..., description="订单数据列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")


class FilledOrdersStatsResponse(BaseModel):
    """成交订单统计响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: dict[str, Any] = Field(..., description="统计数据")


class FilledOrderSymbolsResponse(BaseModel):
    """成交订单交易对列表响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: list[str] = Field(..., description="交易对列表")


class SyncFilledOrdersResponse(BaseModel):
    """同步成交订单响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: dict[str, Any] = Field(..., description="同步统计数据")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    logger.info("📋 成交订单数据模型")
    logger.info("定义成交订单相关的 Pydantic 数据模型")
    logger.info("- FilledOrderResponse - 单个成交订单响应")
    logger.info("- FilledOrdersListResponse - 成交订单列表响应")
    logger.info("- FilledOrdersStatsResponse - 成交订单统计响应")
    logger.info("- FilledOrderSymbolsResponse - 交易对列表响应")
    logger.info("- SyncFilledOrdersResponse - 同步结果响应")
