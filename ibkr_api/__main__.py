"""Binance API 模块主入口."""

import sys
from collections.abc import Callable

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m ibkr_api` 运行该入口, 无需手动修改 sys.path"
    )

from loguru import logger


def show_usage() -> None:
    """显示使用帮助"""
    logger.info("Binance API 模块使用指南")
    logger.info("=" * 50)
    logger.info("\n可用命令:")
    logger.info("  account                    - 查看账户信息")
    logger.info("  balance [ASSET]           - 查看余额")
    logger.info("  exchange [SYMBOL]         - 查看交易所信息")
    logger.info("  klines SYMBOL [INTERVAL]  - 查看K线数据")
    logger.info("  orders [SYMBOL]           - 查看未成交订单")
    logger.info("  price SYMBOL [TYPE]       - 查看价格信息")
    logger.info("  test                      - 测试API连接")
    logger.info("\n示例:")
    logger.info("  p -m ibkr_api account")
    logger.info("  p -m ibkr_api balance BTC")
    logger.info("  p -m ibkr_api price ADAUSDC")
    logger.info("  p -m ibkr_api klines ADAUSDC 1h")


def test_connection() -> bool:
    """测试API连接"""
    from ibkr_api.common import get_configured_client_with_config

    logger.info("🔧 Binance API连接测试")
    logger.info("=" * 50)

    logger.info("1. 获取API配置")
    client, config = get_configured_client_with_config()
    environment = config["environment"]
    logger.info(f"   ✅ 环境: {environment}")

    logger.info("2. 测试API连接")
    account = client.get_account()
    account_type = account.get("accountType", "SPOT")
    logger.info(f"   ✅ 连接成功, 账户类型: {account_type}")

    logger.info("✅ API连接测试完成")
    logger.info(f"🔧 环境: {environment}")
    return True


def main() -> None:
    """主入口函数 - 负责参数验证和模块调度"""
    command = _parse_command(sys.argv)
    if command is None:
        show_usage()
        return

    sys.argv = [sys.argv[0], *sys.argv[2:]]

    handlers: dict[str, Handler] = _command_handlers()
    handler = handlers.get(command)
    if handler is None:
        logger.error(f"❌ 未知命令: {command}")
        show_usage()
        return

    handler()


def _parse_command(argv: list[str]) -> str | None:
    if len(argv) < 2:
        return None
    command = argv[1].lower().strip()
    return command or None


Handler = Callable[[], None]


def _command_handlers() -> dict[str, Handler]:
    return {
        "test": _run_test,
        "account": _run_account,
        "balance": _run_balance,
        "exchange": _run_exchange,
        "klines": _run_klines,
        "orders": _run_orders,
        "price": _run_price,
    }


def _run_test() -> None:
    _ = test_connection()


def _run_account() -> None:
    from ibkr_api.get_account import main as account_main

    account_main()


def _run_balance() -> None:
    from ibkr_api.get_balance import main as balance_main

    balance_main()


def _run_exchange() -> None:
    from ibkr_api.get_exchange_info import main as exchange_main

    exchange_main()


def _run_klines() -> None:
    from ibkr_api.get_klines import main as klines_main

    klines_main()


def _run_orders() -> None:
    from ibkr_api.get_open_orders import main as orders_main

    orders_main()


def _run_price() -> None:
    from ibkr_api.get_symbol_ticker import main as price_main

    price_main()


if __name__ == "__main__":
    main()
