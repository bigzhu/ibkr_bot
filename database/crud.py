"""
数据库CRUD操作 - 主入口

统一导出所有数据库表的增删改查操作
金融系统要求:严格的数据验证和错误处理
"""

from loguru import logger

# 导入所有CRUD模块的函数
from .symbol_crud import (
    build_deletion_result,
    cascade_delete_related_data,
    create_symbol_timeframe_config,
    create_trading_symbol,
    delete_trading_symbol,
    get_symbol_by_id,
    get_symbol_info,
    get_symbol_timeframe_config,
)
from .trading_log_crud import (
    create_trading_log,
    get_recent_trading_logs,
    update_trading_log,
)

# 导出所有函数供外部使用
__all__ = [
    "build_deletion_result",
    "cascade_delete_related_data",
    "create_symbol_timeframe_config",
    "create_trading_log",
    "create_trading_symbol",
    "delete_trading_symbol",
    "get_recent_trading_logs",
    "get_symbol_by_id",
    "get_symbol_info",
    "get_symbol_timeframe_config",
    "update_trading_log",
]


if __name__ == "__main__":
    """CRUD操作测试"""
    from pathlib import Path
    from tempfile import TemporaryDirectory

    from .connection import DatabaseConfig, get_database_manager
    from .models import TradingSymbol
    from .schema import create_all_tables

    with TemporaryDirectory() as temp_dir:
        # 创建测试数据库
        test_config = DatabaseConfig(db_path=Path(temp_dir) / "test_crud.db")
        db_manager = get_database_manager(test_config)
        create_all_tables(db_manager)

        # 测试交易对CRUD
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
        symbol_id = create_trading_symbol(db_manager, symbol)
        retrieved_symbol = get_symbol_info("ADAUSDC")
        logger.info(f"交易对测试: {retrieved_symbol}")

        logger.info("✅ CRUD操作测试完成")
