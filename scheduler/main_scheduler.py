"""
主调度逻辑 - 纯函数式调度器实现 (仅进程池模式)

功能:
1. 整合时间匹配,配置查询,DeMark信号处理
2. 每分钟整点执行DeMark信号检测
3. 使用 ProcessPoolExecutor 复用执行器, 不再支持子进程 stdout 解析

用法:
    p main_scheduler.py  # 启动调度器
环境:
    SCHEDULER_MAX_PROCESSES  配置进程池大小, 默认 14
    SCHEDULER_WORKER_LOG_LEVEL 子进程日志级别, 默认 WARNING
    SCHEDULER_LOG_STYLE      日志风格 concise|normal, 默认 normal
"""

import asyncio
import concurrent.futures
import contextlib
import os
import sys
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any, cast

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# 执行时长保护: 保证批次能在一分钟内完成
PER_TASK_TIMEOUT_SECONDS = 50.0

from shared.logger_utils import setup_scheduler_logger

setup_scheduler_logger()

from loguru import logger

if __name__ == "__main__":
    try:
        from shared.path_utils import ensure_project_root_for_script
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from shared.path_utils import ensure_project_root_for_script

    ensure_project_root_for_script(__file__)

from database import get_database_manager
from database.db_config import get_default_database_config
from scheduler.config_loader import get_active_configs_by_timeframes
from scheduler.timeframe_matcher import get_matched_timeframes

# 执行模式: 仅进程池
MAX_PROCESSES = int(os.getenv("SCHEDULER_MAX_PROCESSES", "14"))

_process_pool: concurrent.futures.ProcessPoolExecutor | None = None
WORKER_LOG_LEVEL = os.getenv("SCHEDULER_WORKER_LOG_LEVEL", "WARNING").upper()
LOG_STYLE = os.getenv("SCHEDULER_LOG_STYLE", "normal").lower()


def _init_worker_logger() -> None:
    """进程池子进程日志初始化: 默认抑制到 WARNING, 保持主进程输出简洁"""
    try:
        import sys as _wsys

        from loguru import logger as _wlogger

        _wlogger.remove()
        # 使用较高等级以减少噪音; 格式极简
        _ = _wlogger.add(
            _wsys.stdout,
            level=WORKER_LOG_LEVEL,
            format="{message}",
        )
    except Exception:
        # 安静失败, 避免影响任务
        pass


"""仅进程池执行模式; 子进程执行路径已移除"""


def _get_process_pool() -> concurrent.futures.ProcessPoolExecutor:
    global _process_pool
    if _process_pool is None:
        _process_pool = concurrent.futures.ProcessPoolExecutor(
            max_workers=MAX_PROCESSES,
            initializer=_init_worker_logger,
        )
        logger.info(f"已初始化进程池, workers={MAX_PROCESSES}")
    return _process_pool


# 子进程执行模式已移除; 统一使用进程池复用执行器


def _create_signal_result(
    symbol: str,
    timeframe: str,
    config_id: int,
    action: str,
    signal_value: int,
    end_time: datetime,
    duration: float,
) -> dict[str, Any]:
    """创建信号处理结果"""
    return {
        "timestamp": end_time.isoformat(),
        "config_id": config_id,
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "success": True,
        "action": action,
        "signal_value": signal_value,
        "duration_seconds": round(duration, 3),
    }


