"""
事件总线系统 - 真正的事件驱动架构

专注功能: WebSocket 实时推送的事件发布订阅系统
当数据库发生变化时,立即通知所有订阅者
"""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, ClassVar

from loguru import logger


class TradingLogEventBus:
    """交易日志事件总线 - 单例模式"""

    _instance: ClassVar[Any] = None
    _subscribers: ClassVar[list[Callable[[dict[str, Any]], Any]]] = []

    def __new__(cls) -> "TradingLogEventBus":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "_initialized"):
            self.__class__._subscribers = []
            self._initialized = True
            logger.info("🔄 交易日志事件总线已初始化")

    def subscribe(self, callback: Callable[[dict[str, Any]], Any]) -> None:
        """订阅事件

        Args:
            callback: 事件回调函数,接收事件数据字典
        """
        self._subscribers.append(callback)
        logger.debug(f"+ 新增事件订阅者,当前订阅数: {len(self._subscribers)}")

    def unsubscribe(self, callback: Callable[[dict[str, Any]], Any]) -> None:
        """取消订阅事件

        Args:
            callback: 要取消的回调函数
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            logger.debug(f"- 移除事件订阅者,当前订阅数: {len(self._subscribers)}")

    async def publish_async(self, event_type: str, data: dict[str, Any]) -> None:
        """异步发布事件 - 用于 WebSocket 推送

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        if not self._subscribers:
            logger.debug(f"📢 发布事件 {event_type},但没有订阅者")
            return

        event_data = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        logger.debug(f"📢 发布事件: {event_type},订阅者数量: {len(self._subscribers)}")

        # 并发调用所有订阅者
        tasks: list[Awaitable[Any]] = []
        for subscriber in self._subscribers:
            if asyncio.iscoroutinefunction(subscriber):
                tasks.append(subscriber(event_data))
            else:
                # 同步函数包装为异步
                async def wrapper(
                    sync_subscriber: Callable[[dict[str, Any]], Any] = subscriber,
                ) -> Any:
                    return sync_subscriber(event_data)

                tasks.append(wrapper())

        if tasks:
            _ = await asyncio.gather(*tasks, return_exceptions=True)

    def publish_sync(self, event_type: str, data: dict[str, Any]) -> None:
        """同步发布事件 - 用于数据库操作触发

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        if not self._subscribers:
            logger.debug(f"📢 同步发布事件 {event_type},但没有订阅者")
            return

        event_data = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        logger.debug(
            f"📢 同步发布事件: {event_type},订阅者数量: {len(self._subscribers)}"
        )

        # 创建异步任务在后台执行
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行,创建任务
                task = asyncio.create_task(self.publish_async(event_type, data))
                # 任务引用存储以避免垃圾回收
                task.add_done_callback(lambda _: None)
            else:
                # 如果没有运行的事件循环,同步执行
                for subscriber in self._subscribers:
                    if not asyncio.iscoroutinefunction(subscriber):
                        subscriber(event_data)
        except RuntimeError:
            # 没有事件循环,只执行同步订阅者
            for subscriber in self._subscribers:
                if not asyncio.iscoroutinefunction(subscriber):
                    subscriber(event_data)


# 全局事件总线实例
trading_log_event_bus = TradingLogEventBus()


def publish_trading_log_created(log_id: int, log_data: dict[str, Any]) -> None:
    """发布交易日志创建事件 - 便捷函数

    Args:
        log_id: 日志ID
        log_data: 日志数据
    """
    trading_log_event_bus.publish_sync(
        "trading_log_created", {"id": log_id, "log": log_data}
    )


def publish_trading_log_updated(log_id: int, updated_fields: dict[str, Any]) -> None:
    """发布交易日志更新事件 - 便捷函数

    Args:
        log_id: 日志ID
        updated_fields: 更新的字段
    """
    logger.debug(
        f"📡 发布交易日志更新事件: log_id={log_id}, 更新字段={list(updated_fields.keys())}"
    )
    trading_log_event_bus.publish_sync(
        "trading_log_updated", {"id": log_id, "updated_fields": updated_fields}
    )


if __name__ == "__main__":
    """测试事件总线"""

    def test_subscriber(event_data: dict[str, Any]) -> None:
        logger.info(f"收到事件: {event_data}")

    # 订阅测试
    bus = TradingLogEventBus()
    bus.subscribe(test_subscriber)

    # 发布测试
    bus.publish_sync("test_event", {"message": "Hello World"})

    logger.info("事件总线测试完成")
