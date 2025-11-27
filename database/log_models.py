"""
日志相关数据模型

定义交易日志的Pydantic模型
"""

from datetime import datetime

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TradingLog(BaseModel):
    """交易日志模型"""

    id: int | None = None
    symbol: str = Field(..., description="交易对符号")
    kline_timeframe: str = Field(..., description="K线时间周期")
    demark: int | None = Field(default=None, description="DeMark信号值")
    side: str | None = Field(default=None, description="订单方向")
    price: float | None = Field(default=None, description="订单价格")
    qty: float | None = Field(default=None, description="订单数量")
    profit_lock_qty: float | None = Field(default=None, description="利润锁定数量")
    order_id: str | None = Field(default=None, description="订单ID")
    open: float | None = Field(default=None, description="信号K线开盘价")
    high: float | None = Field(default=None, description="信号K线最高价")
    low: float | None = Field(default=None, description="信号K线最低价")
    close: float | None = Field(default=None, description="信号K线收盘价")
    error: str | None = Field(default=None, description="错误信息")
    kline_time: int | None = Field(default=None, description="K线时间")
    run_time: int | None = Field(default=None, description="运行时间")
    demark_percentage_coefficient: float | None = Field(
        default=None, description="DeMark百分比系数"
    )
    from_price: float | None = Field(default=None, description="基准价格")
    user_balance: float | None = Field(default=None, description="用户余额")
    price_change_percentage: float | None = Field(
        default=None, description="价格变化百分比"
    )
    created_at: datetime | None = None

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        return v.upper()

    @field_validator("demark")
    @classmethod
    def validate_demark(cls, v: int | None) -> int | None:
        """验证DeMark信号值范围"""
        if v is not None and (v < 1 or v > 50):
            raise ValueError("DeMark信号值必须在1-50范围内")
        return v

    model_config = ConfigDict(use_enum_values=True)


if __name__ == "__main__":
    """日志模型测试"""
    logger.info("📝 交易日志数据模型")
    logger.info("定义交易日志的数据模型:")
    logger.info("- TradingLog: 交易日志模型")

    # 测试交易日志模型
    log = TradingLog(
        symbol="ADAUSDC",
        kline_timeframe="15m",
        demark=8,
        side="BUY",
        price=50000.0,
        qty=0.001,
    )

    logger.info(f"\n测试模型: TradingLog({log.symbol}, {log.kline_timeframe})")
