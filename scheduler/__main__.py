"""
整点调度器入口 - 函数式调度器

功能:
1. 每分钟整点(0秒)运行一次
2. 从trading_configs查询满足当前整点时间周期的配置
3. 对每个配置执行demark计算并输出结果

用法:
    p scheduler.py        # 启动调度器
    p scheduler.py test   # 立即测试执行一次
"""

import asyncio
import sys
from pathlib import Path

from loguru import logger

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入函数式调度器
from scheduler import run_once_now, start_scheduler


async def main() -> None:
    """主函数 - 调度器入口"""
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help", "help"]:
            logger.info(__doc__)
            return
        elif sys.argv[1] == "test":
            # 测试模式 - 立即执行一次
            _ = await run_once_now()
            return

    # 正常启动调度器
    await start_scheduler()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n程序已被用户中断")
        sys.exit(0)
