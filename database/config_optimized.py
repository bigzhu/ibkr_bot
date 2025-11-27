"""
优化版配置管理器
演示如何将多次单独查询合并为一次批量查询
"""

from loguru import logger
from pydantic import BaseModel

from .connection import DatabaseManager


class ApiConfigOptimized(BaseModel):
    """优化版API配置模型"""

    environment: str = "testnet"
    main_api_key: str | None = None
    main_secret_key: str | None = None
    test_api_key: str | None = None
    test_secret_key: str | None = None

    def get_api_key(self) -> str:
        """根据环境获取API密钥"""
        if self.environment == "testnet":
            if not self.test_api_key:
                error_msg = "测试网环境缺少API密钥配置"
                logger.critical(f"💥 {error_msg}")
                raise ValueError(error_msg)
            return self.test_api_key
        else:
            if not self.main_api_key:
                error_msg = "主网环境缺少API密钥配置"
                logger.critical(f"💥 {error_msg}")
                raise ValueError(error_msg)
            return self.main_api_key

    def get_secret_key(self) -> str:
        """根据环境获取Secret密钥"""
        if self.environment == "testnet":
            if not self.test_secret_key:
                error_msg = "测试网环境缺少Secret密钥配置"
                logger.critical(f"💥 {error_msg}")
                raise ValueError(error_msg)
            return self.test_secret_key
        else:
            if not self.main_secret_key:
                error_msg = "主网环境缺少Secret密钥配置"
                logger.critical(f"💥 {error_msg}")
                raise ValueError(error_msg)
            return self.main_secret_key

    def is_testnet(self) -> bool:
        """是否为测试网环境"""
        return self.environment == "testnet"


class ConfigManagerOptimized:
    """
    优化版配置管理器

    主要优化:
    1. 批量查询替代单独查询
    2. 减少数据库访问次数
    3. 提高性能
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    def get_system_configs_batch(self, keys: list[str]) -> dict[str, str | None]:
        """
        批量获取系统配置值

        Args:
            keys: 配置键名列表

        Returns:
            dict[str, str | None]: 配置键值对字典
        """
        if not keys:
            return {}

        try:
            # 构建 IN 查询语句
            placeholders = ",".join("?" * len(keys))
            sql = f"""
                SELECT key, value
                FROM system_configs
                WHERE key IN ({placeholders}) AND is_active = 1
            """

            results = self.db.execute_query(sql, tuple(keys))

            # 构建结果字典, 缺失的键设为 None
            config_dict = dict.fromkeys(keys)
            for row in results:
                config_dict[row["key"]] = row["value"]

            return config_dict

        except Exception as e:
            logger.error(
                f"❌ 批量获取系统配置失败: keys={keys}, 错误: {e}", exc_info=True
            )
            raise ValueError(f"批量获取系统配置失败: {e}") from e

    def get_api_config_optimized(self) -> ApiConfigOptimized:
        """
        优化版获取API配置

        使用一次批量查询替代5次单独查询

        Returns:
            ApiConfigOptimized: API配置模型
        """
        try:
            logger.debug("🔍 从数据库批量获取API配置")

            # 定义需要的配置键
            required_keys = [
                "ENVIRONMENT",
                "MAIN_MEXC_API_KEY",
                "MAIN_MEXC_SECRET_KEY",
                "TEST_MEXC_API_KEY",
                "TEST_MEXC_SECRET_KEY",
            ]

            # 一次性获取所有配置
            configs = self.get_system_configs_batch(required_keys)

            return ApiConfigOptimized(
                environment=configs.get("ENVIRONMENT") or "testnet",
                main_api_key=configs.get("MAIN_MEXC_API_KEY"),
                main_secret_key=configs.get("MAIN_MEXC_SECRET_KEY"),
                test_api_key=configs.get("TEST_MEXC_API_KEY"),
                test_secret_key=configs.get("TEST_MEXC_SECRET_KEY"),
            )

        except Exception as e:
            logger.error(f"❌ 获取API配置失败: {e}", exc_info=True)
            raise ValueError(f"获取API配置失败: {e}") from e


def get_config_manager_optimized(db_manager: DatabaseManager) -> ConfigManagerOptimized:
    """获取优化版配置管理器实例"""
    return ConfigManagerOptimized(db_manager)


if __name__ == "__main__":
    """优化版配置管理器性能对比测试"""
    import time
    from pathlib import Path
    from tempfile import TemporaryDirectory

    from .config import ConfigManager  # 原版配置管理器
    from .connection import DatabaseConfig, get_database_manager
    from .schema import create_all_tables

    logger.info("🔄 配置管理器性能对比测试")
    logger.info("=" * 50)

    with TemporaryDirectory() as temp_dir:
        # 创建测试数据库
        test_config = DatabaseConfig(db_path=Path(temp_dir) / "test_config_perf.db")

        db_manager = get_database_manager(test_config)
        create_all_tables(db_manager)

        # 初始化测试数据
        test_configs = [
            ("ENVIRONMENT", "testnet", "交易环境"),
            ("MAIN_MEXC_API_KEY", "main_api_123", "主网API密钥"),
            ("MAIN_MEXC_SECRET_KEY", "main_secret_456", "主网Secret密钥"),
            ("TEST_MEXC_API_KEY", "test_api_789", "测试网API密钥"),
            ("TEST_MEXC_SECRET_KEY", "test_secret_abc", "测试网Secret密钥"),
        ]

        for key, value, desc in test_configs:
            sql = "INSERT OR REPLACE INTO system_configs (key, value, description, is_active) VALUES (?, ?, ?, 1)"
            _ = db_manager.execute_update(sql, (key, value, desc))

        logger.info("📊 测试数据初始化完成")

        # 测试原版配置管理器
        original_manager = ConfigManager(db_manager)

        logger.info("\n🐌 原版配置管理器测试 (5次单独查询):")
        start_time = time.time()

        api_config_original = None
        for _ in range(10):  # 执行10次取平均
            api_config_original = original_manager.get_api_config()

        original_time = time.time() - start_time
        logger.info(f"   - 10次调用耗时: {original_time:.4f}秒")
        logger.info(f"   - 平均每次: {original_time / 10:.4f}秒")
        if api_config_original is not None:
            logger.info(
                f"   - 配置示例: {api_config_original.environment}, API Key: {api_config_original.test_api_key}"
            )

        # 测试优化版配置管理器
        optimized_manager = ConfigManagerOptimized(db_manager)

        logger.info("\n🚀 优化版配置管理器测试 (1次批量查询):")
        start_time = time.time()

        api_config_optimized = None
        for _ in range(10):  # 执行10次取平均
            api_config_optimized = optimized_manager.get_api_config_optimized()

        optimized_time = time.time() - start_time
        logger.info(f"   - 10次调用耗时: {optimized_time:.4f}秒")
        logger.info(f"   - 平均每次: {optimized_time / 10:.4f}秒")
        if api_config_optimized is not None:
            logger.info(
                f"   - 配置示例: {api_config_optimized.environment}, API Key: {api_config_optimized.test_api_key}"
            )

        # 性能对比
        if optimized_time > 0:
            improvement = ((original_time - optimized_time) / original_time) * 100
            logger.info(f"\n📈 性能提升: {improvement:.1f}%")
            logger.info(f"📉 速度提升: {original_time / optimized_time:.1f}x")

        logger.info("\n✅ 性能对比测试完成")
