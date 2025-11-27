"""
订单同步命令行入口 - 双重用途模块

提供独立运行的命令行界面,同时支持库模块导入.
遵循CLAUDE.md规范: 双重用途模块,CLI与核心逻辑分离.
"""

import sys
from pathlib import Path

from loguru import logger

if __name__ == "__main__":
    try:
        from shared.path_utils import ensure_project_root_for_script
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from shared.path_utils import ensure_project_root_for_script

    ensure_project_root_for_script(__file__)

from order_filler.sync import sync_orders_for_pair


def main() -> None:
    """订单同步命令行入口"""
    if len(sys.argv) < 2:
        logger.info("用法: p order_filler/sync/cli.py PAIR [LIMIT]")
        logger.info("示例: p order_filler/sync/cli.py ADAUSDC 500")
        sys.exit(1)

    pair = sys.argv[1].upper()
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 1000

    logger.info(f"🔄 Binance订单同步 - {pair}")

    # 执行同步
    sync_orders_for_pair(pair, limit)

    logger.info("✅ 订单同步完成")


if __name__ == "__main__":
    main()
