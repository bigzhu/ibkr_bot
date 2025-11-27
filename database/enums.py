"""
数据库相关的枚举类型定义

定义系统中使用的所有枚举类型
"""

from enum import Enum

from loguru import logger


class OrderStatus(str, Enum):
    """订单状态枚举"""

    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class OrderType(str, Enum):
    """订单类型枚举"""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"


class OperMode(str, Enum):
    """操作模式枚举"""

    ALL = "all"
    BUY_ONLY = "buy_only"
    SELL_ONLY = "sell_only"


if __name__ == "__main__":
    """枚举类型测试"""
    logger.info("📋 数据库枚举类型模块")
    logger.info("定义系统中使用的所有枚举类型:")
    logger.info("- OrderStatus: 订单状态枚举")
    logger.info("- OrderType: 订单类型枚举")
    logger.info("- OperMode: 操作模式枚举")

    logger.info(f"\nOrderStatus 选项: {list(OrderStatus)}")
    logger.info(f"OrderType 选项: {list(OrderType)}")
    logger.info(f"OperMode 选项: {list(OperMode)}")
