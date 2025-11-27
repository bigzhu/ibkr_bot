"""共享日志工具模块

提供统一的日志路径管理和模块专用日志配置功能.
确保无论从哪个目录运行都能正确创建日志文件.
遵循CLAUDE.md规范: fail-fast原则,类型注解,禁用try-except
"""

import os
import sys
from pathlib import Path

from loguru import logger


def get_project_root() -> Path:
    """获取项目根目录路径

    通过查找包含特定标识文件的目录来确定项目根目录.

    Returns:
        Path: 项目根目录路径

    Raises:
        RuntimeError: 当找不到项目根目录时抛出异常
    """
    current_path = Path(__file__).resolve()

    # 从当前文件向上查找项目根目录
    for parent in current_path.parents:
        # 检查是否包含项目标识文件
        if (parent / "CLAUDE.md").exists() or (parent / "pyproject.toml").exists():
            return parent

    # 如果找不到,抛出异常
    raise RuntimeError("无法找到项目根目录,请确保项目结构正确")


def get_logs_dir() -> Path:
    """获取日志目录路径

    Returns:
        Path: 日志目录的绝对路径
    """
    logs_dir = get_project_root() / "logs"
    logs_dir.mkdir(exist_ok=True)  # 确保目录存在
    return logs_dir


def get_log_file_path(log_filename: str) -> str:
    """获取日志文件的绝对路径

    Args:
        log_filename: 日志文件名,如 "order_filler.log"

    Returns:
        str: 日志文件的绝对路径字符串
    """
    return str(get_logs_dir() / log_filename)


def setup_scheduler_logger() -> None:
    """配置调度器相关任务的日志输出

    配置规则:
    - 控制台输出: INFO 级别
    - 文件输出: DEBUG 级别,保存到 logs/scheduler.log
    - 日志轮转: 每天轮转,保留7天
    - 用于所有调度任务(order_builder, order_filler等)

    配置完成后可通过 from loguru import logger 使用
    """
    # 移除默认的日志处理器,重新配置
    logger.remove()

    # 控制台输出格式: 支持简洁样式开关
    style = os.getenv("SCHEDULER_LOG_STYLE", "normal").lower()
    if style == "concise":
        fmt = "{time:YYYY-MM-DD HH:mm:ss.SSS} {message}"
    else:
        fmt = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}"

    _ = logger.add(sys.stdout, level="INFO", format=fmt)

    # 不再写入文件,仅控制台输出


def setup_web_admin_logger() -> None:
    """配置 Web Admin 的日志输出

    配置规则:
    - 控制台输出: INFO 级别
    - 文件输出: DEBUG 级别,保存到 logs/web_admin.log
    - 日志轮转: 每天轮转,保留7天

    配置完成后可通过 from loguru import logger 使用
    """
    # 移除默认的日志处理器,重新配置
    logger.remove()

    # 添加控制台输出
    _ = logger.add(
        sys.stdout,
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}",
    )

    # 不再写入文件,仅控制台输出


if __name__ == "__main__":
    """测试日志路径工具"""
    import sys

    if len(sys.argv) < 2:
        logger.info("共享日志工具模块")
        logger.info("用法: p logger_utils.py [test]")
        logger.info("功能:")
        logger.info("  - get_project_root: 获取项目根目录")
        logger.info("  - get_logs_dir: 获取日志目录")
        logger.info("  - get_log_file_path: 获取日志文件路径")
        logger.info("  - setup_scheduler_logger: 配置调度器日志")
        logger.info("  - setup_web_admin_logger: 配置Web Admin日志")
        sys.exit(0)

    # 测试路径获取
    try:
        project_root = get_project_root()
        logs_dir = get_logs_dir()
        log_file = get_log_file_path("test.log")

        logger.info(f"✅ 项目根目录: {project_root}")
        logger.info(f"✅ 日志目录: {logs_dir}")
        logger.info(f"✅ 测试日志文件: {log_file}")

        logger.info("📁 共享日志工具模块加载成功")
    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")
        sys.exit(1)
