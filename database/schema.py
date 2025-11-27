"""
数据库表结构定义

定义所有数据库表的创建SQL语句.
金融系统要求:完整的约束和索引设计.
"""

from typing import Any

from loguru import logger

from .connection import DatabaseManager

# 说明: 原 admin_auth 表已废弃,认证改由 Web Admin 专用管理器处理

# 系统配置表
CREATE_SYSTEM_CONFIG_TABLE = """
CREATE TABLE IF NOT EXISTS system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT NOT NULL UNIQUE,
    config_value TEXT,
    config_type TEXT NOT NULL DEFAULT 'string',
    description TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    is_required BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

# 交易对表 - 存储交易对的基本信息和市场数据
CREATE_TRADING_SYMBOLS_TABLE = """
CREATE TABLE IF NOT EXISTS trading_symbols (
    -- 基础字段
    id INTEGER PRIMARY KEY AUTOINCREMENT,                -- 主键ID
    symbol TEXT NOT NULL UNIQUE,                         -- 交易对符号 (如: ADAUSDC)
    base_asset TEXT NOT NULL,                            -- 基础资产 (如: BTC)
    quote_asset TEXT NOT NULL,                           -- 计价资产 (如: USDT)
    is_active BOOLEAN DEFAULT TRUE,                      -- 是否启用交易
    description TEXT,                                    -- 交易对描述
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,      -- 创建时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,      -- 更新时间

    -- 精度相关字段 - 来自币安API /api/v3/exchangeInfo
    base_asset_precision INTEGER DEFAULT 8,             -- 基础资产精度 (小数位数)
    quote_asset_precision INTEGER DEFAULT 8,            -- 计价资产精度 (小数位数)

    -- 市场数据字段 - 来自币安API /api/v3/ticker/24hr
    current_price REAL DEFAULT 0,                       -- 当前最新成交价格
    volume_24h REAL DEFAULT 0,                          -- 24小时成交量 (基础资产)
    volume_24h_quote REAL DEFAULT 0,                    -- 24小时成交额 (计价资产)
    price_change_24h REAL DEFAULT 0,                    -- 24小时价格变动百分比
    high_24h REAL DEFAULT 0,                            -- 24小时最高价
    low_24h REAL DEFAULT 0,                             -- 24小时最低价

    -- 交易限制字段 - 来自币安API /api/v3/exchangeInfo 的filters
    min_qty REAL DEFAULT 0,                             -- 最小下单数量
    max_qty REAL DEFAULT 0,                             -- 最大下单数量
    step_size REAL DEFAULT 0,                           -- 数量精度步长 (下单数量必须为此值的倍数)
    min_notional REAL DEFAULT 0,                        -- 最小名义价值 (price * quantity)
    min_price REAL DEFAULT 0,                           -- 最小价格
    max_price REAL DEFAULT 0,                           -- 最大价格
    tick_size REAL DEFAULT 0,                           -- 价格精度步长 (价格必须为此值的倍数)

    -- 系统字段
    last_updated_price DATETIME,                        -- 价格数据最后更新时间
    max_fund INTEGER DEFAULT NULL,                      -- 最大资金限制 (本系统自定义字段)
    base_asset_balance REAL DEFAULT 0.0,                -- 基础资产余额 (如BTC数量)
    quote_asset_balance REAL DEFAULT 0.0,               -- 计价资产余额 (如USDT数量)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

# 交易对时间框架配置表
CREATE_SYMBOL_TIMEFRAME_CONFIGS_TABLE = """
CREATE TABLE IF NOT EXISTS symbol_timeframe_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,                    -- 主键ID
    trading_symbol TEXT NOT NULL,                            -- 交易对符号,如ADAUSDC
    kline_timeframe TEXT DEFAULT '15m',                      -- K线时间框架,如15m,1h,4h
    buy_interval_minutes INTEGER DEFAULT 60,                 -- 买入间隔(分钟)
    demark_buy INTEGER DEFAULT 9,                           -- DeMark买入信号阈值
    demark_sell INTEGER DEFAULT 9,                          -- DeMark卖出信号阈值
    daily_max_percentage REAL DEFAULT 24.0,                -- 日最大百分比(支持小数)
    demark_percentage_coefficient REAL DEFAULT 1.0,         -- DeMark百分比系数
    monitor_delay REAL DEFAULT 0.8,                         -- 监控延迟时间(秒)
    oper_mode TEXT DEFAULT 'all',                           -- 操作模式: all/buy/sell
    is_active BOOLEAN DEFAULT TRUE,                         -- 是否启用该配置
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,          -- 创建时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,          -- 更新时间
    minimum_profit_percentage REAL DEFAULT 0.4,             -- 最小利润百分比要求
    UNIQUE(trading_symbol, kline_timeframe)
);
"""


# 说明: 原 mexc_order_filler 表已废弃,请使用 filled_orders

# 已完成订单表 - 基于币安CSV导出格式
CREATE_FILLED_ORDERS_TABLE = """
CREATE TABLE IF NOT EXISTS filled_orders (
    -- 基础字段
    id INTEGER PRIMARY KEY AUTOINCREMENT,                -- 主键ID,系统自动生成
    date_utc TEXT NOT NULL,                              -- 订单创建时间(UTC): "2025-07-31 18:30:04"
    order_no TEXT NOT NULL UNIQUE,                       -- 订单号,币安系统唯一标识
    client_order_id TEXT,                                -- 客户端订单ID,由API调用者设置: "myOrder1", "abc123"
    pair TEXT NOT NULL,                                  -- 交易对符号: "ADAUSDC", "ETHUSDT"
    order_type TEXT NOT NULL,                            -- 订单类型: "LIMIT", "MARKET", "STOP_LOSS"
    side TEXT NOT NULL,                                  -- 交易方向: "BUY", "SELL"

    -- 价格和数量字段 (使用TEXT避免浮点精度问题)
    order_price TEXT NOT NULL,                           -- 挂单价格: "50000.00" (STOP_LOSS订单为"0")
    order_amount TEXT NOT NULL,                          -- 挂单数量: "0.1"
    executed TEXT NOT NULL,                              -- 交易完成数量: "0.1" (FILLED状态时等于order_amount)
    average_price REAL NOT NULL,                         -- 平均成交价格: "49999.50" (STOP_LOSS订单以此为准确成交价格)
    trading_total TEXT NOT NULL,                         -- 成交总额: "4999.95" (以计价货币计价,如USDT/USDC)

    -- 订单状态和时间
    time TEXT NOT NULL,                                  -- 订单完成时间(UTC): "2024-01-01 12:00:00"
    matched_time TEXT,                                   -- 撮合完成时间(UTC), BUY订单完全撮合后写入
    status TEXT NOT NULL,                                -- 订单状态: "FILLED" (仅存储已完成订单)

    -- 撮合相关字段
    unmatched_qty REAL DEFAULT 0,                        -- 未撮合数量,用于利润锁定计算

    -- 业务扩展字段
    profit TEXT DEFAULT '0',                             -- 利润金额: "10.50" (SELL订单记录交易闭环利润)
    commission TEXT DEFAULT '0',                         -- 手续费: "2.50" (本次订单的手续费)

    -- 系统字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,      -- 记录创建时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP       -- 记录最后更新时间
);
"""


# 交易日志表
CREATE_TRADING_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS trading_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    kline_timeframe TEXT NOT NULL,

    -- 正常情况下的字段
    demark INTEGER,                      -- DeMark信号值

    -- 挂单相关字段(仅在满足条件时记录)
    side TEXT,                           -- BUY/SELL
    price REAL,                          -- 挂单价格
    qty REAL,                            -- 挂单数量
    profit_lock_qty REAL,                -- 利润锁定数量
    order_id TEXT,                       -- 订单ID(如果挂单成功)
    open REAL,                           -- 信号K线开盘价
    high REAL,                           -- 信号K线最高价
    low REAL,                            -- 信号K线最低价
    close REAL,                          -- 信号K线收盘价

    -- 异常情况字段
    error TEXT,                          -- 错误信息

    -- DeMark计算相关字段
    demark_percentage_coefficient REAL,     -- DeMark百分比系数
    from_price REAL,                        -- 基准价格
    user_balance REAL,                      -- 用户余额

    -- 时间字段
    kline_time INTEGER,                      -- K线时间(Unix毫秒时间戳)
    run_time INTEGER,                        -- 运行时间(Unix毫秒时间戳)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- 价格分析字段
    price_change_percentage REAL DEFAULT NULL   -- 价格变化百分比
);
"""

# 订单撮合详情表
CREATE_ORDER_MATCHES_TABLE = """
CREATE TABLE IF NOT EXISTS order_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sell_order_no TEXT NOT NULL,           -- SELL单订单号
    buy_order_no TEXT NOT NULL,            -- BUY单订单号
    sell_price TEXT NOT NULL,              -- SELL单价格(使用TEXT避免精度问题)
    buy_price TEXT NOT NULL,               -- BUY单价格(使用TEXT避免精度问题)
    matched_qty TEXT NOT NULL,             -- 撮合数量(使用TEXT避免精度问题)
    profit TEXT NOT NULL,                  -- 单笔利润(使用TEXT避免精度问题)
    pair TEXT NOT NULL,                    -- 交易对
    timeframe TEXT NOT NULL,               -- 时间周期
    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# 回测K线数据表
