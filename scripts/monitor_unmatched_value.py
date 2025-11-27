#!/usr/bin/env python3
"""
监控指定交易对未匹配订单价值变化

默认每0.5秒查询一次数据库, 监控未匹配买单的总价值变化
当检测到值增加时, 输出新的最大值

使用方法:
- 运行监控(默认 1m ADAUSDC): p scripts/monitor_unmatched_value.py
- 指定时间周期: p scripts/monitor_unmatched_value.py 5m
- 指定时间周期和交易对: p scripts/monitor_unmatched_value.py 15m DOGEUSDC
- 指定查询间隔: p scripts/monitor_unmatched_value.py --interval 0.2
- 停止监控: Ctrl+C
"""

import argparse
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

from database.db_config import get_db_manager
from shared.timeframe_utils import timeframe_candidates
from shared.timeframes import SUPPORTED_TIMEFRAMES


class UnmatchedValueMonitor:
    """未匹配订单价值监控器"""

    def __init__(self, timeframe: str, pair: str, interval: float) -> None:
        self.db_manager = get_db_manager()
        self.max_value: float = 0.0
        self.timeframe = timeframe
        self.pair = pair.upper()
        self.interval = interval
        self.client_order_ids = timeframe_candidates(self.timeframe)
        self.local_tz = datetime.now().astimezone().tzinfo
        placeholders = ", ".join("?" for _ in self.client_order_ids)
        self.query = f"""
        SELECT
            SUM(unmatched_qty * average_price) AS total_value,
            MAX(date_utc) AS latest_date_utc
        FROM filled_orders
        WHERE pair = ?
        AND side = 'BUY'
        AND unmatched_qty > 0
        AND status = 'FILLED'
        AND (client_order_id IS NULL OR client_order_id IN ({placeholders}))
        ORDER BY time DESC
        """
        self.query_params: tuple[str, ...] = (self.pair, *self.client_order_ids)

    def get_current_value(self) -> tuple[float, str | None]:
        """
        查询当前未匹配订单总价值

        Returns:
            (当前总价值, 最新未匹配订单时间UTC字符串)
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(self.query, self.query_params)
                result = cursor.fetchone()

                if not result:
                    return 0.0, None

                total_value = result["total_value"]
                latest_date_utc = result["latest_date_utc"]

                value_float = float(total_value) if total_value is not None else 0.0
                date_str = str(latest_date_utc) if latest_date_utc else None
                return value_float, date_str

        except Exception as e:
            logger.error(f"查询数据库失败: {e}")
            return 0.0, None

    def check_and_update(self) -> None:
        """检查并更新最大值"""
        current_value, latest_date_utc = self.get_current_value()

        if current_value > self.max_value:
            time_suffix = ""
            if latest_date_utc:
                local_time = self._format_local_time(latest_date_utc)
                time_suffix = f", 本地时间: {local_time}"

            logger.info(
                f"🔥 检测到 {self.pair} {self.timeframe} 新最大值: {current_value:.6f} USDC (之前: {self.max_value:.6f}){time_suffix}"
            )
            self.max_value = current_value
        else:
            logger.trace(
                f"{self.pair} {self.timeframe} 当前值: {current_value:.6f}, 最大值: {self.max_value:.6f}"
            )

    def run(self) -> None:
        """启动监控循环"""
        logger.info(f"🚀 开始监控 {self.pair} {self.timeframe} 未匹配订单价值变化")
        logger.info(f"💡 每{self.interval:.2f}秒查询一次, 按 Ctrl+C 停止监控")

        # 初始化最大值
        initial_value, _ = self.get_current_value()
        self.max_value = initial_value
        logger.info(f"📊 {self.timeframe} 初始值: {self.max_value:.6f} USDC")

        try:
            while True:
                self.check_and_update()
                time.sleep(self.interval)

        except KeyboardInterrupt:
            logger.info("👋 监控已停止")
        except Exception as e:
            logger.error(f"监控过程中发生错误: {e}")

    def _format_local_time(self, utc_str: str) -> str:
        """将 UTC 字符串转换为当前时区时间显示."""
        try:
            utc_dt = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
        except ValueError:
            logger.debug(f"无法解析 date_utc 字段: {utc_str}")
            return utc_str

        if self.local_tz is None:
            return utc_dt.isoformat()

        local_dt = utc_dt.astimezone(self.local_tz)
        return local_dt.strftime("%Y-%m-%d %H:%M:%S %Z")


def parse_args(argv: list[str]) -> tuple[str, str, float]:
    """解析命令行参数并返回归一化时间周期,交易对与查询间隔"""
    parser = argparse.ArgumentParser(
        description="监控指定时间周期和交易对的未匹配订单价值变化"
    )
    parser.add_argument(
        "timeframe",
        nargs="?",
        default="1m",
        help="监控的时间周期, 如 1m 或 5m",
        metavar="TIMEFRAME",
    )
    parser.add_argument(
        "pair",
        nargs="?",
        default="ADAUSDC",
        help="监控的交易对, 如 ADAUSDC 或 DOGEUSDC",
        metavar="SYMBOL",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.4,
        help="数据库查询间隔(秒), 默认为 0.5 秒",
    )

    args = parser.parse_args(argv)
    timeframe = args.timeframe.lower()
    allowed = {tf.lower() for tf in SUPPORTED_TIMEFRAMES}
    if timeframe not in allowed:
        allowed_display = ", ".join(sorted(allowed))
        parser.error(f"不支持的时间周期: {args.timeframe}. 支持: {allowed_display}")
    pair = args.pair.strip().upper()
    if not pair:
        parser.error("交易对不能为空, 例如 ADAUSDC")
    if args.interval <= 0:
        parser.error("查询间隔必须大于 0 秒")

    return timeframe, pair, args.interval


def main() -> None:
    """主函数"""
    timeframe, pair, interval = parse_args(sys.argv[1:])
    monitor = UnmatchedValueMonitor(timeframe=timeframe, pair=pair, interval=interval)
    monitor.run()


if __name__ == "__main__":
    main()
