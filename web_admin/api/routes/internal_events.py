"""
内部事件接收路由 - 跨进程事件通知

专门处理来自独立进程(如scheduler调度的order_builder)的事件通知
通过HTTP POST接收事件,转发到WebSocket事件总线
"""

from typing import Any

from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from ..events import publish_trading_log_created, publish_trading_log_updated

router = APIRouter()


class TradingLogCreatedEvent(BaseModel):
    """交易日志创建事件模型"""

    log_id: int
    log_data: dict[str, Any]


class TradingLogUpdatedEvent(BaseModel):
    """交易日志更新事件模型"""

    log_id: int
    updated_fields: dict[str, Any]


@router.post("/trading-log-created")
async def handle_trading_log_created(event: TradingLogCreatedEvent) -> dict[str, Any]:
    """
    处理交易日志创建事件 - 来自独立进程的HTTP通知

    Args:
        event: 交易日志创建事件数据

    Returns:
        处理结果
    """
    logger.info(f"🔄 收到HTTP事件通知: 交易日志创建, log_id={event.log_id}")

    # 转发到WebSocket事件总线
    publish_trading_log_created(event.log_id, event.log_data)

    logger.info(f"✅ HTTP事件转发成功: log_id={event.log_id}")

    return {"success": True, "message": f"交易日志创建事件已处理: {event.log_id}"}


@router.post("/trading-log-updated")
async def handle_trading_log_updated(event: TradingLogUpdatedEvent) -> dict[str, Any]:
    """
    处理交易日志更新事件 - 来自独立进程的HTTP通知

    Args:
        event: 交易日志更新事件数据

    Returns:
        处理结果
    """
    logger.info(
        f"🔄 收到HTTP事件通知: 交易日志更新, log_id={event.log_id}, 字段={list(event.updated_fields.keys())}"
    )

    # 转发到WebSocket事件总线
    publish_trading_log_updated(event.log_id, event.updated_fields)

    logger.info(f"✅ HTTP事件转发成功: log_id={event.log_id}")

    return {"success": True, "message": f"交易日志更新事件已处理: {event.log_id}"}
