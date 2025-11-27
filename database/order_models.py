"""
订单相关数据模型

定义各种订单类型的Pydantic模型,包括账户交易记录和已完成订单
"""

import re
from datetime import datetime
from typing import Any

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, field_validator

if __name__ == "__main__":
    try:
        from shared.path_utils import ensure_project_root_for_script
    except ImportError:
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from shared.path_utils import ensure_project_root_for_script

    ensure_project_root_for_script(__file__)

from shared.constants import BUY, SELL


class AccountTradeList(BaseModel):
    """账户交易记录模型"""

    db_id: int | None = Field(default=None, description="数据库自增ID")
    symbol: str = Field(..., description="交易对符号")
    trade_id: str = Field(..., description="交易ID", alias="id")
    order_id: str = Field(..., description="订单ID", alias="orderId")
    order_list_id: int = Field(
        default=-1, description="订单列表ID", alias="orderListId"
    )
    price: str = Field(..., description="成交价格")
    qty: str = Field(..., description="成交数量")
    quote_qty: str = Field(..., description="成交金额", alias="quoteQty")
    commission: str = Field(..., description="手续费")
    commission_asset: str = Field(
        ..., description="手续费资产", alias="commissionAsset"
    )
    time: int = Field(..., description="成交时间戳")
    is_buyer: bool = Field(..., description="是否买方", alias="isBuyer")
    is_maker: bool = Field(..., description="是否挂单方", alias="isMaker")
    is_best_match: bool = Field(..., description="是否最佳匹配", alias="isBestMatch")
    is_self_trade: bool = Field(..., description="是否自成交", alias="isSelfTrade")
    client_order_id: str = Field(
        default="", description="客户端订单ID", alias="clientOrderId"
    )
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """验证交易对符号"""
        return v.upper()

    @field_validator("trade_id")
    @classmethod
    def validate_trade_id(cls, v: str) -> str:
        """验证交易ID格式"""
        if not v:
            raise ValueError("交易ID不能为空")
        return v

    model_config = ConfigDict(use_enum_values=True, populate_by_name=True)


class MexcFilledOrder(BaseModel):
    """MEXC已完成订单模型"""

    id: int | None = None
    symbol: str = Field(..., description="交易对符号")
    order_id: int = Field(..., description="订单ID", alias="orderId")
    order_list_id: int | None = Field(
        default=None, description="订单列表ID", alias="orderListId"
    )
    client_order_id: str | None = Field(
        default=None, description="客户端订单ID", alias="clientOrderId"
    )
    price: str | None = Field(default=None, description="价格")
    orig_qty: str | None = Field(default=None, description="原始数量", alias="origQty")
    executed_qty: str | None = Field(
        default=None, description="执行数量", alias="executedQty"
    )
    cumulative_quote_qty: str | None = Field(
        default=None, description="累计计价数量", alias="cummulativeQuoteQty"
    )
    status: str | None = Field(default=None, description="状态")
    time_in_force: str | None = Field(
        default=None, description="时效", alias="timeInForce"
    )
    type: str | None = Field(default=None, description="类型")
    side: str | None = Field(default=None, description="方向")
    stop_price: str | None = Field(
        default=None, description="止损价", alias="stopPrice"
    )
    iceberg_qty: str | None = Field(
        default=None, description="冰山数量", alias="icebergQty"
    )
    time: int | None = Field(default=None, description="时间")
    update_time: int | None = Field(
        default=None, description="更新时间", alias="updateTime"
    )
    is_working: bool | None = Field(
        default=None, description="是否工作中", alias="isWorking"
    )
    orig_quote_order_qty: str | None = Field(
        default=None, description="原始计价订单数量", alias="origQuoteOrderQty"
    )
    working_time: int | None = Field(default=None, description="工作时间")
    self_trade_prevention_mode: str | None = Field(
        default=None, description="自成交防止模式"
    )
    unmatched_qty: str | None = Field(default=None, description="未匹配数量")
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """验证交易对符号"""
        return v.upper()

    model_config = ConfigDict(use_enum_values=True, populate_by_name=True)


