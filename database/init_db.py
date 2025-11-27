"""
数据库初始化脚本

专门负责创建数据库表,索引和触发器
应该在系统初始化时运行一次,而不是每次连接数据库都运行
"""

from loguru import logger

# 双重用途模块导入处理 - 唯一允许的 try-except
try:
    from .db_config import get_database_path, get_db_manager
    from .schema import create_all_tables
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    from db_config import get_database_path, get_db_manager
    from schema import create_all_tables


def init_database() -> None:
    """
    初始化数据库

    创建所有必要的表,索引和触发器
    这个函数应该在系统首次部署或升级时调用
    """
    logger.info("🗄️ 开始初始化数据库")

    # 获取数据库管理器
    db_manager = get_db_manager()

    # 创建所有表
    create_all_tables(db_manager)

    logger.info("✅ 数据库初始化完成")


def check_database_exists() -> bool:
    """
    检查数据库文件是否存在

    Returns:
        bool: 数据库文件是否存在
    """
    db_path = get_database_path()
    return db_path.exists()


def ensure_database_initialized() -> None:
    """
    确保数据库已初始化

    如果数据库不存在,则自动初始化
    这是一个安全的幂等操作
    """
    if not check_database_exists():
        logger.info("🔄 数据库不存在,自动初始化")
        init_database()
    else:
        logger.debug("✅ 数据库已存在")


if __name__ == "__main__":
    """数据库初始化命令行工具"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "init":
            logger.info("🗄️ 正在初始化数据库...")
            init_database()
            logger.info("✅ 数据库初始化完成")

        elif command == "check":
            exists = check_database_exists()
            if exists:
                logger.info("✅ 数据库文件存在")
            else:
                logger.info("❌ 数据库文件不存在")
                logger.info("请运行: uv run python database/init_db.py init")

        elif command == "ensure":
            logger.info("🔄 确保数据库已初始化...")
            ensure_database_initialized()
            logger.info("✅ 完成")

        else:
            logger.info(f"❌ 未知命令: {command}")
            logger.info("可用命令:")
            logger.info("  init   - 初始化数据库")
            logger.info("  check  - 检查数据库是否存在")
            logger.info("  ensure - 确保数据库已初始化")
    else:
        logger.info("数据库初始化工具")
        logger.info("用法: uv run python database/init_db.py <command>")
        logger.info("")
        logger.info("命令:")
        logger.info("  init   - 初始化数据库")
        logger.info("  check  - 检查数据库是否存在")
        logger.info("  ensure - 确保数据库已初始化")
