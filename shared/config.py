"""
共享配置模块

统一管理应用配置,支持环境变量和默认值
避免在代码中硬编码配置信息
"""

import os
from pathlib import Path

from loguru import logger


def _load_env_file() -> None:
    """加载 .env 文件中的环境变量"""
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        return

    try:
        with env_file.open(encoding="utf-8") as file:
            for raw_line in file:
                parsed = _parse_env_line(raw_line)
                if not parsed:
                    continue
                key, value = parsed
                if key and not os.getenv(key):
                    os.environ[key] = value
    except Exception:
        # 忽略 .env 文件读取错误
        pass


def _parse_env_line(raw_line: str) -> tuple[str, str] | None:
    """解析单行环境变量记录"""
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
        return None

    key_part, value_part = line.split("=", 1)
    key = _normalize_env_key(key_part)
    if not key:
        return None

    value = _sanitize_env_value(value_part.strip())
    return key, value


def _normalize_env_key(raw_key: str) -> str:
    """处理 export 前缀并标准化键名"""
    key = raw_key.strip()
    if key.startswith("export "):
        _, _, remainder = key.partition(" ")
        return remainder.strip()
    return key


def _sanitize_env_value(value: str) -> str:
    """移除注释与围绕的引号"""
    if not value:
        return ""

    if value[0] not in {'"', "'"} and "#" in value:
        value = value.split("#", 1)[0].strip()

    if _is_wrapped_by_quotes(value):
        return value[1:-1]

    return value


def _is_wrapped_by_quotes(value: str) -> bool:
    """判断值是否由成对引号包裹"""
    if len(value) < 2:
        return False
    if value[0] not in {'"', "'"}:
        return False
    return value[-1] == value[0]


# 模块导入时自动加载环境变量
_load_env_file()


class Config:
    """应用配置类"""

    @staticmethod
    def get_web_admin_host() -> str:
        """获取 Web Admin API 服务主机地址"""
        return os.getenv("WEB_ADMIN_HOST", "localhost")

    @staticmethod
    def get_web_admin_port() -> str:
        """获取 Web Admin API 服务端口"""
        # 优先显式端口
        port = os.getenv("WEB_ADMIN_PORT")
        if port:
            return port
        # 基于环境自动选择: lead -> 8001, 其他 -> 8000
        remote = os.getenv("REMOTE_DIR_NAME", "").strip().lower()
        if remote == "lead":
            return os.getenv("LEAD_API_PORT", "8001")
        # 默认 bot
        return os.getenv("BOT_API_PORT", "8000")

    @staticmethod
    def get_web_admin_base_url() -> str:
        """获取 Web Admin API 服务基础URL"""
        host = Config.get_web_admin_host()
        port = Config.get_web_admin_port()
        return f"http://{host}:{port}"

    @staticmethod
    def get_internal_events_url(endpoint: str) -> str:
        """
        获取内部事件通知URL

        Args:
            endpoint: 端点路径(如 'trading-log-created')

        Returns:
            完整的事件通知URL
        """
        base_url = Config.get_web_admin_base_url()
        return f"{base_url}/api/v1/internal/events/{endpoint}"

    @staticmethod
    def get_database_path() -> Path | None:
        """获取数据库文件路径"""
        db_path_env = os.getenv("DATABASE_PATH")
        if db_path_env:
            return Path(db_path_env)
        return None

    @staticmethod
    def get_log_level() -> str:
        """获取日志级别"""
        return os.getenv("LOG_LEVEL", "INFO")

    @staticmethod
    def is_development() -> bool:
        """判断是否为开发环境"""
        return os.getenv("ENVIRONMENT", "development").lower() in ["development", "dev"]

    @staticmethod
    def is_production() -> bool:
        """判断是否为生产环境"""
        return os.getenv("ENVIRONMENT", "development").lower() in ["production", "prod"]

    @staticmethod
    def get_admin_jwt_secret() -> str:
        """获取管理端 JWT 密钥(默认仅用于开发环境)"""
        return os.getenv("ADMIN_JWT_SECRET", "dev-admin-jwt-secret")


if __name__ == "__main__":
    """配置模块测试"""
    logger.info("📋 当前配置信息:")
    logger.info(f"Web Admin Host: {Config.get_web_admin_host()}")
    logger.info(f"Web Admin Port: {Config.get_web_admin_port()}")
    logger.info(f"Base URL: {Config.get_web_admin_base_url()}")
    logger.info(f"Log Level: {Config.get_log_level()}")
    logger.info(
        f"Environment: {'Development' if Config.is_development() else 'Production'}"
    )
    logger.info("\n📡 内部事件URL:")
    logger.info(
        f"Trading Log Created: {Config.get_internal_events_url('trading-log-created')}"
    )
    logger.info(
        f"Trading Log Updated: {Config.get_internal_events_url('trading-log-updated')}"
    )
