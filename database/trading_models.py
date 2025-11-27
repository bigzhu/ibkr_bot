"""
交易相关数据模型

定义交易对和时间框架配置的Pydantic模型
"""

from datetime import datetime

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

from database.enums import OperMode


class TradingSymbol(BaseModel):
    """交易对模型"""

    id: int | None = None
    symbol: str = Field(..., description="交易对符号")
    base_asset: str = Field(..., description="基础资产")
    quote_asset: str = Field(..., description="计价资产")
    is_active: bool = Field(..., description="是否激活")
    description: str | None = Field(default=None, description="描述")
    base_asset_precision: int = Field(..., description="基础资产精度")
    quote_asset_precision: int = Field(..., description="计价资产精度")
    current_price: float = Field(..., description="当前价格")
    volume_24h: float = Field(..., description="24小时成交量")
    volume_24h_quote: float = Field(..., description="24小时成交额")
    price_change_24h: float = Field(..., description="24小时价格变化")
    high_24h: float = Field(..., description="24小时最高价")
    low_24h: float = Field(..., description="24小时最低价")
    min_qty: float = Field(..., description="最小数量")
    max_qty: float = Field(..., description="最大数量")
    step_size: float = Field(..., description="数量步长")
    min_notional: float = Field(..., description="最小名义价值")
    min_price: float = Field(..., description="最小价格")
    max_price: float = Field(..., description="最大价格")
    tick_size: float = Field(..., description="价格步长")
    last_updated_price: datetime | None = None
    max_fund: int | None = Field(default=None, description="最大资金")
    base_asset_balance: float = Field(default=0.0, description="基础资产余额")
    quote_asset_balance: float = Field(default=0.0, description="计价资产余额")
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """验证交易对符号格式"""
        if not v or len(v) < 5:
            raise ValueError("交易对符号格式无效")
        return v.upper()


class SymbolTimeframeConfig(BaseModel):
    """交易对时间框架配置模型"""

    id: int | None = None
    trading_symbol: str = Field(..., description="交易对符号")
    kline_timeframe: str = Field(..., description="K线时间周期")
    demark_buy: int = Field(..., description="DeMark买入信号阈值")
    demark_sell: int = Field(..., description="DeMark卖出信号阈值")
    daily_max_percentage: float = Field(..., description="每日最大百分比")
    monitor_delay: float = Field(..., description="监控延迟")
    oper_mode: OperMode = Field(..., description="操作模式")
    is_active: bool = Field(..., description="是否激活")
    minimum_profit_percentage: float = Field(..., description="最小利润百分比")
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("trading_symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """验证交易对符号格式"""
        if not v or len(v) < 5:
            raise ValueError("交易对符号格式无效")
        return v.upper()

    @field_validator("kline_timeframe")
    @classmethod
    def validate_timeframe(cls, v: str) -> str:
        """验证时间周期格式"""
        valid_timeframes = [
            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1h",
            "4h",
            "1d",
            "1W",
            "1M",
        ]
        if v not in valid_timeframes:
            raise ValueError(f"时间周期必须是: {valid_timeframes}")
        return v

    model_config = ConfigDict(use_enum_values=True)


if __name__ == "__main__":
    """交易模型测试"""
    logger.info("📈 交易相关数据模型")
    logger.info("定义交易对和时间框架配置的数据模型:")
    logger.info("- TradingSymbol: 交易对模型")
    logger.info("- SymbolTimeframeConfig: 时间框架配置模型")

    # 测试交易对模型
    symbol = TradingSymbol(
        symbol="ADAUSDC",
        base_asset="BTC",
        quote_asset="USDT",
        is_active=True,
        description="BTC/USDT交易对",
        base_asset_precision=8,
        quote_asset_precision=8,
        current_price=50000.0,
        volume_24h=1000.0,
        volume_24h_quote=50000000.0,
        price_change_24h=2.5,
        high_24h=51000.0,
        low_24h=49000.0,
        min_qty=0.000001,
        max_qty=9000.0,
        step_size=0.000001,
        min_notional=10.0,
        min_price=0.01,
        max_price=1000000.0,
        tick_size=0.01,
        max_fund=100000,
    )

    # 测试配置模型
    config = SymbolTimeframeConfig(
        trading_symbol="ADAUSDC",
        kline_timeframe="15m",
        demark_buy=9,
        demark_sell=9,
        daily_max_percentage=24.0,
        minimum_profit_percentage=0.5,
        monitor_delay=1.0,
        oper_mode=OperMode.ALL,
        is_active=True,
    )

    logger.info(
        f"\n测试模型: TradingSymbol({symbol.symbol}), SymbolTimeframeConfig({config.trading_symbol})"
    )