CREATE_BACKTEST_KLINES_TABLE = """
CREATE TABLE IF NOT EXISTS backtest_klines (
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    open_time INTEGER NOT NULL,
    open_price TEXT NOT NULL,
    high_price TEXT NOT NULL,
    low_price TEXT NOT NULL,
    close_price TEXT NOT NULL,
    volume TEXT NOT NULL,
    close_time INTEGER NOT NULL,
    quote_asset_volume TEXT NOT NULL,
    number_of_trades INTEGER NOT NULL,
    taker_buy_base_asset_volume TEXT NOT NULL,
    taker_buy_quote_asset_volume TEXT NOT NULL,
    PRIMARY KEY (symbol, timeframe, open_time)
);
"""

# 索引定义
INDEXES = [
    # 交易对索引
    "CREATE INDEX IF NOT EXISTS idx_trading_symbols_symbol ON trading_symbols(symbol);",
    "CREATE INDEX IF NOT EXISTS idx_trading_symbols_active ON trading_symbols(is_active);",
    # 已完成订单索引
    "CREATE INDEX IF NOT EXISTS idx_filled_orders_pair ON filled_orders(pair);",
    "CREATE INDEX IF NOT EXISTS idx_filled_orders_status ON filled_orders(status);",
    "CREATE INDEX IF NOT EXISTS idx_filled_orders_time ON filled_orders(time);",
    "CREATE INDEX IF NOT EXISTS idx_filled_orders_matched_time ON filled_orders(matched_time);",
    "CREATE INDEX IF NOT EXISTS idx_filled_orders_order_no ON filled_orders(order_no);",
    "CREATE INDEX IF NOT EXISTS idx_filled_orders_side ON filled_orders(side);",
    "CREATE INDEX IF NOT EXISTS idx_filled_orders_pair_side_status_time ON filled_orders(pair, side, status, time);",
    "CREATE INDEX IF NOT EXISTS idx_filled_orders_pair_status_client ON filled_orders(pair, status, client_order_id);",
    "CREATE INDEX IF NOT EXISTS idx_filled_orders_pair_status_unmatched ON filled_orders(pair, status, unmatched_qty);",
    "CREATE INDEX IF NOT EXISTS idx_filled_orders_pair_side_matched_time ON filled_orders(pair, side, matched_time);",
    # 交易日志索引
    "CREATE INDEX IF NOT EXISTS idx_trading_logs_symbol_timeframe ON trading_logs(symbol, kline_timeframe);",
    "CREATE INDEX IF NOT EXISTS idx_trading_logs_symbol_timeframe_kline_time ON trading_logs(symbol, kline_timeframe, kline_time);",
    "CREATE INDEX IF NOT EXISTS idx_trading_logs_run_time ON trading_logs(run_time DESC);",
    # 订单撮合详情索引
    "CREATE INDEX IF NOT EXISTS idx_order_matches_sell_order ON order_matches(sell_order_no);",
    "CREATE INDEX IF NOT EXISTS idx_order_matches_buy_order ON order_matches(buy_order_no);",
    "CREATE INDEX IF NOT EXISTS idx_order_matches_pair ON order_matches(pair);",
    "CREATE INDEX IF NOT EXISTS idx_order_matches_timeframe ON order_matches(timeframe);",
    "CREATE INDEX IF NOT EXISTS idx_order_matches_matched_at ON order_matches(matched_at);",
    # 系统配置索引
    "CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);",
    "CREATE INDEX IF NOT EXISTS idx_system_config_active ON system_config(is_required);",
    # 配置表索引
    "CREATE INDEX IF NOT EXISTS idx_symbol_timeframe_configs_symbol ON symbol_timeframe_configs(trading_symbol);",
    "CREATE INDEX IF NOT EXISTS idx_symbol_timeframe_configs_active ON symbol_timeframe_configs(is_active);",
    # K线数据索引
    "CREATE INDEX IF NOT EXISTS idx_backtest_klines_symbol_timeframe_open_time ON backtest_klines(symbol, timeframe, open_time);",
]

