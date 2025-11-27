"""
数据库连接管理器

提供线程安全的数据库连接池和事务管理.
金融系统要求: 严格的数据一致性和完整性保证.
"""

import sqlite3
import threading
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from loguru import logger
from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    """数据库配置模型"""

    db_path: Path
    timeout: float = 30.0
    check_same_thread: bool = False
    enable_foreign_keys: bool = True


class DatabaseManager:
    """
    线程安全的数据库连接管理器

    Features:
    - 连接池管理
    - 自动事务处理
    - 外键约束启用
    - 连接超时配置
    """

    def __init__(self, config: DatabaseConfig) -> None:
        self.config = config
        self._local = threading.local()
        self._lock = threading.Lock()

        # 确保数据库目录存在 (内存数据库无须创建)
        if str(self.config.db_path) != ":memory:":
            self.config.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_database()

    def _init_database(self) -> None:
        """初始化数据库连接和基础设置"""
        with self.get_connection() as conn:
            # 启用外键约束
            if self.config.enable_foreign_keys:
                _ = conn.execute("PRAGMA foreign_keys = ON")

            # 设置 WAL 模式提高并发性能
            _ = conn.execute("PRAGMA journal_mode = WAL")

            # 设置同步模式
            _ = conn.execute("PRAGMA synchronous = FULL")

            conn.commit()

    def _get_local_connection(self) -> sqlite3.Connection:
        """获取线程本地连接"""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(self.config.db_path),
                timeout=self.config.timeout,
                check_same_thread=self.config.check_same_thread,
            )
            # 设置行工厂为字典模式
            self._local.connection.row_factory = sqlite3.Row

            logger.trace(f"🔗 创建新的数据库连接: {threading.current_thread().name}")

        connection = self._local.connection
        if not isinstance(connection, sqlite3.Connection):
            raise RuntimeError("Database connection is not valid")
        return connection

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        获取数据库连接的上下文管理器

        自动处理连接的获取和释放, 确保连接正确关闭.
        """
        conn = self._get_local_connection()
        try:
            yield conn
        finally:
            # 连接不在这里关闭, 由线程结束时清理
            pass

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        事务上下文管理器

        自动处理事务的开始,提交和回滚.
        金融系统要求: 确保数据一致性.
        """
        conn = self._get_local_connection()
        try:
            _ = conn.execute("BEGIN")
            yield conn
            conn.commit()
            logger.trace("✅ 事务提交成功")
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ 事务回滚: {e}", exc_info=True)
            raise ValueError(f"数据库事务失败: {e}") from e

    def execute_query(
        self, query: str, params: tuple[object, ...] = ()
    ) -> list[sqlite3.Row]:
        """
        执行查询并返回结果 - 遵循fail-fast原则,异常直接向上传播

        Args:
            query: SQL 查询语句
            params: 查询参数

        Returns:
            查询结果列表
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            results = cursor.fetchall()
            logger.trace(f"🔍 查询执行成功, 返回 {len(results)} 条记录")
            return results

    def execute_update(self, query: str, params: tuple[object, ...] = ()) -> int:
        """
        执行更新操作并返回影响的行数 - 遵循fail-fast原则,异常直接向上传播

        Args:
            query: SQL 更新语句
            params: 更新参数

        Returns:
            影响的行数
        """
        with self.transaction() as conn:
            cursor = conn.execute(query, params)
            rowcount = cursor.rowcount
            logger.trace(f"📝 更新执行成功, 影响 {rowcount} 行")
            return rowcount

    def close(self) -> None:
        """关闭所有连接"""
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
            logger.trace("🔒 数据库连接已关闭")


# 全局数据库管理器实例
_db_manager: DatabaseManager | None = None
_init_lock = threading.Lock()


def get_database_manager(config: DatabaseConfig | None = None) -> DatabaseManager:
    """
    获取全局数据库管理器实例

    Args:
        config: 数据库配置, 首次调用时必须提供

    Returns:
        数据库管理器实例

    Raises:
        ValueError: 配置缺失或初始化失败时抛出
    """
    global _db_manager

    if _db_manager is None:
        with _init_lock:
            if _db_manager is None:
                if config is None:
                    error_msg = "首次调用必须提供数据库配置"
                    logger.critical(f"💥 {error_msg}")
                    raise ValueError(error_msg)

                _db_manager = DatabaseManager(config)

    return _db_manager


def reset_database_manager(config: DatabaseConfig) -> DatabaseManager:
    """
    重置全局数据库管理器, 允许在运行时切换数据库配置.

    Args:
        config: 新的数据库配置

    Returns:
        DatabaseManager: 重新初始化的数据库管理器
    """
    global _db_manager

    with _init_lock:
        if _db_manager is not None:
            _db_manager.close()
        _db_manager = DatabaseManager(config)

    return _db_manager


if __name__ == "__main__":
    """数据库连接管理器测试"""
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as temp_dir:
        # 创建测试配置
        test_config = DatabaseConfig(db_path=Path(temp_dir) / "test.db")

        # 测试数据库管理器
        db_manager = get_database_manager(test_config)

        # 测试基本操作
        with db_manager.transaction() as conn:
            _ = conn.execute(
                """
                CREATE TABLE test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    value REAL
                )
            """
            )

        # 测试插入
        rows_affected = db_manager.execute_update(
            "INSERT INTO test_table (name, value) VALUES (?, ?)", ("test", 123.45)
        )
        logger.info(f"插入影响行数: {rows_affected}")

        # 测试查询
        results = db_manager.execute_query("SELECT * FROM test_table")
        logger.info(f"查询结果: {[dict(row) for row in results]}")

        # 测试连接关闭
        db_manager.close()

        logger.info("✅ 数据库连接管理器测试完成")
