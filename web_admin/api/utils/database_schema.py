"""
Web Admin 数据库表结构初始化
为Web Admin API创建必要的数据库表
"""

from typing import Any

from loguru import logger

from database.db_config import get_db_manager


def _create_trading_symbols_table(conn: Any) -> None:
    """创建交易对表"""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS trading_symbols (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL UNIQUE,
            base_asset TEXT NOT NULL,
            quote_asset TEXT NOT NULL,
            base_asset_precision INTEGER DEFAULT 8,
            quote_asset_precision INTEGER DEFAULT 8,
            is_active BOOLEAN DEFAULT TRUE,
            description TEXT,
            current_price REAL DEFAULT 0.0,
            volume_24h REAL DEFAULT 0.0,
            volume_24h_quote REAL DEFAULT 0.0,
            price_change_24h REAL DEFAULT 0.0,
            high_24h REAL DEFAULT 0.0,
            low_24h REAL DEFAULT 0.0,
            min_qty REAL DEFAULT 0.0,
            max_qty REAL DEFAULT 0.0,
            step_size REAL DEFAULT 0.0,
            min_notional REAL DEFAULT 0.0,
            min_price REAL DEFAULT 0.0,
            max_price REAL DEFAULT 0.0,
            tick_size REAL DEFAULT 0.0,
            last_updated_price REAL DEFAULT 0.0,
            max_fund REAL DEFAULT 0.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )


def _create_symbol_timeframe_configs_table(conn: Any) -> None:
    """创建时间周期配置表"""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS symbol_timeframe_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trading_symbol TEXT NOT NULL,
            kline_timeframe TEXT NOT NULL,
            buy_interval_minutes INTEGER DEFAULT 60,
            demark_buy INTEGER DEFAULT 14,
            demark_sell INTEGER DEFAULT 14,
            daily_max_percentage REAL DEFAULT 24,
            demark_percentage_coefficient REAL DEFAULT 1.5,
            minimum_profit_percentage REAL DEFAULT 0.5,
            monitor_delay INTEGER DEFAULT 60,
            oper_mode TEXT DEFAULT 'monitor',
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(trading_symbol, kline_timeframe),
            FOREIGN KEY (trading_symbol) REFERENCES trading_symbols(symbol)
        )
    """
    )


def _create_web_admin_indexes(conn: Any) -> None:
    """创建 Web Admin 相关索引"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_trading_symbols_symbol ON trading_symbols(symbol)",
        "CREATE INDEX IF NOT EXISTS idx_trading_symbols_active ON trading_symbols(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_symbol_timeframe_configs_symbol ON symbol_timeframe_configs(trading_symbol)",
        "CREATE INDEX IF NOT EXISTS idx_symbol_timeframe_configs_timeframe ON symbol_timeframe_configs(kline_timeframe)",
        "CREATE INDEX IF NOT EXISTS idx_symbol_timeframe_configs_active ON symbol_timeframe_configs(is_active)",
    ]

    for index_sql in indexes:
        conn.execute(index_sql)


def create_web_admin_tables() -> bool:
    """
    创建Web Admin需要的数据库表

    Returns:
        bool: 是否创建成功
    """
    db_manager = get_db_manager()

    with db_manager.get_connection() as conn:
        # 1. 创建交易对表
        _create_trading_symbols_table(conn)

        # 2. 创建时间周期配置表
        _create_symbol_timeframe_configs_table(conn)

        # 3. 创建索引
        _create_web_admin_indexes(conn)

        conn.commit()
        logger.info("✅ Web Admin 数据库表创建成功")
        return True


def insert_sample_data() -> bool:
    """
    插入示例数据用于测试

    Returns:
        bool: 是否插入成功
    """
    db_manager = get_db_manager()

    with db_manager.get_connection() as conn:
        # 检查是否已有数据
        cursor = conn.execute("SELECT COUNT(*) FROM trading_symbols")
        if cursor.fetchone()[0] > 0:
            logger.info("数据库中已有交易对数据,跳过示例数据插入")
            return True

        # 插入示例交易对
        sample_symbols = [
            ("ADAUSDC", "BTC", "USDT", "比特币/USDT"),
            ("ETHUSDT", "ETH", "USDT", "以太坊/USDT"),
            ("BNBUSDT", "BNB", "USDT", "BNB/USDT"),
        ]

        for symbol, base, quote, desc in sample_symbols:
            _ = conn.execute(
                """
                INSERT OR IGNORE INTO trading_symbols
                (symbol, base_asset, quote_asset, description, is_active)
                VALUES (?, ?, ?, ?, TRUE)
            """,
                (symbol, base, quote, desc),
            )

        # 插入示例时间周期配置 (使用MEXC支持的格式)
        sample_timeframes = ["1m", "3m", "5m", "15m", "30m", "1h", "4h"]

        for symbol, _, _, _ in sample_symbols:
            for timeframe in sample_timeframes:
                _ = conn.execute(
                    """
                    INSERT OR IGNORE INTO symbol_timeframe_configs
                    (trading_symbol, kline_timeframe, is_active)
                    VALUES (?, ?, TRUE)
                """,
                    (symbol, timeframe),
                )

        conn.commit()
        logger.info("✅ 示例数据插入成功")
        return True


def initialize_web_admin_database() -> bool:
    """
    初始化Web Admin数据库(创建表和插入示例数据)

    Returns:
        bool: 是否初始化成功
    """
    logger.info("🔧 开始初始化 Web Admin 数据库...")

    # 创建表结构
    if not create_web_admin_tables():
        return False

    # 插入示例数据
    if not insert_sample_data():
        return False

    logger.info("🎉 Web Admin 数据库初始化完成")
    return True


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    logger.info("🗄️ Web Admin 数据库表结构初始化")

    # 执行初始化
    success = initialize_web_admin_database()

    if success:
        logger.info("✅ 数据库初始化成功!")

        # 测试查询
        from .database_helpers import get_all_timeframe_configs, get_all_trading_symbols

        symbols = get_all_trading_symbols()
        configs = get_all_timeframe_configs()

        logger.info(f"📊 创建了 {len(symbols)} 个交易对")
        logger.info(f"⏰ 创建了 {len(configs)} 个时间周期配置")
    else:
        logger.info("❌ 数据库初始化失败!")
