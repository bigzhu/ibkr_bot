"""
Binance API 公共函数

提供可复用的数据库连接, API 配置, 客户端创建等功能, 遵循 fail-fast 原则.
"""

from decimal import Decimal
from pathlib import Path
from typing import Any

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m ibkr_api.common` 运行该模块, 无需手动修改 sys.path"
    )

from binance.client import Client
from loguru import logger

from database.db_config import get_db_manager

# 简单的配置缓存, 避免重复数据库查询
_config_cache: dict[str, Any] | None = None
# 简单的客户端缓存, 避免重复创建与握手
_client_cache: Client | None = None


def get_api_config_from_db() -> dict[str, Any]:
    """从数据库获取 Binance API 配置, 缓存并返回."""

    global _config_cache

    if _config_cache is not None:
        return _config_cache

    db = get_db_manager()
    rows = db.execute_query(
        """
        SELECT config_key, config_value
        FROM system_config
        WHERE config_key IN ('MAIN_BINANCE_API_KEY', 'MAIN_BINANCE_SECRET_KEY', 'BINANCE_TESTNET')
        """
    )

    config_map = {row["config_key"]: row["config_value"] for row in rows}

    api_key = config_map.get("MAIN_BINANCE_API_KEY")
    secret_key = config_map.get("MAIN_BINANCE_SECRET_KEY")
    if not api_key or not secret_key:
        raise ValueError("Binance API 配置不完整, 请在 system_config 中设置密钥")

    raw_testnet = config_map.get("BINANCE_TESTNET", "false")
    testnet = raw_testnet.lower() == "true"

    config_dict = {
        "api_key": api_key,
        "secret_key": secret_key,
        "testnet": testnet,
        "environment": "testnet" if testnet else "mainnet",
    }
    _config_cache = config_dict
    return config_dict


def get_configured_client() -> Client:
    """获取已配置的Binance客户端

    Returns:
        Client: Binance客户端

    Raises:
        ValueError: 当API配置未找到时
    """
    global _client_cache

    # 复用已创建的客户端
    if _client_cache is not None:
        return _client_cache

    api_config = get_api_config_from_db()

    if not api_config:
        raise ValueError("Binance API配置未找到,请先配置API密钥")

    _client_cache = Client(
        api_key=api_config["api_key"],
        api_secret=api_config["secret_key"],
        testnet=api_config["testnet"],
    )
    return _client_cache


def get_configured_client_with_config() -> tuple[Client, dict[str, Any]]:
    """获取已配置的Binance客户端和配置信息

    Returns:
        tuple: (client, config)

    Raises:
        ValueError: 当API配置未找到时
    """
    # 复用单例客户端, 同时返回已缓存/获取的配置
    api_config = get_api_config_from_db()

    if not api_config:
        raise ValueError("Binance API配置未找到,请先配置API密钥")

    client = get_configured_client()
    return client, api_config


def reset_client_cache() -> None:
    """重置已缓存的Binance客户端(测试或更换配置时使用)."""
    global _client_cache
    _client_cache = None


def print_api_setup_help() -> None:
    """打印API设置帮助信息"""
    logger.error("❌ Binance API密钥未配置")


def get_current_price(client: Client, symbol: str) -> Decimal:
    """获取交易对当前价格 - fail-fast原则

    统一的价格获取函数,消除项目中的代码重复

    Args:
        client: 币安客户端
        symbol: 交易对符号

    Returns:
        Decimal: 当前价格

    Raises:
        任何币安API异常直接向上传播,遵循fail-fast原则
    """
    ticker = client.get_symbol_ticker(symbol=symbol.upper())
    return Decimal(str(ticker["price"]))


if __name__ == "__main__":
    """测试公共函数 - 遵循金融系统fail-fast原则, 不捕获任何异常"""
    logger.info("🔧 Binance API公共函数测试")

    logger.info("1. 测试项目路径")
    project_root = Path(__file__).parent.parent
    from database.db_config import get_database_path

    db_path = get_database_path()
    logger.info(f"   ✅ 项目根目录: {project_root}")
    logger.info(f"   ✅ 数据库路径: {db_path}")

    logger.info("2. 测试API配置获取")
    client, config = get_configured_client_with_config()
    if not client or not config:
        print_api_setup_help()
        exit(1)

    environment = config["environment"]
    logger.info(f"   ✅ API配置已就绪, 环境: {environment}")

    # 测试API连接 - 不捕获异常, 失败时立即终止
    logger.info("3. 测试API连接")
    account = client.get_account()  # 任何异常都会导致程序终止
    account_type = account.get("accountType", "SPOT")
    logger.info(f"   ✅ API连接成功, 账户类型: {account_type}")

    logger.info("✅ 公共函数测试完成")
    logger.info(f"🔧 环境: {environment}")
