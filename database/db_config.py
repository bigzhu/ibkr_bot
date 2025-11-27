"""
数据库统一配置模块

项目中所有数据库路径的唯一入口点.
遵循单一职责原则,统一管理数据库配置.
"""

import sys
from pathlib import Path

from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection import (
    DatabaseConfig,
    DatabaseManager,
    get_database_manager,
    reset_database_manager,
)


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent


def get_database_path() -> Path:
    """
    获取数据库文件路径 - 项目唯一配置入口

    Returns:
        数据库文件的完整路径
    """
    return get_project_root() / "data" / "bot.db"


def get_default_database_config() -> DatabaseConfig:
    """
    获取默认数据库配置

    Returns:
        标准数据库配置对象
    """
    return DatabaseConfig(
        db_path=get_database_path(),
        timeout=30.0,
        check_same_thread=False,
        enable_foreign_keys=True,
    )


def get_db_manager() -> DatabaseManager:
    """
    获取默认数据库管理器实例

    Returns:
        使用默认配置的数据库管理器
    """
    return get_database_manager(get_default_database_config())


def get_in_memory_database_config() -> DatabaseConfig:
    """构建内存数据库配置"""
    return DatabaseConfig(
        db_path=Path(":memory:"),
        timeout=30.0,
        check_same_thread=False,
        enable_foreign_keys=True,
    )


def use_in_memory_database() -> DatabaseManager:
    """切换到内存数据库(用于回测)"""
    return reset_database_manager(get_in_memory_database_config())


if __name__ == "__main__":
    """测试数据库配置"""

    # 测试路径获取
    db_path = get_database_path()
    logger.info(f"数据库路径: {db_path}")
    logger.info(f"项目根目录: {get_project_root()}")

    # 测试配置获取
    config = get_default_database_config()
    logger.info(f"数据库配置: {config}")

    logger.info("✅ 数据库配置模块测试完成")
