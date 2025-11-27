"""
数据库配置管理

从数据库读取系统配置,包括MEXC API密钥等
遵循金融数据零容忍原则:配置缺失必须立即失败
"""

from loguru import logger
from pydantic import BaseModel

from .connection import DatabaseManager


class ApiConfig(BaseModel):
    """API配置模型"""

    environment: str = "testnet"  # testnet or mainnet
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


class ConfigManager:
    """
    配置管理器

    从数据库读取系统配置,提供类型安全的配置访问
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    def get_system_config(self, key: str) -> str | None:
        """
        获取系统配置值 - 遵循fail-fast原则,异常直接向上传播

        Args:
            key: 配置键名

        Returns:
            str | None: 配置值,不存在时返回None
        """
        sql = "SELECT value FROM system_configs WHERE key = ? AND is_active = 1"
        results = self.db.execute_query(sql, (key,))

        if results:
            return results[0]["value"]

        return None

    def set_system_config(self, key: str, value: str, description: str = "") -> None:
        """
        设置系统配置 - 遵循fail-fast原则,异常直接向上传播

        Args:
            key: 配置键名
            value: 配置值
            description: 配置描述
        """
        sql = """
            INSERT OR REPLACE INTO system_configs (key, value, description, is_active)
            VALUES (?, ?, ?, 1)
        """

        _ = self.db.execute_update(sql, (key, value, description))

    def get_api_config(self) -> ApiConfig:
        """
        获取API配置 - 遵循fail-fast原则,异常直接向上传播

        Returns:
            ApiConfig: API配置模型
        """

        return ApiConfig(
            environment=self.get_system_config("ENVIRONMENT") or "testnet",
            main_api_key=self.get_system_config("MAIN_MEXC_API_KEY"),
            main_secret_key=self.get_system_config("MAIN_MEXC_SECRET_KEY"),
            test_api_key=self.get_system_config("TEST_MEXC_API_KEY"),
            test_secret_key=self.get_system_config("TEST_MEXC_SECRET_KEY"),
        )

    def is_api_configured(self) -> bool:
        """检查API是否已配置 - 遵循fail-fast原则,异常直接向上传播"""
        api_config = self.get_api_config()

        if api_config.is_testnet():
            return bool(api_config.test_api_key and api_config.test_secret_key)
        else:
            return bool(api_config.main_api_key and api_config.main_secret_key)

    def init_default_configs(self) -> None:
        """初始化默认配置"""
        default_configs = [
            ("ENVIRONMENT", "testnet", "交易环境:testnet或mainnet"),
            ("TEST_MEXC_API_KEY", "", "测试网API密钥"),
            ("TEST_MEXC_SECRET_KEY", "", "测试网Secret密钥"),
            ("MAIN_MEXC_API_KEY", "", "主网API密钥"),
            ("MAIN_MEXC_SECRET_KEY", "", "主网Secret密钥"),
        ]

        for key, value, description in default_configs:
            existing = self.get_system_config(key)
            if existing is None:
                self.set_system_config(key, value, description)


if __name__ == "__main__":
    """配置管理器测试"""
    from pathlib import Path
    from tempfile import TemporaryDirectory

    from .connection import DatabaseConfig, get_database_manager
    from .schema import create_all_tables

    logger.info("🔄 配置管理器测试")
    logger.info("=" * 40)

    with TemporaryDirectory() as temp_dir:
        # 创建测试数据库
        test_config = DatabaseConfig(db_path=Path(temp_dir) / "test_config.db")

        db_manager = get_database_manager(test_config)
        create_all_tables(db_manager)

        # 测试配置管理器
        config_manager = ConfigManager(db_manager)

        logger.info("1. 初始化默认配置")
        config_manager.init_default_configs()

        logger.info("2. 设置测试配置")
        config_manager.set_system_config(
            "TEST_MEXC_API_KEY", "test_api_key_123", "测试用的API密钥"
        )
        config_manager.set_system_config(
            "TEST_MEXC_SECRET_KEY", "test_secret_key_456", "测试用的Secret密钥"
        )

        logger.info("3. 获取配置")
        api_key = config_manager.get_system_config("TEST_MEXC_API_KEY")
        logger.info(f"   - API密钥: {api_key}")

        logger.info("4. 获取API配置")
        api_config = config_manager.get_api_config()
        logger.info(f"   - 环境: {api_config.environment}")
        logger.info(f"   - 是否测试网: {api_config.is_testnet()}")
        logger.info(f"   - API已配置: {config_manager.is_api_configured()}")

        try:
            current_api_key = api_config.get_api_key()
            current_secret_key = api_config.get_secret_key()
            logger.info(f"   - 当前API密钥: {current_api_key}")
            logger.info(f"   - 当前Secret密钥: {current_secret_key}")
        except ValueError as e:
            logger.info(f"   - 配置获取失败: {e}")

        logger.info("\n✅ 配置管理器测试完成")
