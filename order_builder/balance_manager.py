"""用户余额管理模块

专门处理用户资产余额的获取,更新和管理.
遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except
"""

from decimal import Decimal

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m order_builder.balance_manager` 运行该模块, 无需手动修改 sys.path"
    )

from loguru import logger

from database.db_config import get_db_manager
from database.models import TradingSymbol
from ibkr_api.get_balance import get_balance
from shared.constants import BUY


def update_base_asset_balance(symbol: str, balance: Decimal) -> None:
    """更新交易对的基础资产余额到数据库

    Args:
        symbol: 交易对符号
        balance: 基础资产余额

    Raises:
        Exception: 数据库操作失败时抛出异常
    """
    db_manager = get_db_manager()
    with db_manager.transaction() as conn:
        _ = conn.execute(
            """
            UPDATE trading_symbols
            SET base_asset_balance = ?
            WHERE symbol = ?
        """,
            (float(balance), symbol),
        )
    logger.debug(f"📊 已更新 {symbol} 基础资产余额: {balance}")


def update_quote_asset_balance(symbol: str, balance: Decimal) -> None:
    """更新交易对的计价资产余额到数据库

    Args:
        symbol: 交易对符号
        balance: 计价资产余额

    Raises:
        Exception: 数据库操作失败时抛出异常
    """
    db_manager = get_db_manager()
    with db_manager.transaction() as conn:
        _ = conn.execute(
            """
            UPDATE trading_symbols
            SET quote_asset_balance = ?
            WHERE symbol = ?
        """,
            (float(balance), symbol),
        )
    logger.debug(f"📊 已更新 {symbol} 计价资产余额: {balance}")


def get_user_balance(
    symbol: str, signal_type: str, symbol_info: TradingSymbol
) -> Decimal:
    """获取用户余额

    根据信号类型获取对应的资产余额并更新数据库.

    Args:
        symbol: 交易对符号(如 ADAUSDC)
        signal_type: 信号类型(BUY/SELL)
        symbol_info: 交易对信息(必需参数)

    Returns:
        Decimal: 用户余额

    Raises:
        Exception: 获取失败时抛出异常
    """
    if signal_type == BUY:
        # BUY 单: 获取计价货币余额
        asset = symbol_info.quote_asset
        balance = Decimal(str(get_balance(asset)))
        logger.info(f"💰 {asset} 余额: {balance}")

        # 更新数据库中的计价资产余额
        update_quote_asset_balance(symbol, balance)
    else:  # SELL
        # SELL 单: 获取基础货币余额
        asset = symbol_info.base_asset
        balance = Decimal(str(get_balance(asset)))
        logger.info(f"💰 {asset} 余额: {balance}")

        # 更新数据库中的基础资产余额
        update_base_asset_balance(symbol, balance)

    return balance


if __name__ == "__main__":
    """测试余额管理功能"""
    pass
