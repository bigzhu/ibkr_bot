"""
订单同步功能 - 纯函数实现

从Binance API同步订单数据到本地数据库,使用纯函数架构.
遵循CLAUDE.md规范: 函数优先,避免不必要的类封装.
"""

from datetime import datetime
from decimal import Decimal
from time import monotonic
from typing import Any
from zoneinfo import ZoneInfo

from loguru import logger

if __name__ == "__main__":
    try:
        from shared.path_utils import ensure_project_root_for_script
    except ImportError:
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from shared.path_utils import ensure_project_root_for_script

    ensure_project_root_for_script(__file__)

from database.models import BinanceFilledOrder
from ibkr_api.get_all_orders import get_all_orders
from order_filler.data_access import get_latest_order_id, insert_orders
from shared.constants import BUY, SELL

# 时区设置
UTC = ZoneInfo("UTC")


def _sync_all_batches(pair: str, limit: int, start_order_id: int | None) -> None:
    """执行分批同步"""
    current_order_id = start_order_id
    total_api_time = 0.0
    total_fetched = 0
    api_calls = 0

    while True:
        # 获取订单数据(计时)
        _t0 = monotonic()
        order_list = get_all_orders(pair, limit, current_order_id)
        _t1 = monotonic()
        api_calls += 1
        total_api_time += _t1 - _t0
        batch_size = len(order_list)
        # 过滤掉 CANCELED 状态的订单不计入统计
        total_fetched += sum(1 for o in order_list if o["status"] != "CANCELED")

        # 检查是否结束
        if not order_list:
            break

        # 处理当前批次
        (
            batch_newly_added,
            batch_duplicates,
            latest_order_id_in_batch,
        ) = _process_order_batch(order_list)

        # 检查结束条件
        if _should_stop_sync(batch_newly_added, batch_duplicates, batch_size, limit):
            break

        # 准备下次请求
        if latest_order_id_in_batch:
            current_order_id = latest_order_id_in_batch + 1

    # 汇总日志(信息级别)
    logger.info(
        f"⏱ get_all_orders 总耗时: {total_api_time:.3f}s, 调用次数: {api_calls}, 累计返回: {total_fetched}"
    )


def _process_order_batch(
    order_list: list[dict[str, Any]],
) -> tuple[int, int, int | None]:
    """处理单个批次的订单数据"""
    batch_newly_added = 0
    batch_duplicates = 0
    latest_order_id_in_batch = None
    filled_orders_to_insert: list[BinanceFilledOrder] = []

    for order_data in order_list:
        # 只处理已完成的订单 - order_filler表只存储FILLED状态订单
        if order_data["status"] != "FILLED":
            # 仍需记录订单ID以保持同步连续性
            order_id = int(order_data["orderId"])
            if not latest_order_id_in_batch or order_id > latest_order_id_in_batch:
                latest_order_id_in_batch = order_id
            continue

        # 转换为BinanceFilledOrder
        filled_order = _convert_order_to_filled_order(order_data)

        filled_orders_to_insert.append(filled_order)

        # 记录当前批次最大订单ID
        order_id = int(order_data["orderId"])
        if not latest_order_id_in_batch or order_id > latest_order_id_in_batch:
            latest_order_id_in_batch = order_id

    if filled_orders_to_insert:
        inserted = insert_orders(filled_orders_to_insert)
        batch_newly_added += inserted
        batch_duplicates += len(filled_orders_to_insert) - inserted

    return batch_newly_added, batch_duplicates, latest_order_id_in_batch


def _should_stop_sync(
    batch_newly_added: int, batch_duplicates: int, batch_size: int, limit: int
) -> bool:
    """判断是否应该停止同步"""
    # 如果获取的数量少于限制,说明已经获取完所有数据
    if batch_size < limit:
        return True

    # 如果整个批次都是重复的,可能后续也都是重复的,提前结束
    return batch_newly_added == 0 and batch_duplicates > 0


def _convert_order_to_filled_order(order_data: dict[str, Any]) -> BinanceFilledOrder:
    """
    将Binance API订单数据映射为BinanceFilledOrder对象, 并基于撮合结果计算平均成交价

    Args:
        order_data: Binance API返回的订单数据

    Returns:
        BinanceFilledOrder对象
    """
    # 转换时间戳为可读时间格式 (数据库需要)
    # API time -> date_utc (订单创建时间)
    order_time = datetime.fromtimestamp(order_data["time"] / 1000, UTC)
    date_utc = order_time.strftime("%Y-%m-%d %H:%M:%S")

    # API updateTime -> time (订单更新时间)
    update_time = datetime.fromtimestamp(order_data["updateTime"] / 1000, UTC)
    time_str = update_time.strftime("%Y-%m-%d %H:%M:%S")

    # 直接字段映射,不做任何计算或转换
    return BinanceFilledOrder(
        date_utc=date_utc,
        order_no=str(order_data["orderId"]),
        pair=order_data["symbol"],
        order_type=order_data["type"],
        side=BUY if order_data["side"] == "BUY" else SELL,
        order_price=order_data["price"],
        order_amount=order_data["origQty"],
        time=time_str,
        executed=order_data["executedQty"],
        average_price=_extract_average_price(order_data),
        trading_total=order_data["cummulativeQuoteQty"],
        status=order_data["status"],
        unmatched_qty=order_data["executedQty"],
        client_order_id=order_data.get("clientOrderId"),
    )


def _extract_average_price(order_data: dict[str, Any]) -> str:
    """根据成交金额和数量计算平均成交价"""
    cumulative_quote = Decimal(str(order_data["cummulativeQuoteQty"]))
    executed_qty = Decimal(str(order_data["executedQty"]))
    if executed_qty == 0:
        return "0"
    average = cumulative_quote / executed_qty
    return str(average.normalize())


def sync_orders_for_pair(pair: str, limit: int = 1000) -> None:
    """
    同步指定交易对的订单 - 主函数

    Args:
        pair: 交易对符号
        limit: 单次获取订单数量限制(最大1000)
    """
    # 获取同步起始点订单ID
    # 币安API的orderId参数是包含性的(>=), 不需要+1
    # 重复订单会被insert_order函数自动去重
    start_order_id = get_latest_order_id(pair)

    _sync_all_batches(pair, limit, start_order_id)