# 触发器定义 - 自动更新时间戳
TRIGGERS = [
    """
    CREATE TRIGGER IF NOT EXISTS update_trading_symbols_timestamp
    AFTER UPDATE ON trading_symbols
    BEGIN
        UPDATE trading_symbols SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
    """,
    """
    CREATE TRIGGER IF NOT EXISTS update_timeframe_configs_timestamp
    AFTER UPDATE ON symbol_timeframe_configs
    BEGIN
        UPDATE symbol_timeframe_configs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
    """,
    """
    CREATE TRIGGER IF NOT EXISTS update_system_config_timestamp
    AFTER UPDATE ON system_config
    BEGIN
        UPDATE system_config SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
    """,
]

# 所有表创建语句
CREATE_TABLES = [
    CREATE_SYSTEM_CONFIG_TABLE,
    CREATE_TRADING_SYMBOLS_TABLE,
    CREATE_SYMBOL_TIMEFRAME_CONFIGS_TABLE,
    CREATE_FILLED_ORDERS_TABLE,
    CREATE_TRADING_LOGS_TABLE,
    CREATE_ORDER_MATCHES_TABLE,
    CREATE_BACKTEST_KLINES_TABLE,
]


def _create_tables_in_transaction(conn: Any) -> None:
    """在事务中创建所有表"""
    for table_sql in CREATE_TABLES:
        conn.execute(table_sql)
        logger.debug("✅ 表创建成功")


