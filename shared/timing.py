"""统一计时辅助工具

提供轻量的计时上下文管理器, 用于统一输出耗时日志.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from time import monotonic

from loguru import logger


@contextmanager
def time_block(label: str) -> Iterator[None]:
    """计时一个逻辑块并在完成后输出耗时日志.

    Args:
        label: 显示在日志中的逻辑块名称
    """
    start = monotonic()
    try:
        yield
    finally:
        elapsed = monotonic() - start
        logger.info(f"⏱ {label}耗时: {elapsed:.3f}s")
