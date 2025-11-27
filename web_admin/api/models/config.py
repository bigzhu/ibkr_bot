"""
配置相关的数据模型 - 使用金融级别数据类型
"""

from typing import Any

from loguru import logger
from pydantic import BaseModel, Field


class BinanceConfigRequest(BaseModel):
    """Binance API配置请求模型"""

    api_key: str = Field(..., description="API密钥")
    secret_key: str = Field(..., description="密钥")


class BinanceConfigResponse(BaseModel):
    """Binance API配置响应模型"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    validation_result: dict[str, Any] | None = Field(None, description="验证结果详情")


class ConfigItem(BaseModel):
    """配置项模型"""

    key: str = Field(..., description="配置键")
    value: str = Field(..., description="配置值")
    type: str = Field("string", description="配置类型")
    description: str = Field("", description="配置描述")
    is_encrypted: bool = Field(False, description="是否加密")
    is_required: bool = Field(False, description="是否必需")


class ConfigUpdateRequest(BaseModel):
    """配置更新请求模型"""

    configs: dict[str, str] = Field(..., description="要更新的配置项")


class ConfigUpdateResponse(BaseModel):
    """配置更新响应模型"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    updated_count: int = Field(0, description="更新的配置项数量")
    failed_configs: dict[str, str] | None = Field(None, description="更新失败的配置项")


class ConfigListResponse(BaseModel):
    """配置列表响应模型"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    configs: dict[str, dict[str, Any]] = Field(..., description="配置项列表")


class ApiValidationRequest(BaseModel):
    """API验证请求模型"""

    api_key: str = Field(..., description="API密钥")
    secret_key: str = Field(..., description="密钥")


class ApiValidationResponse(BaseModel):
    """API验证响应模型"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: dict[str, Any] | None = Field(None, description="验证结果数据")
    error_code: str | None = Field(None, description="错误代码")
    error_details: str | None = Field(None, description="错误详情")


class BinanceStatusData(BaseModel):
    """Binance状态数据模型"""

    has_api_key: bool = Field(..., description="是否已设置API密钥")
    has_secret_key: bool = Field(..., description="是否已设置密钥")
    is_configured: bool = Field(..., description="是否已完全配置")
    api_key: str = Field(..., description="显示用的API密钥(部分隐藏)")
    secret_key: str = Field(..., description="显示用的密钥(隐藏)")
    environment_name: str = Field(..., description="环境名称")


class BinanceStatusResponse(BaseModel):
    """Binance状态响应模型"""

    success: bool = Field(..., description="是否成功")
    data: BinanceStatusData = Field(..., description="Binance状态数据")


class SymbolValidationResponse(BaseModel):
    """交易对验证响应模型"""

    success: bool = Field(..., description="是否验证成功")
    message: str = Field(..., description="响应消息")
    data: dict[str, Any] | None = Field(None, description="验证结果数据")
    error_code: str | None = Field(None, description="错误代码")
    error_details: str | None = Field(None, description="错误详情")


# 交易对相关模型
class TradingSymbol(BaseModel):
    """交易对模型"""

    id: int = Field(..., description="交易对ID")
    symbol: str = Field(..., description="交易对符号")
    base_asset: str = Field(..., description="基础资产")
    quote_asset: str = Field(..., description="报价资产")
    base_asset_precision: int | None = Field(8, description="基础资产精度")
    quote_asset_precision: int | None = Field(8, description="报价资产精度")
    is_active: bool = Field(..., description="是否激活")
    description: str | None = Field(None, description="描述")

    # 价格相关字段
    current_price: float | None = Field(default=None, description="当前价格")
    high_24h: float | None = Field(default=None, description="24小时最高价")
    low_24h: float | None = Field(default=None, description="24小时最低价")
    min_price: float | None = Field(default=None, description="最小价格")
    max_price: float | None = Field(default=None, description="最大价格")
    tick_size: float | None = Field(default=None, description="价格步长")

    # 数量相关字段
    volume_24h: float | None = Field(default=None, description="24小时成交量")
    min_qty: float | None = Field(default=None, description="最小下单量")
    max_qty: float | None = Field(default=None, description="最大下单量")
    step_size: float | None = Field(default=None, description="下单步长")

    # 余额/价值相关字段
    volume_24h_quote: float | None = Field(default=None, description="24小时报价成交量")
    min_notional: float | None = Field(default=None, description="最小名义值")

    # 百分比字段
    price_change_24h: float | None = Field(
        default=None, description="24小时价格变化百分比"
    )

    # 其他字段保持原样
    last_updated_price: str | None = Field(None, description="价格最后更新时间")
    max_fund: int | None = Field(None, description="使用资金上限")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class AddTradingSymbolRequest(BaseModel):
    """添加交易对请求模型"""

    symbol: str = Field(..., description="交易对符号", min_length=5, max_length=12)
    description: str | None = Field("", description="描述信息", max_length=200)
    max_fund: int | None = Field(None, description="使用资金上限", ge=1)