class BinanceFilledOrder(BaseModel):
    """Binance已完成订单模型 - 基于CSV导出格式"""

    id: int | None = None
    date_utc: str = Field(..., description="订单创建时间(UTC)")
    order_no: str = Field(..., description="订单号")
    pair: str = Field(..., description="交易对")
    order_type: str = Field(..., description="订单类型")
    side: str = Field(..., description="买卖方向")
    order_price: str = Field(..., description="订单价格")
    order_amount: str = Field(..., description="订单数量")
    time: str = Field(..., description="成交时间")
    matched_time: str | None = Field(default=None, description="撮合完成时间(UTC)")
    executed: str = Field(..., description="已执行数量")
    average_price: str = Field(..., description="平均成交价格")
    trading_total: str = Field(..., description="成交总额")
    status: str = Field(..., description="订单状态")
    unmatched_qty: str = Field(default="0", description="未匹配数量")
    client_order_id: str | None = Field(default=None, description="客户端订单ID")
    profit: str = Field(default="0", description="利润金额")
    commission: str = Field(default="0", description="手续费")
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("pair")
    @classmethod
    def validate_pair(cls, v: str) -> str:
        """验证交易对符号"""
        return v.upper()

    @field_validator("order_no")
    @classmethod
    def validate_order_no(cls, v: str) -> str:
        """验证订单号"""
        if not v:
            raise ValueError("订单号不能为空")
        return v

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> "BinanceFilledOrder":
        """从CSV行数据创建BinanceFilledOrder对象"""

        def extract_numeric_value(value: str) -> str:
            """提取字符串中的数值部分, 去除单位"""
            match = re.search(r"[\d.]+", value)
            return match.group() if match else "0"

        executed_value = extract_numeric_value(row["Executed"])

        return cls(
            date_utc=row["Date(UTC)"],
            order_no=row["OrderNo"],
            pair=row["Pair"],
            order_type=row["Type"],
            side=BUY if row["Side"].upper() == "BUY" else SELL,
            order_price=extract_numeric_value(row["Order Price"]),
            order_amount=extract_numeric_value(row["Order Amount"]),
            time=row["Time"],
            executed=executed_value,
            average_price=extract_numeric_value(row["Average Price"]),
            trading_total=extract_numeric_value(row["Trading total"]),
            status=row["Status"],
            unmatched_qty=executed_value if row["Status"] == "FILLED" else "0",
            client_order_id=None,  # CSV 文件通常不包含此字段
        )

    @classmethod
    def from_db_dict(cls, row_dict: dict[str, Any]) -> "BinanceFilledOrder":
        """从数据库字典创建BinanceFilledOrder对象 - 使用字段名映射避免索引错误"""
        id_val = row_dict.get("id")
        id_typed = int(id_val) if isinstance(id_val, int) else None
        return cls(
            id=id_typed,
            date_utc=_to_str(row_dict, "date_utc"),
            order_no=_to_str(row_dict, "order_no"),
            pair=_to_str(row_dict, "pair"),
            order_type=_to_str(row_dict, "order_type"),
            side=_to_str(row_dict, "side", default=BUY),
            order_price=_to_str(row_dict, "order_price", default="0"),
            order_amount=_to_str(row_dict, "order_amount", default="0"),
            time=_to_str(row_dict, "time"),
            matched_time=_optional_str(row_dict, "matched_time"),
            executed=_to_str(row_dict, "executed", default="0"),
            average_price=_to_str(row_dict, "average_price", default="0"),
            trading_total=_to_str(row_dict, "trading_total", default="0"),
            status=_to_str(row_dict, "status"),
            unmatched_qty=_to_str(row_dict, "unmatched_qty", default="0"),
            client_order_id=_optional_str(row_dict, "client_order_id"),
        )

    model_config = ConfigDict(use_enum_values=True)


class BinanceOpenOrder(BaseModel):
    """Binance 未成交订单模型 - 基于 API 返回格式"""

    symbol: str = Field(..., description="交易对")
    order_id: int = Field(..., description="订单ID", alias="orderId")
    client_order_id: str = Field(..., description="客户端订单ID", alias="clientOrderId")
    price: str = Field(..., description="订单价格")
    orig_qty: str = Field(..., description="原始订单数量", alias="origQty")
    executed_qty: str = Field(..., description="已成交数量", alias="executedQty")
    cumulative_quote_qty: str = Field(
        ..., description="已成交金额", alias="cummulativeQuoteQty"
    )
    status: str = Field(..., description="订单状态")
    time_in_force: str = Field(..., description="时效类型", alias="timeInForce")
    type: str = Field(..., description="订单类型")
    side: str = Field(..., description="买卖方向")
    stop_price: str | None = Field(
        default=None, description="止损价格", alias="stopPrice"
    )
    iceberg_qty: str = Field(..., description="冰山订单数量", alias="icebergQty")
    time: int = Field(..., description="订单时间戳")
    update_time: int = Field(..., description="更新时间戳", alias="updateTime")
    is_working: bool = Field(..., description="是否生效中", alias="isWorking")
    working_time: int = Field(..., description="生效时间戳", alias="workingTime")
    orig_quote_order_qty: str = Field(
        ..., description="原始计价订单数量", alias="origQuoteOrderQty"
    )
    self_trade_prevention_mode: str = Field(
        ..., description="自成交防止模式", alias="selfTradePreventionMode"
    )

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """验证交易对符号"""
        return v.upper()

    @field_validator("side")
    @classmethod
    def validate_side(cls, v: str) -> str:
        """验证买卖方向"""
        side_upper = v.upper()
        if side_upper not in (BUY, SELL):
            raise ValueError(f"买卖方向必须是 {BUY} 或 {SELL}, 不能是 {side_upper}")
        return side_upper

    model_config = ConfigDict(use_enum_values=True, populate_by_name=True)


if __name__ == "__main__":
    """订单模型测试"""
    logger.info("📋 订单相关数据模型")
    logger.info("定义各种订单类型的数据模型:")
    logger.info("- AccountTradeList: 账户交易记录模型")
    logger.info("- MexcFilledOrder: MEXC已完成订单模型")
    logger.info("- BinanceFilledOrder: Binance已完成订单模型")
    logger.info("- BinanceOpenOrder: Binance未成交订单模型")

    # 测试账户交易记录模型
    trade = AccountTradeList(
        symbol="ADAUSDC",
        id="579645657212563456X1",
        orderId="C02__579645657212563456047",
        price="50000.12",
        qty="0.001",
        quoteQty="50.0",
        commission="0.05",
        commissionAsset="USDT",
        time=1753980543000,
        isBuyer=True,
        isMaker=False,
        isBestMatch=True,
        isSelfTrade=False,
    )

    # 测试MEXC已完成订单模型
    mexc_order = MexcFilledOrder(
        symbol="ADAUSDC",
        orderId=123456789,
    )

    logger.info(
        f"\n测试模型: AccountTradeList({trade.symbol}), MexcFilledOrder({mexc_order.symbol})"
    )


def _to_str(row: dict[str, Any], key: str, *, default: str = "") -> str:
    """Safely convert a dictionary field to string with default."""
    return str(row.get(key, default))


def _optional_str(row: dict[str, Any], key: str) -> str | None:
    """Return string value when present and non-null."""
    value = row.get(key)
    return str(value) if value is not None else None
