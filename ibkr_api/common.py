"""
IBKR API 公共函数

提供可复用的 API 配置与客户端创建, 遵循 fail-fast 原则.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m ibkr_api.common` 运行该模块, 无需手动修改 sys.path"
    )

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper
from loguru import logger

# 简单的配置缓存, 避免重复读取
_config_cache: dict[str, Any] | None = None
# 简单的客户端缓存, 避免重复创建与握手
_client_cache: IBKRClient | None = None


@dataclass(slots=True)
class IBKRConfig:
    host: str
    port: int
    client_id: int
    account: str | None
    base_currency: str
    paper: bool


class IBKRClient(EWrapper, EClient):
    """最小化 IBKR 客户端封装, 提供同步 account_summary."""

    def __init__(self, config: IBKRConfig):
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self.config = config
        self._connected_event = threading.Event()
        self._summary_event = threading.Event()
        self._summary_lock = threading.Lock()
        self._summary: dict[str, Any] = {}
        self._next_req_id = 1
        self._order_id_lock = threading.Lock()
        self._next_order_id: int | None = None

    # ===== EWrapper 回调 =====
    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str) -> None:
        with self._summary_lock:
            self._summary[tag] = value
            self._summary.setdefault("account", account)
            self._summary.setdefault("currency", currency)

    def nextValidId(self, orderId: int) -> None:  # - IBKR 回调命名
        self._connected_event.set()
        with self._order_id_lock:
            self._next_order_id = orderId

    def accountSummaryEnd(self, reqId: int) -> None:  # - IBKR 回调命名
        self._summary_event.set()

    # ===== 业务方法 =====
    def connect_and_start(self, timeout: float = 5.0) -> None:
        """连接 IB Gateway/TWS 并启动读写线程."""
        self.connect(self.config.host, self.config.port, self.config.client_id)
        thread = threading.Thread(target=self.run, name="ibkr-client-thread", daemon=True)
        thread.start()

        start = time.time()
        while not self.isConnected():
            if time.time() - start > timeout:
                raise TimeoutError("IBKR 连接超时, 请确认 Gateway/TWS 已启动并允许 API")
            time.sleep(0.1)

        if not self._connected_event.wait(timeout=timeout):
            raise TimeoutError("IBKR 连接未完成握手(nextValidId) , 请检查 Gateway/TWS 状态")

        with self._order_id_lock:
            if self._next_order_id is None:
                raise TimeoutError("未获得有效的下单起始ID(nextValidId)")

    def account_summary(self, timeout: float = 5.0) -> dict[str, Any]:
        """同步获取账户概要信息."""
        if not self.isConnected():
            self.connect_and_start()

        with self._summary_lock:
            self._summary.clear()
        self._summary_event.clear()

        req_id = self._next_req_id
        self._next_req_id += 1

        tags = "NetLiquidation,AvailableFunds,BuyingPower,TotalCashValue,EquityWithLoanValue"
        self.reqAccountSummary(req_id, "All", tags)

        if not self._summary_event.wait(timeout=timeout):
            self.cancelAccountSummary(req_id)
            raise TimeoutError("获取 IBKR 账户概要超时")

        self.cancelAccountSummary(req_id)

        with self._summary_lock:
            if not self._summary:
                raise ValueError("未能获取 IBKR 账户概要")
            return dict(self._summary)

    def next_order_id(self) -> int:
        """获取下一个可用的订单ID."""
        with self._order_id_lock:
            if self._next_order_id is None:
                raise TimeoutError("尚未从 IBKR 获取有效的订单ID")
            order_id = self._next_order_id
            self._next_order_id += 1
            return order_id

    def get_current_price(self, contract: Contract) -> Decimal:
        """占位: 获取当前价格, 需要补充行情订阅实现."""
        raise NotImplementedError("行情获取需另行实现")


def get_api_config() -> IBKRConfig:
    """从环境变量获取 IBKR 配置, 缓存并返回."""
    global _config_cache

    if _config_cache is not None:
        return IBKRConfig(**_config_cache)

    host = os.getenv("IBKR_HOST", "127.0.0.1")
    port = int(os.getenv("IBKR_PORT", "4001"))
    client_id = int(os.getenv("IBKR_CLIENT_ID", "1"))
    account = os.getenv("IBKR_ACCOUNT")
    base_currency = os.getenv("BASE_CURRENCY", "USD")
    paper_raw = os.getenv("IBKR_PAPER", "true").lower()
    paper = paper_raw == "true"

    config_dict = {
        "host": host,
        "port": port,
        "client_id": client_id,
        "account": account,
        "base_currency": base_currency,
        "paper": paper,
    }
    _config_cache = config_dict
    return IBKRConfig(**config_dict)


def get_configured_client() -> IBKRClient:
    """获取已配置的 IBKR 客户端."""
    global _client_cache

    if _client_cache is not None:
        return _client_cache

    config = get_api_config()
    client = IBKRClient(config)
    client.connect_and_start()
    _client_cache = client
    return client


def get_configured_client_with_config() -> tuple[IBKRClient, IBKRConfig]:
    """获取客户端与配置."""
    client = get_configured_client()
    config = get_api_config()
    return client, config


def reset_client_cache() -> None:
    """重置客户端与配置缓存."""
    global _client_cache, _config_cache
    if _client_cache is not None and _client_cache.isConnected():
        _client_cache.disconnect()
    _client_cache = None
    _config_cache = None


def print_api_setup_help() -> None:
    """打印 API 设置帮助信息."""
    logger.error("❌ IBKR API 未配置, 请检查 IBKR_HOST/IBKR_PORT/IBKR_CLIENT_ID 等环境变量")


if __name__ == "__main__":
    logger.info("🔧 IBKR API 公共函数测试")
    client, config = get_configured_client_with_config()
    logger.info(f"   ✅ 客户端已连接, host={config.host}, port={config.port}, client_id={config.client_id}")
    summary = client.account_summary()
    logger.info(f"   ✅ 账户概要: {summary}")
