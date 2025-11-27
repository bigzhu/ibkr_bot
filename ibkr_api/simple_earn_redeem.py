"""
CLI 工具: 赎回 Simple Earn 活期理财资产

用法:
    uv run python ibkr_api/simple_earn_redeem.py USDC 100
    # 或者赎回全部:
    uv run python ibkr_api/simple_earn_redeem.py USDC --all
"""

from __future__ import annotations

import argparse
from decimal import Decimal

from loguru import logger

from ibkr_api.simple_earn import redeem_flexible_asset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple Earn 活期赎回工具")
    _ = parser.add_argument("asset", help="资产符号 (如 USDC)")
    _ = parser.add_argument(
        "amount",
        nargs="?",
        type=Decimal,
        default=None,
        help="赎回数量, 不填则必须指定 --all",
    )
    _ = parser.add_argument(
        "--all",
        action="store_true",
        help="赎回全部活期持仓, amount 参数可省略",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.all:
        amount = Decimal("1e18")  # 足够大的值, redeem 函数会自动取 min
        logger.info(f"准备赎回 {args.asset.upper()} 的全部活期持仓")
    else:
        if args.amount is None:
            raise ValueError("未提供赎回数量, 必须指定数值或使用 --all")
        amount = args.amount
        logger.info(f"准备赎回 {amount} {args.asset.upper()}")

    redeemed = redeem_flexible_asset(args.asset, amount)
    logger.info(f"实际提交赎回数量: {redeemed} {args.asset.upper()}")


if __name__ == "__main__":
    main()
