"""
币安成交订单管理API接口
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import requests
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from shared.timeframe_utils import timeframe_candidates
from web_admin.api.utils.database_helpers import (
    compute_pagination,
    query_all_dict,
    query_one_dict,
)

from ..utils.binance_filled_orders_helpers import (
    build_where_clause_and_params,
    convert_row_to_response,
    get_base_query,
    validate_order_params,
)
from .auth import get_current_user

router = APIRouter()


@router.get("/binance-filled-orders/", dependencies=[Depends(get_current_user)])
async def get_binance_order_filler(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    pair: str | None = Query(None, description="交易对过滤"),
    status: str | None = Query(None, description="状态过滤"),
    side: str | None = Query(None, description="买卖方向过滤"),
    order_by: str = Query("time", description="排序字段"),
    order_direction: str = Query("DESC", description="排序方向"),
) -> dict[str, Any]:
    """
    获取币安成交订单列表

    支持分页,筛选和排序功能
    """
    # 使用辅助函数构建查询条件
    base_query = get_base_query()
    where_clause, params = build_where_clause_and_params(pair, status, side)
    order_by, order_direction = validate_order_params(order_by, order_direction)

    # 获取总记录数
    count_query = f"SELECT COUNT(*) FROM filled_orders{where_clause}"
    count_result = query_one_dict(count_query, tuple(params))
    total = int(count_result["COUNT(*)"]) if count_result else 0

    # 计算分页参数
    total_pages, offset = compute_pagination(total, page, page_size)

    # 构建分页查询
    data_query = f"{base_query}{where_clause} ORDER BY {order_by} {order_direction} LIMIT ? OFFSET ?"
    params.extend([str(page_size), str(offset)])

    # 执行查询并转换数据
    rows = query_all_dict(data_query, tuple(params))

    # 转换数据为响应模型 - rows已经是字典格式
    orders = [convert_row_to_response(row) for row in rows]

    return {
        "success": True,
        "message": f"获取到 {len(orders)} 个币安成交订单",
        "data": orders,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/binance-filled-orders/stats", dependencies=[Depends(get_current_user)])
async def get_binance_order_filler_stats() -> dict[str, Any]:
    """
    获取币安成交订单统计信息
    """
    # 异常向上传播(fail-fast原则)
    result = query_one_dict("SELECT COUNT(*) as total_count FROM filled_orders")
    total_count = int(result["total_count"]) if result else 0
    stats = {"total_orders": total_count}

    return {"success": True, "message": "获取币安订单统计信息成功", "data": stats}


@router.get("/binance-filled-orders/pairs", dependencies=[Depends(get_current_user)])
async def get_binance_filled_order_pairs() -> dict[str, Any]:
    """
    获取币安成交订单中的所有交易对列表
    """
    # 异常向上传播(fail-fast原则)
    query = """
    SELECT DISTINCT pair
    FROM filled_orders
    WHERE pair IS NOT NULL
    ORDER BY pair
    """

    rows = query_all_dict(query)

    # 访问字典中的pair字段
    pairs = [row["pair"] for row in rows]

    return {
        "success": True,
        "message": f"获取到 {len(pairs)} 个交易对",
        "data": pairs,
    }


def _build_min_sell_conditions_query(timeframe: str = "1m") -> str:
    """构建最低SELL条件查询SQL - 移除售价计算,在Python中处理

    使用共享工具生成 timeframe 候选,避免硬编码 'tf' 与 'tf_1'.
    """
    tf_candidates = timeframe_candidates(timeframe)
    in_clause = ", ".join([f"'{tf}'" for tf in tf_candidates])
    return f"""
    WITH buy_orders AS (
        SELECT
            pair,
            CAST(unmatched_qty AS REAL) AS unmatched_qty,
            CAST(average_price AS REAL) AS average_price,
            CAST(average_price AS REAL) * CAST(unmatched_qty AS REAL) AS position_cost
        FROM filled_orders
        WHERE side = 'BUY'
          AND unmatched_qty > 0
          AND client_order_id IN ({in_clause})
    ), aggregated AS (
        SELECT
            pair,
            SUM(unmatched_qty) AS total_unmatched_qty,
            SUM(position_cost) AS total_cost,
            MIN(average_price) AS min_buy_price
        FROM buy_orders
        GROUP BY pair
    )
    SELECT
        a.pair,
        '{timeframe}' AS timeframe,
        COALESCE(a.total_unmatched_qty, 0) AS quantity,
        CASE
            WHEN a.total_unmatched_qty > 0 THEN a.total_cost / a.total_unmatched_qty
            ELSE 0
        END AS average_price,
        COALESCE(a.min_buy_price, 0) AS min_buy_price,
        COALESCE(s.minimum_profit_percentage, 5.0) AS minimum_profit_percentage,
        ts.base_asset,
        COALESCE(a.total_unmatched_qty, 0.0) AS balance,
        ts.quote_asset,
        COALESCE(ts.quote_asset_balance, 0.0) AS quote_balance,
        COALESCE(a.total_cost, 0) AS cost,
        ts.current_price AS current_price
    FROM aggregated a
    LEFT JOIN symbol_timeframe_configs s ON a.pair = s.trading_symbol AND s.kline_timeframe = '{timeframe}'
    INNER JOIN trading_symbols ts ON a.pair = ts.symbol
    ORDER BY a.pair
    """


def _execute_min_sell_conditions_query(query: str) -> list[dict[str, Any]]:
    """执行最低SELL条件查询"""
    return query_all_dict(query)


def _fetch_market_prices(symbols: set[str]) -> dict[str, Decimal | None]:
    prices: dict[str, Decimal | None] = {}
    for symbol in symbols:
        try:
            response = requests.get(
                "https://api.binance.com/api/v3/ticker/price",
                params={"symbol": symbol.upper()},
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()
            price_value = data.get("price")
            if price_value is None:
                prices[symbol] = None
                continue
            prices[symbol] = Decimal(str(price_value))
        except Exception as exc:  # pragma: no cover - 网络异常容错
            logger.debug("获取市价失败: %s %s", symbol, exc)
            prices[symbol] = None
    return prices


def _format_min_sell_conditions(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """格式化最低SELL条件数据 - 使用Decimal进行精确计算"""
    min_sell_conditions: list[dict[str, Any]] = []
    for row in rows:
        # 使用Decimal进行精确的售价计算
        average_price = Decimal(str(row["average_price"]))
        minimum_profit_percentage = Decimal(str(row["minimum_profit_percentage"]))
        total_cost = Decimal(str(row.get("cost", "0")))

        market_price_raw = row.get("current_price")
        if market_price_raw is not None:
            try:
                market_price = Decimal(str(market_price_raw))
                market_price_quantized = market_price.quantize(
                    Decimal("0.00000001"), rounding=ROUND_HALF_UP
                )
                market_price_str = str(market_price_quantized).rstrip("0").rstrip(".")
            except Exception:  # pragma: no cover - 容错外部数据
                market_price_str = "-"
        else:
            market_price_str = "-"

        # 计算售价: average_price * (1 + minimum_profit_percentage/100)
        profit_multiplier = (minimum_profit_percentage / Decimal("100")) + Decimal("1")
        sell_price = average_price * profit_multiplier

        # 格式化为字符串,保持精度但去除末尾的0
        sell_price_str = str(
            sell_price.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
        )
        if "." in sell_price_str:
            sell_price_str = sell_price_str.rstrip("0").rstrip(".")

        cost_str = str(
            total_cost.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
        )
        if "." in cost_str:
            cost_str = cost_str.rstrip("0").rstrip(".")

        # 格式化最低买价
        min_buy_price = Decimal(str(row.get("min_buy_price", "0")))
        min_buy_price_str = str(
            min_buy_price.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
        )
        if "." in min_buy_price_str:
            min_buy_price_str = min_buy_price_str.rstrip("0").rstrip(".")

        min_sell_conditions.append(
            {
                "pair": row["pair"],
                "timeframe": row.get("timeframe", ""),
                "quantity": row["quantity"],
                "average_price": row["average_price"],
                "min_buy_price": min_buy_price_str,
                "minimum_profit_percentage": row["minimum_profit_percentage"],
                "holding_qty": row["quantity"],
                "quote_balance": row["quote_balance"],
                "cost": cost_str,
                "market_price": market_price_str,
            }
        )
    return min_sell_conditions


def _get_active_timeframes() -> list[str]:
    sql = """
        SELECT DISTINCT kline_timeframe
        FROM symbol_timeframe_configs
        WHERE is_active = 1
        ORDER BY kline_timeframe
    """
    rows = query_all_dict(sql)
    return [str(row["kline_timeframe"]) for row in rows if row.get("kline_timeframe")]


@router.get(
    "/binance-filled-orders/min-sell-conditions",
    dependencies=[Depends(get_current_user)],
)
async def get_min_sell_conditions(
    timeframe: str | None = Query(
        None, description="最小SELL条件对应的时间周期, 不传则返回所有激活周期"
    ),
) -> dict[str, Any]:
    """
    获取最低SELL条件数据

    显示条件:
    - order_filler.unmatched_qty 不为 0 且是 BUY 单
    - 只显示目前参与整点运行的交易对 (symbol_timeframe_configs.is_active = 1 AND trading_symbols.is_active = 1)
    - 只查询 client_order_id 为 '1m' 或 '1m_1' 的订单
    - 查出 average_price 最低的那条记录
    - 计算售价:average_price * (1 + minimum_profit_percentage/100)
    - minimum_profit_percentage 取 1m 时间周期的配置,如无配置则默认 5.0%
    - 添加对应币种的当前余额信息
    """
    timeframes = [timeframe] if timeframe else _get_active_timeframes()
    if not timeframes:
        timeframes = ["1m"]

    min_sell_conditions: list[dict[str, Any]] = []
    for tf in timeframes:
        query = _build_min_sell_conditions_query(tf)
        rows = _execute_min_sell_conditions_query(query)
        if not rows:
            continue
        min_sell_conditions.extend(_format_min_sell_conditions(rows))

    return {
        "success": True,
        "message": f"获取到 {len(min_sell_conditions)} 个最低SELL条件",
        "data": min_sell_conditions,
    }


@router.get(
    "/binance-filled-orders/market-price",
    dependencies=[Depends(get_current_user)],
)
async def get_market_price(
    symbol: str = Query(..., description="交易对, 例如 ADAUSDC"),
) -> dict[str, Any]:
    """
    获取单个交易对的最新市价
    """
    symbol_clean = symbol.strip().upper()
    if not symbol_clean:
        raise HTTPException(status_code=400, detail="symbol 参数不能为空")

    prices = _fetch_market_prices({symbol_clean})
    price_value = prices.get(symbol_clean)
    if price_value is None:
        return {
            "success": False,
            "symbol": symbol_clean,
            "market_price": None,
            "message": "获取市价失败",
        }

    market_price_str = (
        str(price_value.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP))
        .rstrip("0")
        .rstrip(".")
    )

    return {
        "success": True,
        "symbol": symbol_clean,
        "market_price": market_price_str or "0",
    }


@router.post("/binance-filled-orders/sync", dependencies=[Depends(get_current_user)])
async def sync_binance_order_filler() -> dict[str, Any]:
    """
    手动触发同步币安成交订单

    自动识别同步模式:
    - 如果数据库中该交易对有历史订单,自动执行增量同步
    - 如果数据库中该交易对无历史订单,自动执行全量同步
    """
    # 简化同步实现 - 返回模拟结果
    result = {
        "success": True,
        "total_pairs": 0,
        "processed_pairs": 0,
        "new_orders": 0,
        "summary": "币安订单同步功能暂未实现",
    }

    if result["success"]:
        # 处理同步结果
        summary = result.get(
            "summary",
            f"同步完成: 处理了 {result.get('processed_pairs', 0)} 个交易对",
        )

        return {
            "success": True,
            "message": summary,
            "data": {
                "total_pairs": result.get("total_pairs", 0),
                "processed_pairs": result.get("processed_pairs", 0),
                "incremental_pairs": result.get("incremental_pairs", 0),
                "full_sync_pairs": result.get("full_sync_pairs", 0),
                "total_orders": result.get("total_orders", 0),
                "new_orders": result.get("new_orders", 0),
                "updated_orders": result.get("updated_orders", 0),
                "skipped_orders": result.get("skipped_orders", 0),
                "errors": result.get("errors", []),
            },
        }
    else:
        return {
            "success": False,
            "message": f"币安订单同步失败: {result.get('error', '未知错误')}",
            "data": result,
        }


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    logger.info("💰 币安成交订单路由模块")
    logger.info("提供币安成交订单相关的 API 端点")
    logger.info("- GET /api/v1/binance-filled-orders/ - 获取币安成交订单列表")
    logger.info("- GET /api/v1/binance-filled-orders/stats - 获取币安成交订单统计")
    logger.info("- GET /api/v1/binance-filled-orders/pairs - 获取交易对列表")
    logger.info(
        "- GET /api/v1/binance-filled-orders/min-sell-conditions - 获取最低SELL条件"
    )
    logger.info("- POST /api/v1/binance-filled-orders/sync - 同步币安成交订单")
