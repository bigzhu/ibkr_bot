"""
异步通知器: 通过 HTTP 回调与主流程解耦, 后台线程异步发送.

特性:
- fire-and-forget: 投递到队列立即返回,不阻塞主线程/事务
- 容错: 发送异常仅记录日志, 不影响主流程
- HTTP-only: 仅通过 HTTP 通知 API 服务, 再由 API 通过 WebSocket 推送到浏览器
"""

from __future__ import annotations

import atexit
import queue
import threading
import time
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

try:
    # requests 仅在HTTP回退时使用
    import requests
except Exception:  # pragma: no cover - 运行环境无 requests 时静默
    requests = None

from loguru import logger

from shared.config import Config

_event_queue: queue.Queue[_NotifyTask] = queue.Queue(maxsize=1000)
_worker_thread: threading.Thread | None = None
_init_lock = threading.Lock()
_shutdown_lock = threading.Lock()


@dataclass
class _NotifyTask:
    kind: str  # "trading_log_created" | "trading_log_updated"
    payload: dict[str, Any]


def _ensure_worker_started() -> None:
    """Start the background worker thread lazily when the first event arrives."""
    global _worker_thread
    if _worker_thread and _worker_thread.is_alive():
        return
    with _init_lock:
        if _worker_thread and _worker_thread.is_alive():
            return
        _start_worker_thread()


def _start_worker_thread() -> None:
    """Create and register the daemon thread responsible for consuming events."""
    global _worker_thread
    _worker_thread = threading.Thread(
        target=_worker_loop, name="async-notifier", daemon=True
    )
    _worker_thread.start()
    logger.debug("✅ 异步通知器后台线程已启动")
    with suppress(Exception):
        _ = atexit.register(_flush_queue_on_exit)


def _worker_loop() -> None:
    """后台线程: 从队列拉取任务并调用对应处理函数."""
    while True:
        try:
            task = _event_queue.get()
        except Exception:
            continue
        _process_task(task)
        with suppress(Exception):
            _event_queue.task_done()


def _http_created(log_id: int, log_data: dict[str, Any]) -> None:
    """Perform HTTP callback for newly created trading log events."""
    if not requests:
        return
    url = Config.get_internal_events_url("trading-log-created")
    payload = {"log_id": log_id, "log_data": log_data}
    _post_with_retries(url, payload)


def _dispatch_trading_log_created(payload: dict[str, Any]) -> None:
    """Validate payload and fire HTTP notification for created events."""
    raw = payload.get("log_id")
    if isinstance(raw, int):
        log_id = raw
    elif isinstance(raw, str) and raw.isdigit():
        log_id = int(raw)
    else:
        logger.debug("缺少有效的 log_id, 跳过 created 通知")
        return
    log_data = dict(payload.get("log_data") or {})
    # HTTP-only
    _http_created(log_id, log_data)


def _http_updated(log_id: int, updated_fields: dict[str, Any]) -> None:
    """Perform HTTP callback for trading log updates."""
    if not requests:
        return
    url = Config.get_internal_events_url("trading-log-updated")
    payload = {"log_id": log_id, "updated_fields": updated_fields}
    _post_with_retries(url, payload)


def _dispatch_trading_log_updated(payload: dict[str, Any]) -> None:
    """Validate payload and fire HTTP notification for updated events."""
    raw = payload.get("log_id")
    if isinstance(raw, int):
        log_id = raw
    elif isinstance(raw, str) and raw.isdigit():
        log_id = int(raw)
    else:
        logger.debug("缺少有效的 log_id, 跳过 updated 通知")
        return
    updated_fields = dict(payload.get("updated_fields") or {})
    _http_updated(log_id, updated_fields)


def _post_with_retries(url: str, payload: dict[str, Any], retries: int = 3) -> None:
    """Best-effort POST with exponential backoff to absorb transient failures."""
    if not requests:
        logger.warning("requests not available; drop async notify")
        return
    backoff = 0.5
    for _ in range(retries):
        try:
            resp = requests.post(url, json=payload, timeout=2)
            if getattr(resp, "status_code", 0) == 200:
                return
            logger.warning(
                f"HTTP notify failed: {url} status={getattr(resp, 'status_code', '?')}"
            )
        except Exception as e:
            logger.warning(f"HTTP notify exception: {e}")
        time.sleep(backoff)
        backoff *= 2


def enqueue_trading_log_created(log_id: int, log_data: dict[str, Any]) -> None:
    """Queue a trading-log-created event for asynchronous dispatch."""
    _ensure_worker_started()
    task = _NotifyTask("trading_log_created", {"log_id": log_id, "log_data": log_data})
    try:
        _event_queue.put_nowait(task)
    except queue.Full:
        logger.debug("异步通知队列已满, 丢弃 created 事件")


def enqueue_trading_log_updated(log_id: int, updated_fields: dict[str, Any]) -> None:
    """Queue a trading-log-updated event for asynchronous dispatch."""
    _ensure_worker_started()
    task = _NotifyTask(
        "trading_log_updated", {"log_id": log_id, "updated_fields": updated_fields}
    )
    try:
        _event_queue.put_nowait(task)
    except queue.Full:
        logger.debug("异步通知队列已满, 丢弃 updated 事件")


def _flush_queue_on_exit() -> None:
    """Drain remaining tasks on interpreter exit to reduce event loss."""
    with _shutdown_lock:
        drained = 0
        while True:
            try:
                task = _event_queue.get_nowait()
            except queue.Empty:
                break

            try:
                _process_task(task)
            except Exception as exc:
                logger.warning(f"flush notify error: {exc}")
            with suppress(Exception):
                _event_queue.task_done()
            drained += 1

        if drained:
            logger.debug(f"async notifier flushed {drained} pending events on exit")


def _process_task(task: _NotifyTask) -> None:
    """根据任务类型分发异步通知."""
    try:
        if task.kind == "trading_log_created":
            _dispatch_trading_log_created(task.payload)
        elif task.kind == "trading_log_updated":
            _dispatch_trading_log_updated(task.payload)
    except Exception as exc:
        logger.debug(f"Async notifier dispatch error: {exc}")
