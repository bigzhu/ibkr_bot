"""
数据库模块

提供统一的数据库访问层,支持SQLite数据库.
包含连接管理,表结构定义,CRUD操作和数据迁移功能.

主要功能:
- 线程安全的数据库连接池
- 完整的表结构和约束定义
- 所有业务实体的CRUD操作
- 数据库迁移和版本管理
- 事务管理和错误处理

数据库设计原则:
- 金融数据零容忍:任何数据异常都立即失败
- 完整性约束:外键,检查约束,唯一约束
- 性能优化:适当的索引设计
- 审计跟踪:时间戳和触发器

使用方式:
```python
from database import get_database_manager, DatabaseConfig
from database.schema import create_all_tables

# 初始化数据库
from .db_config import get_default_database_config, get_db_manager
db_config = get_default_database_config()
db_manager = get_db_manager()
create_all_tables(db_manager)
```
"""

# 导出主要接口
from .config import ApiConfig, ConfigManager
from .connection import DatabaseConfig, DatabaseManager, get_database_manager
from .crud import (
    create_symbol_timeframe_config,
    create_trading_log,
    create_trading_symbol,
    get_recent_trading_logs,
    get_symbol_info,
    get_symbol_timeframe_config,
)
from .models import (
    OperMode,
    OrderStatus,
    OrderType,
    SymbolTimeframeConfig,
    SystemConfig,
    TradingLog,
    TradingSymbol,
)
from .schema import create_all_tables, drop_all_tables, get_table_info

__all__ = [
    # 数据模型
    # 配置管理
    "ApiConfig",
    "ConfigManager",
    # 连接管理
    "DatabaseConfig",
    "DatabaseManager",
    "OperMode",
    "OrderStatus",
    "OrderType",
    "SymbolTimeframeConfig",
    "SystemConfig",
    "TradingLog",
    "TradingSymbol",
    # CRUD操作
    # 表结构管理
    "create_all_tables",
    "create_symbol_timeframe_config",
    "create_trading_log",
    "create_trading_symbol",
    "drop_all_tables",
    "get_database_manager",
    "get_recent_trading_logs",
    "get_symbol_info",
    "get_symbol_timeframe_config",
    "get_table_info",
]