class UpdateTradingSymbolRequest(BaseModel):
    """更新交易对请求模型"""

    is_active: bool | None = Field(None, description="是否激活")
    description: str | None = Field(None, description="描述信息", max_length=200)
    max_fund: int | None = Field(None, description="使用资金上限", ge=1)


class TradingSymbolResponse(BaseModel):
    """交易对操作响应模型"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: dict[str, Any] | None = Field(None, description="返回数据")


class TradingSymbolListResponse(BaseModel):
    """交易对列表响应模型"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    symbols: list[dict[str, Any]] = Field(..., description="交易对列表")


# Timeframe配置相关模型
class SymbolTimeframeConfig(BaseModel):
    """交易对timeframe配置模型"""

    id: int = Field(..., description="配置ID")
    trading_symbol: str = Field(..., description="交易对符号")
    kline_timeframe: str = Field(..., description="K线时间周期")
    demark_buy: int = Field(..., description="DeMark买入信号阈值")
    demark_sell: int = Field(..., description="DeMark卖出信号阈值")

    # 百分比相关字段
    daily_max_percentage: float = Field(..., description="每日最大百分比")
    minimum_profit_percentage: float = Field(..., description="利润百分比")

    # 系数和延迟字段
    monitor_delay: float = Field(..., description="监控延迟")

    # 其他字段保持原样
    oper_mode: str = Field(..., description="操作模式")
    is_active: bool = Field(..., description="是否激活")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class UpdateTimeframeConfigRequest(BaseModel):
    """更新timeframe配置请求模型"""

    kline_timeframe: str | None = Field(None, description="K线时间周期")
    demark_buy: int | None = Field(None, description="DeMark买入信号阈值", ge=1, le=50)
    demark_sell: int | None = Field(None, description="DeMark卖出信号阈值", ge=1, le=50)

    # 百分比字段
    daily_max_percentage: float | None = Field(None, description="每日最大百分比")
    minimum_profit_percentage: float | None = Field(None, description="利润百分比")

    # 系数和延迟字段
    monitor_delay: float | None = Field(None, description="监控延迟")

    # 其他字段保持原样
    oper_mode: str | None = Field(None, description="操作模式")
    is_active: bool | None = Field(None, description="是否激活")


class BulkUpdatePercentagesRequest(BaseModel):
    """批量更新百分比与信号配置请求模型"""

    demark_buy: int | None = Field(None, description="新的买入信号阈值", ge=1, le=50)
    demark_sell: int | None = Field(None, description="新的卖出信号阈值", ge=1, le=50)
    minimum_profit_percentage: float | None = Field(
        None, description="新的利润百分比", ge=0.0, le=100.0
    )
    monitor_delay: float | None = Field(
        None, description="新的监控延迟(秒)", ge=0.0, le=60.0
    )

    def model_post_init(self, __context: Any) -> None:
        if (
            self.demark_buy is None
            and self.demark_sell is None
            and self.minimum_profit_percentage is None
            and self.monitor_delay is None
        ):
            raise ValueError("至少提供一个需要更新的字段")


class BulkUpdatePercentagesResponse(BaseModel):
    """批量更新百分比配置响应模型"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    updated_count: int = Field(..., description="受影响的配置数量")


class TimeframeConfigResponse(BaseModel):
    """timeframe配置操作响应模型"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: dict[str, Any] | None = Field(None, description="返回数据")


class TimeframeConfigListResponse(BaseModel):
    """timeframe配置列表响应模型"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    configs: list[dict[str, Any]] = Field(..., description="配置列表")


class TimeframeConfigsBySymbolResponse(BaseModel):
    """根据交易对获取配置的响应模型"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    configs: list[dict[str, Any]] = Field(..., description="配置列表")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    logger.info("⚙️ 配置数据模型")
    logger.info("定义系统配置相关的 Pydantic 数据模型")
    logger.info("- BinanceConfig - Binance配置模型")
    logger.info("- BinanceConfigResponse - Binance配置响应模型")
    logger.info("- UpdateBinanceConfigRequest - 更新Binance配置请求模型")
    logger.info("- LogLevelUpdateRequest - 日志级别更新请求模型")
    logger.info("- SymbolTimeframeConfig - 交易对时间周期配置模型")
    logger.info("- TimeframeConfigsResponse - 时间周期配置列表响应模型")
    logger.info("- TimeframeConfigsBySymbolResponse - 根据交易对获取配置响应模型")
