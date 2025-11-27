"""
WebSocket 连接管理器 - 实时推送核心

专注功能: 管理 WebSocket 连接,处理实时数据推送
基于事件总线,实现真正的事件驱动推送
"""

import json
from datetime import UTC, datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from .events import trading_log_event_bus


class LogsWebSocketManager:
    """交易日志 WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.connection_filters: dict[WebSocket, dict[str, Any]] = {}
        self._setup_event_subscription()

    def _setup_event_subscription(self):
        """设置事件订阅"""
        trading_log_event_bus.subscribe(self._handle_event)
        logger.debug("WebSocket manager subscribed to trading log events")

    async def connect(self, websocket: WebSocket):
        """接受新的 WebSocket 连接

        Args:
            websocket: WebSocket 连接实例
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_filters[websocket] = {}  # 初始化筛选条件
        logger.debug(f"New WebSocket connection, total: {len(self.active_connections)}")

        # 发送连接成功消息
        await self._send_to_connection(
            websocket,
            {
                "type": "connection_established",
                "data": {
                    "message": "WebSocket 连接已建立",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            },
        )

    def disconnect(self, websocket: WebSocket):
        """断开 WebSocket 连接

        Args:
            websocket: 要断开的 WebSocket 连接
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_filters:
            del self.connection_filters[websocket]
        logger.debug(f"WebSocket disconnected, total: {len(self.active_connections)}")

    async def set_connection_filters(
        self, websocket: WebSocket, filters: dict[str, Any]
    ):
        """设置连接的筛选条件

        Args:
            websocket: WebSocket 连接
            filters: 筛选条件字典
        """
        self.connection_filters[websocket] = filters
        logger.debug(f"🔍 更新连接筛选条件: {filters}")

        # 确认筛选条件已设置
        await self._send_to_connection(
            websocket,
            {
                "type": "filters_updated",
                "data": {
                    "filters": filters,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            },
        )

    async def _handle_event(self, event_data: dict[str, Any]):
        """处理事件总线推送的事件

        Args:
            event_data: 事件数据
        """
        if not self.active_connections:
            logger.debug(f"📢 收到事件 {event_data['type']} 但没有活跃连接")
            return

        logger.debug(
            f"Handling event: {event_data['type']}, active: {len(self.active_connections)}"
        )

        # 向所有符合筛选条件的连接推送数据
        disconnected_connections: list[WebSocket] = []
        sent_count = 0

        for websocket in self.active_connections:
            try:
                # 检查筛选条件
                if self._should_send_to_connection(websocket, event_data):
                    await self._send_to_connection(websocket, event_data)
                    sent_count += 1
                else:
                    pass  # 连接被筛选条件过滤,跳过发送
            except (RuntimeError, WebSocketDisconnect) as e:
                logger.warning(f"⚠️ 向连接推送数据失败(连接关闭): {e}")
                disconnected_connections.append(websocket)
            except Exception as e:
                # 未知异常遵循 fail-fast 策略,向上抛出
                logger.error(f"❌ 未知推送异常: {e}")
                raise

        # 清理断开的连接
        for websocket in disconnected_connections:
            self.disconnect(websocket)

    def _should_send_to_connection(
        self, websocket: WebSocket, event_data: dict[str, Any]
    ) -> bool:
        """检查是否应该向指定连接发送事件

        Args:
            websocket: WebSocket 连接
            event_data: 事件数据

        Returns:
            bool: 是否应该发送
        """
        filters = self.connection_filters.get(websocket, {})

        # 如果没有筛选条件,发送所有事件
        if not filters:
            return True

        # 检查事件类型筛选
        if event_data.get("type") not in ["trading_log_created", "trading_log_updated"]:
            return True  # 非交易日志事件直接发送

        # 对于交易日志更新事件,更新数据通常不包含完整的日志字段(如 symbol/timeframe)
        # 为避免被筛选条件误过滤,统一放行更新事件
        if event_data.get("type") == "trading_log_updated":
            return True

        event_log_data = event_data.get("data", {}).get("log", {})

        # 检查交易对筛选 - 兼容新的symbols数组格式
        symbols = filters.get("symbols", [])
        if symbols and len(symbols) > 0 and event_log_data.get("symbol") not in symbols:
            return False

        # 检查时间周期筛选 - 兼容新的timeframes数组格式
        timeframes = filters.get("timeframes", [])
        if (
            timeframes
            and len(timeframes) > 0
            and event_log_data.get("kline_timeframe") not in timeframes
        ):
            return False

        # 检查执行状态筛选
        if filters.get("execution_status"):
            has_error = bool(event_log_data.get("error"))
            if filters["execution_status"] == "error" and not has_error:
                return False
            if filters["execution_status"] == "normal" and has_error:
                return False

        # 检查挂单方向筛选
        if (
            filters.get("order_side")
            and event_log_data.get("side") != filters["order_side"]
        ):
            return False

        # 检查order_id筛选 - 仅显示有order_id的记录
        return not (filters.get("hasOrderId") and not event_log_data.get("order_id"))

    async def _send_to_connection(self, websocket: WebSocket, data: dict[str, Any]):
        """向指定连接发送数据

        Args:
            websocket: WebSocket 连接
            data: 要发送的数据
        """
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            await websocket.send_text(json_data)
        except Exception as e:
            logger.error(f"❌ 发送数据失败: {e}")
            raise

    async def broadcast_to_all(self, data: dict[str, Any]):
        """向所有连接广播数据

        Args:
            data: 要广播的数据
        """
        if not self.active_connections:
            logger.debug("📢 尝试广播但没有活跃连接")
            return

        logger.debug(f"Broadcasting to {len(self.active_connections)} connections")

        disconnected_connections: list[WebSocket] = []

        for websocket in self.active_connections:
            try:
                await self._send_to_connection(websocket, data)
            except (RuntimeError, WebSocketDisconnect) as e:
                logger.warning(f"⚠️ 广播到连接失败(连接关闭): {e}")
                disconnected_connections.append(websocket)
            except Exception as e:
                logger.error(f"❌ 未知广播异常: {e}")
                raise

        # 清理断开的连接
        for websocket in disconnected_connections:
            self.disconnect(websocket)

    async def handle_client_message(self, websocket: WebSocket, message: str):
        """处理客户端发送的消息

        Args:
            websocket: WebSocket 连接
            message: 客户端消息
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "set_filters":
                # 设置筛选条件
                filters = data.get("filters", {})
                await self.set_connection_filters(websocket, filters)

            elif message_type == "ping":
                # 心跳检测
                await self._send_to_connection(
                    websocket,
                    {"type": "pong", "data": {"timestamp": datetime.now().isoformat()}},
                )

            else:
                logger.warning(f"⚠️ 未知消息类型: {message_type}")

        except json.JSONDecodeError as e:
            logger.error(f"❌ 解析客户端消息失败: {e}")
            await self._send_to_connection(
                websocket, {"type": "error", "data": {"message": "消息格式错误"}}
            )
        except Exception as e:
            logger.error(f"❌ 处理客户端消息失败: {e}")
            # 未知异常向上抛出,保持 fail-fast
            raise


# 全局 WebSocket 管理器实例
logs_websocket_manager = LogsWebSocketManager()


async def websocket_logs_endpoint(websocket: WebSocket):
    """WebSocket 端点处理函数

    Args:
        websocket: WebSocket 连接实例
    """
    await logs_websocket_manager.connect(websocket)

    try:
        while True:
            # 等待客户端消息
            message = await websocket.receive_text()
            await logs_websocket_manager.handle_client_message(websocket, message)

    except WebSocketDisconnect:
        logger.info("📱 客户端主动断开 WebSocket 连接")
    finally:
        logs_websocket_manager.disconnect(websocket)