def _create_indexes_in_transaction(conn: Any) -> None:
    """在事务中创建所有索引"""
    for index_sql in INDEXES:
        conn.execute(index_sql)
        logger.debug("✅ 索引创建成功")


def _create_triggers_in_transaction(conn: Any) -> None:
    """在事务中创建所有触发器"""
    for trigger_sql in TRIGGERS:
        conn.execute(trigger_sql)
        logger.debug("✅ 触发器创建成功")


def create_all_tables(db_manager: DatabaseManager) -> None:
    """
    创建所有数据库表,索引和触发器

    Args:
        db_manager: 数据库管理器实例

    Raises:
        Exception: 数据库操作失败时抛出异常
    """
    with db_manager.transaction() as conn:
        _create_tables_in_transaction(conn)
        _create_indexes_in_transaction(conn)
        _create_triggers_in_transaction(conn)

    logger.info("🗄️ 所有数据库表,索引和触发器创建完成")


def _get_table_drop_order() -> list[str]:
    """获取表删除的正确顺序(先删除有外键约束的表)"""
    return [
        "backtest_klines",
        "trading_logs",  # 有外键约束,先删除
        "symbol_timeframe_configs",  # 有外键约束,先删除
        "order_matches",  # 撮合详情表
        "filled_orders",  # 订单表
        "trading_symbols",
        "system_config",
    ]


def drop_all_tables(db_manager: DatabaseManager) -> None:
    """
    删除所有数据库表(用于测试和重置)

    Args:
        db_manager: 数据库管理器实例

    Raises:
        Exception: 数据库操作失败时抛出异常
    """
    table_names = _get_table_drop_order()

    with db_manager.transaction() as conn:
        for table_name in table_names:
            _ = conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            logger.debug(f"✅ 表 {table_name} 删除成功")

    logger.info("🗑️ 所有数据库表删除完成")


def get_table_info(db_manager: DatabaseManager) -> dict[str, list[dict[str, object]]]:
    """
    获取所有表的结构信息

    Args:
        db_manager: 数据库管理器实例

    Returns:
        包含所有表结构信息的字典
    """
    table_info: dict[str, list[dict[str, object]]] = {}

    try:
        # 获取所有表名
        tables = db_manager.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )

        for table_row in tables:
            table_name = table_row["name"]

            # 获取表结构
            columns = db_manager.execute_query(f"PRAGMA table_info({table_name})")
            table_info[table_name] = [dict(column) for column in columns]

        logger.info(f"📊 获取到 {len(table_info)} 个表的结构信息")
        return table_info

    except Exception as e:
        logger.error(f"❌ 获取表信息失败: {e}", exc_info=True)
        raise ValueError(f"获取表信息失败: {e}") from e


if __name__ == "__main__":
    """数据库表结构测试"""
    from pathlib import Path
    from tempfile import TemporaryDirectory

    from .connection import DatabaseConfig, get_database_manager

    with TemporaryDirectory() as temp_dir:
        # 创建测试数据库配置
        test_config = DatabaseConfig(db_path=Path(temp_dir) / "test_schema.db")

        # 获取数据库管理器
        db_manager = get_database_manager(test_config)

        # 创建所有表
        create_all_tables(db_manager)

        # 获取表信息
        table_info = get_table_info(db_manager)

        logger.info("数据库表结构:")
        for table_name, columns in table_info.items():
            logger.info(f"\n📋 {table_name}:")
            for col in columns:
                logger.info(
                    f"  - {col['name']}: {col['type']} {'(主键)' if col['pk'] else ''}"
                )

        # 测试删除表
        drop_all_tables(db_manager)

        # 验证表已删除
        final_tables = db_manager.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        logger.info(f"\n删除后剩余表数: {len(final_tables)}")

        logger.info("✅ 数据库表结构测试完成")
