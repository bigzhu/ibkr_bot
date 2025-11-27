"""
Binance API 模块

基于 Binance 官方 python-binance SDK 的简化 API 接口
遵循 CLAUDE.md 规范: 函数优先,禁止异常捕获,类型注解
遵循模块化设计模式: 纯函数,不对返回数据加工
"""

# 从共享模块导入输出工具
from shared.output_utils import print_json

from .common import (
    get_api_config_from_db,
    get_configured_client,
)

# 核心功能函数
from .get_account import account_info
from .get_balance import get_account_info, get_all_balances, get_balance
from .get_exchange_info import exchange_info, get_symbol_info
from .get_klines import klines
from .get_open_orders import get_open_orders
from .get_symbol_ticker import ticker_price
from .place_order import place_order, place_order_test

__all__ = [
    # 核心功能
    "account_info",
    "exchange_info",
    "get_account_info",
    "get_all_balances",
    "get_api_config_from_db",
    "get_balance",
    # 公共函数
    "get_configured_client",
    "get_open_orders",
    "get_symbol_info",
    "klines",
    "place_order",
    "place_order_test",
    "print_json",
    "ticker_price",
]