async def process_demark_signal(
    symbol: str, timeframe: str, config_id: int
) -> dict[str, Any]:
    """
    处理单个配置的订单构建流程

    Args:
        symbol: 交易对符号
        timeframe: 时间周期
        config_id: 配置ID

    Returns:
        订单构建执行结果
    """
    start_time = datetime.now()

    # 此处不做 monitor_delay 等待; 由下游数据层自行保证K线完整性

    # 仅使用进程池复用, 避免每任务冷启动
    from order_builder.app import run_order_builder
    from shared.types.order_builder import OrderPlacedResult, RunResult

    loop = asyncio.get_running_loop()
    try:
        result_dict = await asyncio.wait_for(
            loop.run_in_executor(
                _get_process_pool(), partial(run_order_builder, symbol, timeframe)
            ),
            timeout=PER_TASK_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        timeout_result = _create_signal_result(
            symbol, timeframe, config_id, "TIMEOUT", 0, end_time, duration
        )
        logger.warning(
            "任务超时(进程池) {}-{} (>{}s)",
            symbol,
            timeframe,
            PER_TASK_TIMEOUT_SECONDS,
        )
        return timeout_result

    res_any: Any = result_dict
    if not isinstance(res_any, dict):
        raise RuntimeError("订单构建返回结果无效")

    result_data = cast(RunResult, res_any)

    action = str(result_data.get("action", "UNKNOWN"))
    signal_value = int(result_data.get("signal_value", 0) or 0)
    extras: dict[str, Any] = {}
    if action == "ORDER_PLACED":
        placed = cast("OrderPlacedResult", result_data)
        extras["qty"] = placed["qty"]
        extras["price"] = placed["price"]
        extras["order_id"] = placed["order_id"]
    # 不从子结果中读取耗时; 调度器自行统计批内耗时

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    signal_result = _create_signal_result(
        symbol, timeframe, config_id, action, signal_value, end_time, duration
    )

    extra_part = ""
    if extras.get("order_id") is not None:
        extra_part = f", 订单={extras.get('order_id')}, 数量={extras.get('qty')}, 价格={extras.get('price')}"
    if LOG_STYLE == "concise":
        info_msg = f"{symbol}-{timeframe} 动作={action} 值={signal_value}, 耗时={duration:.3f}s{extra_part}"
    else:
        info_msg = (
            f"✅ 完成处理 {symbol}-{timeframe} - "
            f"耗时: {duration:.3f}s, 结果值={signal_value}, 动作={action}{extra_part} - "
            f"{end_time.strftime('%H:%M:%S.%f')[:-3]}"
        )
    logger.info(info_msg)
    return signal_result


async def process_configs_concurrent(
    active_configs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    并发处理所有活跃配置 - fail-fast策略

    Args:
        active_configs: 活跃配置列表

    Returns:
        处理结果列表

    Note:
        遵循fail-fast原则, 任何配置处理失败都会导致整个批次失败
        这确保数据完整性, 避免部分成功的不一致状态
    """
    if not active_configs:
        return []

    batch_start_time = datetime.now()

    # 保留原设计: 每个子进程独立同步与撮合,不做批前预同步

    # 创建并发任务 - 使用asyncio.create_task确保真正并发
    tasks: list[asyncio.Task[dict[str, Any]]] = []
    for config in active_configs:
        task = asyncio.create_task(
            process_demark_signal(
                config["trading_symbol"],
                config["kline_timeframe"],
                config["id"],
            )
        )
        tasks.append(task)

    # 并发执行 - 捕获取消异常避免中断时的错误堆栈
    try:
        results_tuple = await asyncio.gather(*tasks)
        results: list[dict[str, Any]] = list(results_tuple)
    except asyncio.CancelledError:
        # 任务被取消时,取消所有未完成的任务
        for task in tasks:
            if not task.done():
                _ = task.cancel()
        # 等待所有任务完成清理
        _ = await asyncio.gather(*tasks, return_exceptions=True)
        raise

    batch_end_time = datetime.now()
    batch_duration = (batch_end_time - batch_start_time).total_seconds()

    # 计算统计信息
    total_individual_time = sum(r.get("duration_seconds", 0) for r in results)
    parallelism_ratio = (
        total_individual_time / batch_duration if batch_duration > 0 else 0
    )

    if LOG_STYLE == "concise":
        summary_msg = f"batch 耗时={batch_duration:.3f}s, 总和={total_individual_time:.3f}s, 并行={parallelism_ratio:.1f}x"
    else:
        summary_msg = (
            f"🎉 并发处理完成 - 总耗时: {batch_duration:.3f}s, "
            f"单独耗时总和: {total_individual_time:.3f}s, "
            f"并行效率: {parallelism_ratio:.1f}x - "
            f"{batch_end_time.strftime('%H:%M:%S.%f')[:-3]}"
        )
    logger.info(summary_msg)

    return results


def _check_matched_timeframes(
    current_time: datetime,
) -> tuple[list[str], dict[str, Any] | None]:
    """检查匹配的时间周期"""
    matched_timeframes = get_matched_timeframes(current_time)
    if not matched_timeframes:
        empty_timeframes: list[str] = []
        result: dict[str, Any] = {
            "batch_timestamp": current_time.isoformat(),
            "matched_timeframes": empty_timeframes,
            "total_configs": 0,
            "message": "当前时间无匹配的时间周期",
        }
        return [], result

    return matched_timeframes, None


def _get_active_configs(
    db_manager: Any, matched_timeframes: list[str], current_time: datetime
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """获取活跃配置"""
    active_configs = get_active_configs_by_timeframes(db_manager, matched_timeframes)
    if not active_configs:
        result = {
            "batch_timestamp": current_time.isoformat(),
            "matched_timeframes": matched_timeframes,
            "total_configs": 0,
            "message": "无活跃的交易配置",
        }
        return [], result

    return active_configs, None


def _build_final_result(
    current_time: datetime,
    matched_timeframes: list[str],
    active_configs: list[dict[str, Any]],
    processing_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """构建最终结果"""
    result = {
        "batch_timestamp": current_time.isoformat(),
        "matched_timeframes": matched_timeframes,
        "total_configs": len(active_configs),
        "results": processing_results,
        "summary": {
            "total_processed": len(processing_results),
            "success_count": len(processing_results),
            "error_count": 0,
        },
    }

    final_msg = (
        f"整点任务完成: 总配置={len(active_configs)}, "
        f"成功={len(processing_results)}, 失败=0"
    )
    logger.info(final_msg)

    return result


async def execute_minute_task(db_manager: Any) -> dict[str, Any]:
    """执行每分钟的整点任务 - 纯函数实现"""
    current_time = datetime.now(UTC)

    # 1. 获取匹配的时间周期
    matched_timeframes, early_result = _check_matched_timeframes(current_time)
    if early_result:
        return early_result

    # 2. 查询活跃配置
    active_configs, early_result = _get_active_configs(
        db_manager, matched_timeframes, current_time
    )
    if early_result:
        return early_result

    # 3. 并发处理所有配置 - 异常向上传播, fail-fast策略
    processing_results = await process_configs_concurrent(active_configs)

    # 4. 构建完整结果
    return _build_final_result(
        current_time, matched_timeframes, active_configs, processing_results
    )


def create_minute_task_handler(db_manager: Any) -> Any:
    """
    创建分钟任务处理器

    Args:
        db_manager: 数据库管理器

    Returns:
        异步任务处理函数
    """

    async def minute_task_handler() -> None:
        """每分钟整点执行的任务处理器 - 捕获取消异常避免调度器报错"""
        try:
            _ = await execute_minute_task(db_manager)
        except asyncio.CancelledError:
            # 静默处理取消异常, 避免 apscheduler 报错
            return
        except Exception as e:
            logger.error("任务执行异常: {}", str(e), exc_info=True)
            # 其他异常继续向上传播, 保持 fail-fast 原则
            raise

    return minute_task_handler


def _setup_scheduler_and_task(db_manager: Any) -> tuple[Any, Any]:
    """初始化调度器和任务"""
    scheduler = cast(Any, AsyncIOScheduler())
    task_handler = create_minute_task_handler(db_manager)

    scheduler.add_job(
        func=task_handler,
        trigger=CronTrigger(second=0),  # 每分钟的0秒执行
        id="minute_order_builder_task",
        name="每分钟订单构建任务",
        max_instances=1,  # 避免并发叠加执行
        coalesce=True,  # 合并错过的触发,不追赶补跑
        misfire_grace_time=30,  # 超过30秒则跳过本次
        replace_existing=True,
    )

    return scheduler, task_handler


async def _run_scheduler_loop(scheduler: Any) -> None:
    """运行调度器主循环"""
    scheduler.start()

    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        await _shutdown_scheduler_gracefully(scheduler)


async def _shutdown_scheduler_gracefully(scheduler: Any) -> None:
    """优雅关闭调度器"""
    try:
        scheduler.shutdown(wait=True)  # 等待正在执行的任务完成
    except Exception:
        # 如果优雅关闭失败, 强制关闭
        scheduler.shutdown(wait=False)

    # 给一点时间让异步任务清理
    with contextlib.suppress(asyncio.CancelledError):
        await asyncio.sleep(0.1)

    # 关闭进程池
    global _process_pool
    if _process_pool is not None:
        try:
            _process_pool.shutdown(wait=True, cancel_futures=True)
            logger.info("进程池已关闭")
        except Exception:
            with contextlib.suppress(Exception):
                _process_pool.shutdown(wait=False, cancel_futures=True)
        finally:
            _process_pool = None


async def start_scheduler() -> None:
    """
    启动调度器 - 主函数

    这是一个纯函数式的调度器启动器, 不使用类
    """
    db_manager = get_database_manager(get_default_database_config())
    scheduler, _ = _setup_scheduler_and_task(db_manager)

    logger.info("整点调度器初始化完成")
    await _run_scheduler_loop(scheduler)


async def run_once_now(db_manager: Any = None) -> dict[str, Any]:
    """
    立即执行一次任务 - 用于测试

    Args:
        db_manager: 数据库管理器, 如果为None则创建默认的

    Returns:
        执行结果
    """
    if db_manager is None:
        db_manager = get_database_manager(get_default_database_config())

    logger.info("立即执行一次整点任务测试")
    result = await execute_minute_task(db_manager)
    return result


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help", "help"]:
            logger.info(__doc__)
            sys.exit(0)
        elif sys.argv[1] == "test":
            # 测试模式 - 立即执行一次
            _ = asyncio.run(run_once_now())
            sys.exit(0)

    # 正常启动调度器
    asyncio.run(start_scheduler())
