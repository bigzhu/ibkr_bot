# order_builder/models.py

from typing import NamedTuple, cast

from pydantic import BaseModel, Field

from shared.types import Kline


class DemarkSignal(NamedTuple):
    side: str
    value: int
    klines: list[Kline]


class CancelOrderResult(BaseModel):
    """取消订单结果模型"""

    order_id: str = Field(..., description="订单ID")
    client_order_id: str | None = Field(None, description="客户端订单ID")
    side: str = Field(..., description="买卖方向")
    quantity: str = Field(..., description="数量")
    symbol: str = Field(..., description="交易对符号")


class CancelOperationResult(BaseModel):
    """取消操作结果模型"""

    success: bool = Field(..., description="操作是否成功")
    cancelled_count: int = Field(default=0, description="成功取消的订单数量")
    failed_count: int = Field(default=0, description="取消失败的订单数量")
    total_orders: int = Field(default=0, description="总处理订单数量")
    cancelled_orders: list[CancelOrderResult] = Field(
        default_factory=lambda: cast(list[CancelOrderResult], []),
        description="取消成功的订单列表",
    )
    message: str = Field(default="", description="操作结果消息")
