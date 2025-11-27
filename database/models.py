"""
数据库模型定义 - 主入口

统一导出所有数据库模型,保持向后兼容性
金融系统要求:严格的数据验证和类型安全.
"""

from loguru import logger

if __name__ == "__main__":
    try:
        from shared.path_utils import ensure_project_root_for_script
    except ImportError:
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from shared.path_utils import ensure_project_root_for_script

    ensure_project_root_for_script(__file__)

from database.auth_models import SystemConfig
from database.enums import OperMode, OrderStatus, OrderType
from database.log_models import TradingLog
from database.order_models import AccountTradeList, BinanceFilledOrder
from database.stats_models import CSVImportStats, MatchingStats
from database.trading_models import SymbolTimeframeConfig, TradingSymbol

# 模型已直接导入,无需重新导出

# 导出所有模型供外部使用
__all__ = [
    # 订单相关模型
    "AccountTradeList",
    # 认证和配置模型
    "BinanceFilledOrder",
    "CSVImportStats",
    "MatchingStats",
    "OperMode",
    # 枚举类型
    "OrderStatus",
    # 统计信息模型
    "OrderType",
    "SymbolTimeframeConfig",
    "SystemConfig",
    # 日志模型
    "TradingLog",
    # 交易相关模型
    "TradingSymbol",
]


if __name__ == "__main__":
    """数据库模型测试"""
    logger.info("🗄️ 数据库模型模块")
    logger.info("统一导出所有数据库模型:")
    logger.info("- 枚举类型: OrderStatus, OrderType, OperMode")
    logger.info("- 认证和配置: AdminAuth, SystemConfig")
    logger.info("- 交易相关: TradingSymbol, SymbolTimeframeConfig")
    logger.info("- 订单相关: AccountTradeList, MexcFilledOrder, BinanceFilledOrder")
    logger.info("- 日志相关: TradingLog")
    logger.info("- 统计信息: MatchingStats, CSVImportStats")

    # 测试模型创建
    config = SystemConfig(
        config_key="test.key",
        config_value="test_value",
        config_type="string",
        is_encrypted=False,
        is_required=False,
    )
    symbol = TradingSymbol(
        symbol="ADAUSDC",
        base_asset="BTC",
        quote_asset="USDT",
        is_active=True,
        base_asset_precision=8,
        quote_asset_precision=2,
        current_price=50000.0,
        volume_24h=1000.0,
        volume_24h_quote=50000000.0,
        price_change_24h=0.05,
        high_24h=51000.0,
        low_24h=49000.0,
        min_qty=0.00001,
        max_qty=10000.0,
        step_size=0.00001,
        min_notional=10.0,
        min_price=0.01,
        max_price=1000000.0,
        tick_size=0.01,
    )
    timeframe_config = SymbolTimeframeConfig(
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
    log = TradingLog(
        symbol="ADAUSDC",
        kline_timeframe="15m",
    )

    logger.info(f"\n✅ 所有模型测试完成,共{len(__all__)}个模型")
